from fastapi import APIRouter, Depends, HTTPException, Request
import uuid
import secrets
import string
from datetime import datetime
from services.supabase import DBConnection
from utils.auth_utils import get_user_from_request, admin_required
from admin.check_ai_access import router as check_ai_access_router
from admin.activate_ai import router as activate_ai_router
from utils.logger import logger

router = APIRouter()

# Include the check-ai-access and activate-ai routers
router.include_router(check_ai_access_router)
router.include_router(activate_ai_router)
db = DBConnection()

@router.post("/admin/generate-code")
async def generate_activation_code(request: Request, admin_user=Depends(admin_required)):
    """
    Generate a new AI activation code.
    Only accessible by admin users.
    """
    try:
        # Generate a random code (16 characters)
        code_chars = string.ascii_uppercase + string.digits
        code_value = ''.join(secrets.choice(code_chars) for _ in range(16))
        code_id = str(uuid.uuid4())
        
        # Get Supabase client
        client = await db.client
        
        # Try to insert using execute_sql RPC for better reliability
        try:
            result = await client.rpc('execute_sql', {
                'query': """
                INSERT INTO ai_activation_codes 
                (id, code_value, is_active, created_at, generated_by_admin_id, is_claimed) 
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                'params': [
                    code_id,
                    code_value,
                    True,
                    datetime.now().isoformat(),
                    admin_user["id"],
                    False
                ]
            }).execute()
        except Exception as e:
            logger.error(f"Error inserting activation code with execute_sql: {e}")
            # Fallback to direct insert if execute_sql fails
            try:
                result = await client.from_("ai_activation_codes").insert({
                    "id": code_id,
                    "code_value": code_value,
                    "is_active": True,
                    "created_at": datetime.now().isoformat(),
                    "generated_by_admin_id": admin_user["id"],
                    "is_claimed": False
                }).execute()
                
                if hasattr(result, 'error') and result.error:
                    raise Exception(f"Supabase error: {result.error.message}")
            except Exception as inner_e:
                logger.error(f"Fallback insert failed: {inner_e}")
                raise Exception(f"Failed to generate activation code: {str(inner_e)}")
            
        return {"success": True, "code": code_value, "id": code_id}
    except Exception as e:
        logger.error(f"Failed to generate code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate activation code: {str(e)}")

@router.post("/activate-ai")
async def activate_ai(request: Request):
    """
    Activate AI access for a user using an activation code.
    """
    user = await get_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get the code from the request body
    data = await request.json()
    code = data.get("code")
    
    if not code:
        raise HTTPException(status_code=400, detail="Activation code is required")
    
    try:
        # Get Supabase client
        client = await db.client
        
        # Try to use the function we created
        try:
            result = await client.rpc('execute_sql', {
                'query': "SELECT activate_ai_access($1, $2) as success;",
                'params': [code, user["id"]]
            }).execute()
            
            if result.data and len(result.data) > 0 and result.data[0].get("success") == True:
                return {"success": True, "message": "AI access activated successfully"}
        except Exception as e:
            logger.error(f"Error activating AI access with function: {e}")
            # Continue with manual process if function fails
            pass
        
        # If the function call failed or returned false, check manually
        try:
            code_result = await client.rpc('execute_sql', {
                'query': "SELECT id FROM ai_activation_codes WHERE code_value = $1 AND is_active = true AND is_claimed = false",
                'params': [code]
            }).execute()
            
            code_record = code_result.data[0] if code_result.data and len(code_result.data) > 0 else None
        except Exception as e:
            logger.error(f"Error checking activation code: {e}")
            raise Exception(f"Failed to verify activation code: {str(e)}")
        
        if not code_record:
            return {"success": False, "message": "Invalid or already claimed code"}
        
        # Mark code as claimed
        try:
            await client.rpc('execute_sql', {
                'query': """
                UPDATE ai_activation_codes
                SET is_claimed = true, claimed_by_user_id = $1, claimed_at = $2
                WHERE id = $3
                """,
                'params': [user["id"], datetime.now().isoformat(), code_record["id"]]
            }).execute()
        except Exception as e:
            logger.error(f"Error marking code as claimed: {e}")
            raise Exception(f"Failed to mark activation code as claimed: {str(e)}")
        
        # Update user's AI access in raw_app_meta_data
        try:
            await client.rpc('execute_sql', {
                'query': """
                UPDATE auth.users
                SET raw_app_meta_data = raw_app_meta_data || '{"has_ai_access": true}'::jsonb
                WHERE id = $1
                """,
                'params': [user["id"]]
            }).execute()
        except Exception as e:
            logger.error(f"Error updating user's AI access: {e}")
            raise Exception(f"Failed to update user's AI access: {str(e)}")
        
        return {"success": True, "message": "AI access activated successfully"}
    except Exception as e:
        logger.error(f"Failed to activate AI access: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate AI access: {str(e)}")

@router.get("/admin/activation-codes")
async def list_activation_codes(request: Request, admin_user=Depends(admin_required)):
    """
    List all activation codes.
    Only accessible by admin users.
    """
    try:
        # Get Supabase client
        client = await db.client
        
        # Get activation codes
        try:
            result = await client.from_("ai_activation_codes").select("*").order("created_at", desc=True).execute()
            # Get user emails for the generated_by and claimed_by fields
            codes = result.data
        except Exception as e:
            logger.error(f"Failed to list codes: {e}")
            raise Exception(f"Failed to fetch activation codes: {str(e)}")
        
        # Enrich the data with user emails where possible
        for code in codes:
            if code.get("generated_by_admin_id"):
                try:
                    user_result = await client.rpc('execute_sql', {
                        'query': 'SELECT email FROM auth.users WHERE id = $1',
                        'params': [code["generated_by_admin_id"]]
                    }).execute()
                    if user_result.data and len(user_result.data) > 0:
                        code["generated_by"] = user_result.data[0]["email"]
                except Exception as e:
                    logger.error(f"Error getting user email: {e}")
                    pass
                    
            if code.get("claimed_by_user_id"):
                try:
                    user_result = await client.rpc('execute_sql', {
                        'query': 'SELECT email FROM auth.users WHERE id = $1',
                        'params': [code["claimed_by_user_id"]]
                    }).execute()
                    if user_result.data and len(user_result.data) > 0:
                        code["claimed_by"] = user_result.data[0]["email"]
                except Exception as e:
                    logger.error(f"Error getting user email: {e}")
                    pass
        
        return {"success": True, "codes": codes}
    except Exception as e:
        logger.error(f"Failed to list codes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list codes: {str(e)}")

@router.get("/admin/users")
async def list_users(request: Request, admin_user=Depends(admin_required)):
    """
    List all users with their AI access status.
    Only accessible by admin users.
    """
    try:
        # Get Supabase client
        client = await db.client
        
        # Get users from auth.users table
        # Since we can't directly query auth.users with the data API,
        # we'll use the admin API to get users
        try:
            users_response = await client.auth.admin.list_users()
            
            if hasattr(users_response, 'error') and users_response.error:
                raise Exception(f"Supabase error: {users_response.error.message}")
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            # Fallback to using execute_sql if admin API fails
            try:
                result = await client.rpc('execute_sql', {
                    'query': """
                    SELECT 
                        id, 
                        email, 
                        raw_app_meta_data->>'is_admin' as is_admin,
                        raw_app_meta_data->>'has_ai_access' as has_ai_access,
                        created_at,
                        last_sign_in_at
                    FROM auth.users
                    ORDER BY created_at DESC
                    """,
                    'params': []
                }).execute()
                
                # Create a mock users_response object with the data from execute_sql
                class MockUser:
                    def __init__(self, data):
                        self.id = data.get('id')
                        self.email = data.get('email')
                        self.created_at = data.get('created_at')
                        self.last_sign_in_at = data.get('last_sign_in_at')
                        self.app_metadata = {
                            'is_admin': data.get('is_admin') == 'true',
                            'has_ai_access': data.get('has_ai_access') == 'true'
                        }
                
                users_response = type('obj', (object,), {'users': [MockUser(user) for user in result.data]})
            except Exception as inner_e:
                logger.error(f"Fallback query failed: {inner_e}")
                raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")
            
        # Process user data to match our expected format
        users = []
        for user in users_response.users:
            user_data = {
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at,
                "last_sign_in_at": user.last_sign_in_at,
                "is_admin": False,
                "has_ai_access": False
            }
        
            # Extract metadata
            if hasattr(user, 'app_metadata') and user.app_metadata:
                if 'is_admin' in user.app_metadata:
                    user_data["is_admin"] = user.app_metadata["is_admin"] == True
                if 'has_ai_access' in user.app_metadata:
                    user_data["has_ai_access"] = user.app_metadata["has_ai_access"] == True
                
            # Special case for admin email
            if user.email and user.email.lower() == 'defom.ai.agent@gmail.com':
                user_data["is_admin"] = True
                user_data["has_ai_access"] = True
            
            users.append(user_data)
        
        # Sort by created_at
        users.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {"success": True, "users": users}
    except Exception as e:
        logger.error(f"Failed to list users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")

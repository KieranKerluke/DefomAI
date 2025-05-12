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
        
        # Insert directly using Supabase client
        result = await client.from_("ai_activation_codes").insert({
            "id": code_id,
            "code_value": code_value,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "generated_by_admin_id": admin_user["id"],
            "is_claimed": False
        }).execute()
        
        if result.error:
            raise Exception(f"Supabase error: {result.error.message}")
            
        return {"success": True, "code": code_value, "id": code_id}
    except Exception as e:
        logger.error(f"Failed to generate code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate code: {str(e)}")

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
        # Try to use the function we created
        result = await db.execute_single(
            """
            SELECT activate_ai_access($1, $2) as success;
            """,
            code, user["id"]
        )
        
        if result and result.get("success") == True:
            return {"success": True, "message": "AI access activated successfully"}
        
        # If the function call failed or returned false, check manually
        code_record = await db.fetch_one(
            """
            SELECT id FROM ai_activation_codes
            WHERE code_value = $1 AND is_active = true AND is_claimed = false
            """,
            code
        )
        
        if not code_record:
            return {"success": False, "message": "Invalid or already claimed code"}
        
        # Mark code as claimed
        await db.execute(
            """
            UPDATE ai_activation_codes
            SET is_claimed = true, claimed_by_user_id = $1, claimed_at = $2
            WHERE id = $3
            """,
            user["id"], datetime.now(), code_record["id"]
        )
        
        # Update user's AI access in raw_app_meta_data
        await db.execute(
            """
            UPDATE auth.users
            SET raw_app_meta_data = raw_app_meta_data || '{"has_ai_access": true}'::jsonb
            WHERE id = $1
            """,
            user["id"]
        )
        
        return {"success": True, "message": "AI access activated successfully"}
    except Exception as e:
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
        result = await client.from_("ai_activation_codes").select("*").order("created_at", desc=True).execute()
        
        if result.error:
            raise Exception(f"Supabase error: {result.error.message}")
            
        # Get user emails for the generated_by and claimed_by fields
        codes = result.data
        
        # Enrich the data with user emails where possible
        for code in codes:
            if code.get("generated_by_admin_id"):
                try:
                    user_result = await client.from_("users").select("email").eq("id", code["generated_by_admin_id"]).execute()
                    if user_result.data and len(user_result.data) > 0:
                        code["generated_by"] = user_result.data[0]["email"]
                except Exception:
                    pass
                    
            if code.get("claimed_by_user_id"):
                try:
                    user_result = await client.from_("users").select("email").eq("id", code["claimed_by_user_id"]).execute()
                    if user_result.data and len(user_result.data) > 0:
                        code["claimed_by"] = user_result.data[0]["email"]
                except Exception:
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
        users_response = await client.auth.admin.list_users()
        
        if hasattr(users_response, 'error') and users_response.error:
            raise Exception(f"Supabase error: {users_response.error.message}")
            
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

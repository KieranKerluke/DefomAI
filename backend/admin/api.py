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
        except Exception as e:
            logger.error(f"Error inserting activation code: {e}")
            raise Exception(f"Failed to generate activation code: {str(e)}")
            
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
        
        # Check for the activation code directly
        try:
            code_result = await client.from_("ai_activation_codes") \
                .select("id") \
                .eq("code_value", code) \
                .eq("is_active", True) \
                .eq("is_claimed", False) \
                .execute()
            
            code_record = code_result.data[0] if code_result.data and len(code_result.data) > 0 else None
        except Exception as e:
            logger.error(f"Error checking activation code: {e}")
            raise Exception(f"Failed to verify activation code: {str(e)}")
        
        if not code_record:
            return {"success": False, "message": "Invalid or already claimed code"}
        
        # Mark code as claimed
        try:
            await client.from_("ai_activation_codes") \
                .update({
                    "is_claimed": True,
                    "claimed_by_user_id": user["id"],
                    "claimed_at": datetime.now().isoformat()
                }) \
                .eq("id", code_record["id"]) \
                .execute()
        except Exception as e:
            logger.error(f"Error marking code as claimed: {e}")
            raise Exception(f"Failed to mark activation code as claimed: {str(e)}")
        
        # Update user's AI access using the auth admin API
        try:
            # Get current user data first
            user_response = await client.auth.admin.get_user_by_id(user["id"])
            if user_response and hasattr(user_response, 'user') and user_response.user:
                current_user = user_response.user
                
                # Update app metadata
                app_metadata = current_user.app_metadata or {}
                app_metadata["has_ai_access"] = True
                
                # Update the user with new metadata
                await client.auth.admin.update_user_by_id(
                    user["id"],
                    {"app_metadata": app_metadata}
                )
            else:
                logger.error("Could not retrieve user data for update")
                raise Exception("Failed to retrieve user data for update")
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
                    # Try to get user email using the auth admin API
                    user_response = await client.auth.admin.get_user_by_id(code["generated_by_admin_id"])
                    if user_response and hasattr(user_response, 'user') and user_response.user:
                        code["generated_by"] = user_response.user.email
                except Exception as e:
                    logger.error(f"Error getting user email: {e}")
                    pass
                    
            if code.get("claimed_by_user_id"):
                try:
                    # Try to get user email using the auth admin API
                    user_response = await client.auth.admin.get_user_by_id(code["claimed_by_user_id"])
                    if user_response and hasattr(user_response, 'user') and user_response.user:
                        code["claimed_by"] = user_response.user.email
                except Exception as e:
                    logger.error(f"Error getting user email: {e}")
                    pass
        
        return {"success": True, "codes": codes}
    except Exception as e:
        logger.error(f"Failed to list codes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list codes: {str(e)}")

@router.delete("/admin/activation-codes/{code_id}")
async def delete_activation_code(code_id: str, request: Request, admin_user=Depends(admin_required)):
    """
    Delete an activation code.
    Only accessible by admin users.
    """
    try:
        # Get Supabase client
        client = await db.client
        
        # Delete the activation code
        result = await client.from_("ai_activation_codes").delete().eq("id", code_id).execute()
        
        if hasattr(result, 'error') and result.error:
            raise Exception(f"Supabase error: {result.error.message}")
        
        # If the code was claimed, revoke AI access for the user
        try:
            # First get the code to check if it was claimed
            code_result = await client.from_("ai_activation_codes") \
                .select("claimed_by_user_id, is_claimed") \
                .eq("id", code_id) \
                .execute()
            
            if code_result.data and len(code_result.data) > 0 and code_result.data[0].get("is_claimed") == True:
                user_id = code_result.data[0].get("claimed_by_user_id")
                if user_id:
                    # Get current user data
                    user_response = await client.auth.admin.get_user_by_id(user_id)
                    if user_response and hasattr(user_response, 'user') and user_response.user:
                        current_user = user_response.user
                        
                        # Update app metadata to revoke AI access
                        app_metadata = current_user.app_metadata or {}
                        app_metadata["has_ai_access"] = False
                        
                        # Update the user with new metadata
                        await client.auth.admin.update_user_by_id(
                            user_id,
                            {"app_metadata": app_metadata}
                        )
        except Exception as inner_e:
            logger.error(f"Error revoking AI access: {inner_e}")
            # Continue with deletion even if revoking access fails
        
        return {"success": True, "message": "Activation code deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete activation code: {str(e)}")

@router.put("/admin/activation-codes/{code_id}/suspend")
async def suspend_activation_code(code_id: str, request: Request, admin_user=Depends(admin_required)):
    """
    Suspend or unsuspend an activation code.
    Only accessible by admin users.
    """
    try:
        # Get request body to check if we're suspending or unsuspending
        data = await request.json()
        is_suspended = data.get("is_suspended", True)  # Default to suspending
        
        # Get Supabase client
        client = await db.client
        
        # First get the code to check if it was claimed
        code_result = await client.from_("ai_activation_codes") \
            .select("claimed_by_user_id, is_claimed, is_active") \
            .eq("id", code_id) \
            .execute()
        
        if not code_result.data or len(code_result.data) == 0:
            raise HTTPException(status_code=404, detail="Activation code not found")
            
        code_data = code_result.data[0]
        
        # Update the activation code status
        result = await client.from_("ai_activation_codes") \
            .update({"is_active": not is_suspended}) \
            .eq("id", code_id) \
            .execute()
        
        if hasattr(result, 'error') and result.error:
            raise Exception(f"Supabase error: {result.error.message}")
        
        # If the code was claimed, update the user's AI access
        if code_data.get("is_claimed") == True:
            user_id = code_data.get("claimed_by_user_id")
            if user_id:
                try:
                    # Get current user data
                    user_response = await client.auth.admin.get_user_by_id(user_id)
                    if user_response and hasattr(user_response, 'user') and user_response.user:
                        current_user = user_response.user
                        
                        # Update app metadata to match suspension status
                        app_metadata = current_user.app_metadata or {}
                        app_metadata["has_ai_access"] = not is_suspended
                        
                        # Update the user with new metadata
                        await client.auth.admin.update_user_by_id(
                            user_id,
                            {"app_metadata": app_metadata}
                        )
                except Exception as inner_e:
                    logger.error(f"Error updating user AI access: {inner_e}")
                    # Continue with suspension even if updating user fails
        
        action = "suspended" if is_suspended else "unsuspended"
        return {"success": True, "message": f"Activation code {action} successfully"}
    except Exception as e:
        logger.error(f"Failed to suspend/unsuspend code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to suspend/unsuspend activation code: {str(e)}")

@router.get("/check-ai-access")
async def check_ai_access(request: Request):
    """
    Check if the current user has AI access and if their access is suspended.
    Returns detailed status information.
    """
    try:
        # Get user from request
        user = await get_user_from_request(request)
        
        if not user:
            return {
                "has_access": False,
                "is_suspended": False,
                "message": "Authentication required",
                "status": "unauthenticated"
            }
        
        # Admins automatically have AI access
        if user.get('is_admin'):
            return {
                "has_access": True,
                "is_suspended": False,
                "message": "Admin access granted",
                "status": "admin"
            }
            
        # Check if user has AI access flag
        has_ai_access = user.get('has_ai_access', False)
        
        if not has_ai_access:
            return {
                "has_access": False,
                "is_suspended": False,
                "message": "AI access required. Please use an activation code to enable AI features.",
                "status": "no_access"
            }
        
        # Check if the user's activation code is suspended
        client = await db.client
        
        # Find the user's activation code
        code_result = await client.from_("ai_activation_codes") \
            .select("is_active, code_value") \
            .eq("claimed_by_user_id", user["id"]) \
            .eq("is_claimed", True) \
            .execute()
            
        # If we found a code and it's not active, the user is suspended
        if code_result.data and len(code_result.data) > 0:
            code_data = code_result.data[0]
            is_active = code_data.get("is_active", True)
            
            if not is_active:
                return {
                    "has_access": False,
                    "is_suspended": True,
                    "message": "Your AI access has been suspended. Please contact support for more information.",
                    "status": "suspended",
                    "code": code_data.get("code_value")
                }
            else:
                return {
                    "has_access": True,
                    "is_suspended": False,
                    "message": "AI access granted",
                    "status": "active",
                    "code": code_data.get("code_value")
                }
        
        # User has AI access flag but no code found (unusual case)
        return {
            "has_access": True,
            "is_suspended": False,
            "message": "AI access granted",
            "status": "active",
            "code": None
        }
    except Exception as e:
        logger.error(f"Error checking AI access: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check AI access: {str(e)}")

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

from fastapi import APIRouter, Depends, HTTPException, Request
import uuid
import secrets
import string
from datetime import datetime
from services.supabase import DBConnection
from utils.auth_utils import get_user_from_request, admin_required
from utils.logger import logger

router = APIRouter()

# We're using the implementations in this file instead of including the separate routers
# to avoid duplicate endpoint conflicts
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

# This endpoint is now handled by the standalone activate_ai.py module
# Keeping this commented out to avoid endpoint conflicts
# @router.post("/activate-ai")
# async def activate_ai(request: Request):
#     """Activate AI access for a user using an activation code."""
#     # Implementation moved to standalone module
#     pass

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
        
        # First get the code to check if it was claimed before deleting it
        code_result = await client.from_("ai_activation_codes") \
            .select("*") \
            .eq("id", code_id) \
            .execute()
        
        if not code_result.data or len(code_result.data) == 0:
            raise HTTPException(status_code=404, detail="Activation code not found")
            
        code_data = code_result.data[0]
        user_id = code_data.get("claimed_by_user_id")
        was_claimed = code_data.get("is_claimed") == True
        code_value = code_data.get("code_value")
        
        # Now delete the activation code
        result = await client.from_("ai_activation_codes").delete().eq("id", code_id).execute()
        
        if hasattr(result, 'error') and result.error:
            raise Exception(f"Supabase error: {result.error.message}")
        
        # If the code was claimed, revoke AI access for the user and record the blocked status
        if was_claimed and user_id:
            try:
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
                    
                    # Create or update access status record to indicate blocked status
                    # First check if a record already exists
                    status_check = await client.from_("ai_access_status").select("*").eq("user_id", user_id).execute()
                    
                    if status_check.data and len(status_check.data) > 0:
                        # Update existing record
                        await client.from_("ai_access_status").update({
                            "status": "blocked",
                            "message": "Your access has been blocked by an administrator. Please contact support for assistance.",
                            "updated_at": datetime.now().isoformat(),
                            "updated_by": admin_user["id"],
                            "code_value": code_value
                        }).eq("user_id", user_id).execute()
                    else:
                        # Create new record
                        await client.from_("ai_access_status").insert({
                            "user_id": user_id,
                            "status": "blocked",
                            "message": "Your access has been blocked by an administrator. Please contact support for assistance.",
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat(),
                            "updated_by": admin_user["id"],
                            "code_value": code_value
                        }).execute()
                    
                    logger.info(f"User {user_id} has been blocked after code deletion")
            except Exception as inner_e:
                logger.error(f"Error revoking AI access: {inner_e}")
                # Continue with deletion even if revoking access fails
        
        return {"success": True, "message": "Activation code deleted successfully"}
    except HTTPException:
        raise
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
        # Get Supabase client
        client = await db.client
        
        # Get the current status of the code
        try:
            code_result = await client.from_("ai_activation_codes").select("*").eq("id", code_id).execute()
            
            if not code_result.data or len(code_result.data) == 0:
                raise HTTPException(status_code=404, detail="Activation code not found")
                
            code_data = code_result.data[0]
            current_status = code_data.get("is_active", True)
            code_value = code_data.get("code_value")
            
            # Toggle the status
            new_status = not current_status
            
            # Update the code
            update_result = await client.from_("ai_activation_codes").update({
                "is_active": new_status,
                "updated_at": datetime.now().isoformat()
            }).eq("id", code_id).execute()
            
            if hasattr(update_result, 'error') and update_result.error:
                raise Exception(f"Supabase error: {update_result.error.message}")
                
            # If the code is claimed by a user, update their AI access status
            if code_data.get("is_claimed") and code_data.get("claimed_by_user_id"):
                user_id = code_data.get("claimed_by_user_id")
                
                if not new_status:  # If we're suspending the code
                    try:
                        # Update the user's metadata to remove AI access
                        await client.auth.admin.update_user_by_id(
                            user_id,
                            {"app_metadata": {"has_ai_access": False}}
                        )
                        
                        # Create or update access status record to indicate suspended status
                        status_check = await client.from_("ai_access_status").select("*").eq("user_id", user_id).execute()
                        
                        if status_check.data and len(status_check.data) > 0:
                            # Update existing record
                            await client.from_("ai_access_status").update({
                                "status": "suspended",
                                "message": "Your access has been temporarily suspended by an administrator. Please contact support for assistance.",
                                "updated_at": datetime.now().isoformat(),
                                "updated_by": admin_user["id"],
                                "code_value": code_value
                            }).eq("user_id", user_id).execute()
                        else:
                            # Create new record
                            await client.from_("ai_access_status").insert({
                                "user_id": user_id,
                                "status": "suspended",
                                "message": "Your access has been temporarily suspended by an administrator. Please contact support for assistance.",
                                "created_at": datetime.now().isoformat(),
                                "updated_at": datetime.now().isoformat(),
                                "updated_by": admin_user["id"],
                                "code_value": code_value
                            }).execute()
                        
                        logger.info(f"Suspended AI access for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error updating user metadata: {str(e)}")
                        # Continue anyway - the code status is already updated
                else:  # If we're unsuspending the code
                    try:
                        # Update the user's metadata to restore AI access
                        await client.auth.admin.update_user_by_id(
                            user_id,
                            {"app_metadata": {"has_ai_access": True}}
                        )
                        
                        # Update access status record to indicate active status
                        status_check = await client.from_("ai_access_status").select("*").eq("user_id", user_id).execute()
                        
                        if status_check.data and len(status_check.data) > 0:
                            # Update existing record
                            await client.from_("ai_access_status").update({
                                "status": "active",
                                "message": "Your access has been restored.",
                                "updated_at": datetime.now().isoformat(),
                                "updated_by": admin_user["id"],
                                "code_value": code_value
                            }).eq("user_id", user_id).execute()
                        
                        logger.info(f"Restored AI access for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error updating user metadata: {str(e)}")
                        # Continue anyway - the code status is already updated
            
            status_text = "suspended" if not new_status else "unsuspended"
            return {"success": True, "message": f"Activation code {status_text} successfully", "is_active": new_status}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error toggling activation code: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to toggle activation code: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle activation code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle activation code: {str(e)}")

@router.get("/check-ai-access", include_in_schema=True)
async def check_ai_access(request: Request):
    """
    Check if the current user has AI access and if their access is suspended or blocked.
    Returns detailed status information including any messages from the admin.
    """
    try:
        # Get user from request
        user = await get_user_from_request(request)
        
        if not user:
            return {
                "has_access": False,
                "is_suspended": False,
                "is_blocked": False,
                "message": "Authentication required",
                "status": "unauthenticated"
            }
        
        # Get Supabase client
        client = await db.client
        
        # Use the SQL function to check AI access status
        try:
            # Call the check_ai_access function we created in SQL
            access_result = await client.rpc('check_ai_access', {
                'user_id': user["id"]
            }).execute()
            
            if access_result.data and len(access_result.data) > 0:
                access_data = access_result.data[0]
                
                # Return the access status from the function
                return {
                    "has_access": access_data.get("has_access", False),
                    "is_suspended": access_data.get("is_suspended", False),
                    "is_blocked": access_data.get("is_blocked", False),
                    "message": access_data.get("message", "No AI access"),
                    "status": access_data.get("status", "no_access"),
                    "code": access_data.get("code")
                }
            
        except Exception as e:
            logger.error(f"Error calling check_ai_access function: {str(e)}")
            # Fall back to the old method if the function call fails
        
        # Admins automatically have AI access
        if user.get('is_admin'):
            return {
                "has_access": True,
                "is_suspended": False,
                "is_blocked": False,
                "message": "Admin access granted",
                "status": "admin"
            }
            
        # Check if user has any status records (blocked, suspended, etc.)
        status_result = await client.from_("ai_access_status").select("*").eq("user_id", user["id"]).execute()
        
        if status_result.data and len(status_result.data) > 0:
            status_data = status_result.data[0]
            
            # Return the status from the table
            return {
                "has_access": status_data.get("has_access", False),
                "is_suspended": status_data.get("is_suspended", False),
                "is_blocked": status_data.get("is_blocked", False),
                "message": status_data.get("message", "No AI access"),
                "status": status_data.get("status", "no_access"),
                "code": status_data.get("code")
            }
        
        # Find the user's activation code
        code_result = await client.from_("ai_activation_codes") \
            .select("is_active, code_value") \
            .eq("claimed_by_user_id", user["id"]) \
            .eq("is_claimed", True) \
            .execute()
            
        # If no code is found, the user needs to enter a passcode
        if not code_result.data or len(code_result.data) == 0:
            # Create or update the ai_access_status record
            try:
                # Check if a record already exists
                status_check = await client.from_("ai_access_status").select("id").eq("user_id", user["id"]).execute()
                
                if status_check.data and len(status_check.data) > 0:
                    # Update existing record
                    await client.from_("ai_access_status").update({
                        "has_access": False,
                        "is_suspended": False,
                        "is_blocked": False,
                        "status": "no_access",
                        "message": "AI access required. Please enter an activation code to use the AI features.",
                        "updated_at": datetime.now().isoformat()
                    }).eq("user_id", user["id"]).execute()
                else:
                    # Create new record
                    await client.from_("ai_access_status").insert({
                        "user_id": user["id"],
                        "has_access": False,
                        "is_suspended": False,
                        "is_blocked": False,
                        "status": "no_access",
                        "message": "AI access required. Please enter an activation code to use the AI features."
                    }).execute()
            except Exception as e:
                logger.error(f"Error updating ai_access_status: {str(e)}")
            
            return {
                "has_access": False,
                "is_suspended": False,
                "is_blocked": False,
                "message": "AI access required. Please enter an activation code to use the AI features.",
                "status": "no_access"
            }
        
        # At this point, we know the user has a valid activation code
        # Now check if the code is active or suspended
        code_data = code_result.data[0]
        is_active = code_data.get("is_active", True)
        code_value = code_data.get("code_value")
        
        if not is_active:
            # Code is suspended - update the ai_access_status record
            try:
                # Check if a record already exists
                status_check = await client.from_("ai_access_status").select("id").eq("user_id", user["id"]).execute()
                
                if status_check.data and len(status_check.data) > 0:
                    # Update existing record
                    await client.from_("ai_access_status").update({
                        "has_access": False,
                        "is_suspended": True,
                        "is_blocked": False,
                        "status": "suspended",
                        "message": "Your AI access has been suspended. Please contact support for more information.",
                        "code": code_value,
                        "updated_at": datetime.now().isoformat()
                    }).eq("user_id", user["id"]).execute()
                else:
                    # Create new record
                    await client.from_("ai_access_status").insert({
                        "user_id": user["id"],
                        "has_access": False,
                        "is_suspended": True,
                        "is_blocked": False,
                        "status": "suspended",
                        "message": "Your AI access has been suspended. Please contact support for more information.",
                        "code": code_value
                    }).execute()
            except Exception as e:
                logger.error(f"Error updating ai_access_status: {str(e)}")
            
            # Return suspended status
            return {
                "has_access": False,
                "is_suspended": True,
                "is_blocked": False,
                "message": "Your AI access has been suspended. Please contact support for more information.",
                "status": "suspended",
                "code": code_value
            }
        
        # Code is valid and active - update the ai_access_status record
        try:
            # Check if a record already exists
            status_check = await client.from_("ai_access_status").select("id").eq("user_id", user["id"]).execute()
            
            if status_check.data and len(status_check.data) > 0:
                # Update existing record
                await client.from_("ai_access_status").update({
                    "has_access": True,
                    "is_suspended": False,
                    "is_blocked": False,
                    "status": "active",
                    "message": "AI access granted",
                    "code": code_value,
                    "updated_at": datetime.now().isoformat()
                }).eq("user_id", user["id"]).execute()
            else:
                # Create new record
                await client.from_("ai_access_status").insert({
                    "user_id": user["id"],
                    "has_access": True,
                    "is_suspended": False,
                    "is_blocked": False,
                    "status": "active",
                    "message": "AI access granted",
                    "code": code_value
                }).execute()
        except Exception as e:
            logger.error(f"Error updating ai_access_status: {str(e)}")
        
        # Grant access
        return {
            "has_access": True,
            "is_suspended": False,
            "is_blocked": False,
            "message": "AI access granted",
            "status": "active",
            "code": code_value
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

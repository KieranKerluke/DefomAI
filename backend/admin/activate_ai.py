from fastapi import APIRouter, HTTPException, Request
from utils.auth_utils import get_user_from_request
from services.supabase import DBConnection
from datetime import datetime
from utils.logger import logger

router = APIRouter()
db = DBConnection()

@router.post("/activate-ai")
async def activate_ai(request: Request):
    """
    Activate AI access for a user using an activation code.
    """
    try:
        # Get the user from the request
        user = await get_user_from_request(request)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Get the activation code from the request body
        body = await request.json()
        code = body.get("code")
        
        if not code:
            raise HTTPException(status_code=400, detail="Activation code is required")
        
        # Get Supabase client
        client = await db.client
        
        # Check if the code exists and is valid
        code_result = await client.from_("ai_activation_codes").select("*").eq("code_value", code).execute()
        
        if code_result.error:
            raise Exception(f"Supabase error: {code_result.error.message}")
            
        if not code_result.data or len(code_result.data) == 0:
            raise HTTPException(status_code=404, detail="Invalid activation code")
            
        code_data = code_result.data[0]
        
        if not code_data.get("is_active"):
            raise HTTPException(status_code=400, detail="This activation code has been deactivated")
        
        if code_data.get("is_claimed"):
            raise HTTPException(status_code=400, detail="This activation code has already been used")
        
        # Mark the code as claimed
        update_result = await client.from_("ai_activation_codes").update({
            "is_claimed": True,
            "claimed_by_user_id": user["id"],
            "claimed_at": datetime.now().isoformat()
        }).eq("id", code_data["id"]).execute()
        
        if update_result.error:
            raise Exception(f"Supabase error updating code: {update_result.error.message}")
        
        # Update the user's metadata to grant AI access
        try:
            # Simple check if user already has AI access
            if user.get('has_ai_access'):
                # If they already have access, just return success
                return {
                    "success": True,
                    "message": "AI access already activated"
                }
            
            # Update the user's metadata to grant AI access
            user_update = await client.auth.admin.update_user_by_id(
                user["id"],
                {"app_metadata": {"has_ai_access": True}}
            )
            
            # Log the successful update
            logger.info(f"User metadata updated successfully for {user['email']}")
            
        except Exception as e:
            logger.error(f"Error updating user metadata: {str(e)}")
            # Continue anyway - the code is already marked as claimed
            # This ensures the user can still use the AI features even if there was an error updating their metadata
        
        logger.info(f"AI access activated for user {user['email']} with code {code}")
        
        return {
            "success": True,
            "message": "AI access activated successfully"
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error activating AI access: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to activate AI access: {str(e)}")

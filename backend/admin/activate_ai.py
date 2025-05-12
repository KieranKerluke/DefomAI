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
        
        # Check if the code exists and is valid
        code_data = await db.execute_single(
            """
            SELECT id, is_active, is_claimed
            FROM ai_activation_codes
            WHERE code_value = $1
            """,
            code
        )
        
        if not code_data:
            raise HTTPException(status_code=404, detail="Invalid activation code")
        
        if not code_data.get("is_active"):
            raise HTTPException(status_code=400, detail="This activation code has been deactivated")
        
        if code_data.get("is_claimed"):
            raise HTTPException(status_code=400, detail="This activation code has already been used")
        
        # Mark the code as claimed
        await db.execute(
            """
            UPDATE ai_activation_codes
            SET is_claimed = true, claimed_by_user_id = $1, claimed_at = $2
            WHERE id = $3
            """,
            user["id"], datetime.now(), code_data["id"]
        )
        
        # Update the user's metadata to grant AI access
        client = await db.client
        await client.auth.admin.update_user_by_id(
            user["id"],
            {"app_metadata": {"has_ai_access": True}}
        )
        
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

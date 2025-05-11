from fastapi import APIRouter, Depends, Request
from utils.auth_utils import ai_access_required

router = APIRouter()

@router.get("/check-ai-access")
async def check_ai_access(request: Request, user=Depends(ai_access_required)):
    """
    Simple endpoint to check if a user has AI access.
    This endpoint will return a 403 error if the user doesn't have AI access,
    or a success message if they do.
    """
    return {
        "success": True,
        "message": "You have AI access",
        "user_id": user["id"],
        "email": user["email"],
        "is_admin": user.get("is_admin", False)
    }

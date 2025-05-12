from fastapi import Request, HTTPException
from utils.auth_utils import get_user_from_request
from utils.logger import logger

async def verify_ai_access(request: Request):
    """
    Middleware to verify AI access for all agent-related endpoints.
    This provides a server-side check that cannot be bypassed by frontend modifications.
    """
    # Skip for non-agent endpoints
    path = request.url.path
    if not (path.startswith("/api/agent") or 
            path.startswith("/api/threads") or 
            path.startswith("/api/projects")):
        return
        
    # Get user from request
    user = await get_user_from_request(request)
    
    if not user:
        logger.warning(f"Unauthorized access attempt to {path}")
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if user is admin or has AI access
    has_admin = user.get('is_admin', False)
    has_ai_access = user.get('has_ai_access', False)
    
    if not (has_admin or has_ai_access):
        logger.warning(f"Access denied to {path} for user {user.get('email')} - No AI access")
        raise HTTPException(
            status_code=403,
            detail="AI access required. Please activate your account with an access code."
        )
        
    # If the user has AI access but is not an admin, check if their activation code is suspended
    if has_ai_access and not has_admin:
        try:
            from services.supabase import DBConnection
            db = DBConnection()
            client = await db.client
            
            # Find the user's activation code
            code_result = await client.from_("ai_activation_codes") \
                .select("is_active") \
                .eq("claimed_by_user_id", user["id"]) \
                .eq("is_claimed", True) \
                .execute()
                
            # If we found a code and it's not active, the user is suspended
            if code_result.data and len(code_result.data) > 0:
                is_active = code_result.data[0].get("is_active")
                if is_active is False:  # Explicitly check for False, not just falsy values
                    logger.warning(f"Access denied to {path} for user {user.get('email')} - Suspended access")
                    raise HTTPException(
                        status_code=403,
                        detail="Your AI access has been suspended. Please contact support for more information."
                    )
        except Exception as e:
            # If there's an error checking the code, log it but allow access if user has AI access flag
            logger.error(f"Error checking activation code status: {e}")
            # Continue with the request since the user has the AI access flag
        
    # User has access, continue with the request
    return

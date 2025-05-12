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
        
    # User has access, continue with the request
    return

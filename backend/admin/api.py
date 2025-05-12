from fastapi import APIRouter, Depends, HTTPException, Request
import uuid
import secrets
import string
from datetime import datetime
from services.supabase import DBConnection
from utils.auth_utils import get_user_from_request, admin_required
from admin.check_ai_access import router as check_ai_access_router
from admin.activate_ai import router as activate_ai_router

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
        
        # Insert into database using the function we created
        result = await db.execute_single(
            """
            SELECT generate_activation_code($1) as code;
            """,
            admin_user["id"]
        )
        
        if not result or "code" not in result:
            # If the function call failed, fall back to direct insert
            code_id = str(uuid.uuid4())
            await db.execute(
                """
                INSERT INTO ai_activation_codes 
                (id, code_value, is_active, created_at, generated_by_admin_id, is_claimed)
                VALUES ($1, $2, true, $3, $4, false)
                """,
                code_id, code_value, datetime.now(), admin_user["id"]
            )
            return {"success": True, "code": code_value, "id": code_id}
        
        return {"success": True, "code": result["code"]}
    except Exception as e:
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
        codes = await db.fetch_all(
            """
            SELECT 
                ac.id, 
                ac.code_value, 
                ac.is_active, 
                ac.created_at, 
                ac.is_claimed, 
                ac.claimed_at,
                ac.notes,
                u1.email as generated_by,
                u2.email as claimed_by
            FROM ai_activation_codes ac
            LEFT JOIN auth.users u1 ON ac.generated_by_admin_id = u1.id
            LEFT JOIN auth.users u2 ON ac.claimed_by_user_id = u2.id
            ORDER BY ac.created_at DESC
            """
        )
        
        return {"success": True, "codes": codes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list codes: {str(e)}")

@router.get("/admin/users")
async def list_users(request: Request, admin_user=Depends(admin_required)):
    """
    List all users with their AI access status.
    Only accessible by admin users.
    """
    try:
        users = await db.fetch_all(
            """
            SELECT 
                id, 
                email, 
                raw_app_meta_data->>'is_admin' as is_admin,
                raw_app_meta_data->>'has_ai_access' as has_ai_access,
                created_at,
                last_sign_in_at
            FROM auth.users
            ORDER BY created_at DESC
            """
        )
        
        return {"success": True, "users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")

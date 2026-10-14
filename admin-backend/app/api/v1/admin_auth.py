from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.api.v1.auth import admin_login, admin_logout, get_admin_me
from app.schemas.auth import AdminLoginRequest, LoginResponse, LogoutResponse, SessionStatusResponse

admin_auth_router = APIRouter(prefix="/admin/auth", tags=["Admin Authentication"])

@admin_auth_router.post("/login", response_model=LoginResponse, summary="Admin authentication endpoint")
async def admin_auth_login(
    payload: AdminLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    return await admin_login(payload=payload, request=request, response=response, db=db)

@admin_auth_router.post("/logout", response_model=LogoutResponse, summary="Admin logout endpoint")
async def admin_auth_logout(response: Response):
    return await admin_logout(response=response)

@admin_auth_router.get("/me", response_model=SessionStatusResponse, summary="Verify Admin session status")
async def admin_auth_me(request: Request, db: AsyncSession = Depends(get_db_session)):
    return await get_admin_me(request=request, db=db)

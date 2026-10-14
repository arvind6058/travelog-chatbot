from typing import Optional
import secrets
import uuid
import hashlib
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.core.config import get_settings
from app.core.dependencies import (
    ADMIN_COOKIE_NAME,
    CUSTOMER_COOKIE_NAME,
)
from app.core.logging import logger
from app.core.rate_limit import auth_limiter
from app.core.security import (
    ADMIN_ROLES,
    TOKEN_TYPE_ADMIN,
    TOKEN_TYPE_CUSTOMER,
    PasswordTooLongError,
    bearer_or_cookie_token,
    constant_time_compare,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.password_reset_token import PasswordResetToken
from app.schemas.auth import (
    AdminLoginRequest,
    AuthenticatedUser,
    CustomerLoginRequest,
    CustomerRegisterRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    LoginResponse,
    LogoutResponse,
    SessionStatusResponse,
)
from app.services.google_auth_service import GoogleAuthService
from app.services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()

OAUTH_STATE_COOKIE = "travelogix_oauth_state"


def _session_cookie_max_age() -> int:
    """Cookie lifetime must not outlive the token it carries."""
    return max(60, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


def _set_session_cookie(response: Response, key: str, token: str) -> None:
    response.set_cookie(
        key=key,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=_session_cookie_max_age(),
    )


def _clear_session_cookie(response: Response, key: str) -> None:
    response.delete_cookie(key=key, path="/", httponly=True, secure=settings.cookie_secure, samesite="lax")


# ============================================================================
# ADMIN AUTHENTICATION
# ============================================================================

@router.post("/admin/login", response_model=LoginResponse, summary="Admin authentication endpoint")
async def admin_login(
    payload: AdminLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Authenticate an administrator against the database.

    The previous implementation also accepted a plaintext admin password read
    from the environment and compared it with ``==``; that path bypassed the
    database entirely (so the credential could not be revoked) and leaked
    timing information. Administrators are now real, revocable database rows.
    """
    limiter = auth_limiter()
    limit_key = limiter.client_key(request, "admin_login", payload.email)
    await limiter.hit(limit_key)

    email = payload.email.strip()
    stmt = select(User).where(User.email == email, User.role.in_(list(ADMIN_ROLES)))
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    if admin is None or not verify_password(payload.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative credentials or insufficient authorization.",
        )

    if (admin.status or "ACTIVE").upper() != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This administrative account is not active.",
        )

    await limiter.reset(limit_key)

    token = create_access_token(
        data={"sub": admin.id, "email": admin.email, "role": admin.role},
        token_type=TOKEN_TYPE_ADMIN,
    )
    _set_session_cookie(response, ADMIN_COOKIE_NAME, token)

    # An audit failure must not leave the session unusable.
    try:
        db.add(
            AuditLog(
                id=str(uuid.uuid4()),
                actor=admin.email,
                action="ADMIN_LOGIN",
                entity_type="USER",
                entity_id=admin.id,
                description=f"Admin '{admin.email}' logged into internal logistics console.",
                is_demo=False,
                timestamp=datetime.now(timezone.utc),
            )
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.warning(f"Could not write the admin login audit record: {exc}")

    return LoginResponse(
        message="Admin authentication successful.",
        user=AuthenticatedUser(id=admin.id, email=admin.email, name=admin.full_name, role=admin.role),
    )


@router.post("/admin/logout", response_model=LogoutResponse, summary="Admin logout endpoint")
async def admin_logout(response: Response):
    _clear_session_cookie(response, ADMIN_COOKIE_NAME)
    return LogoutResponse(message="Admin session logged out successfully.")


@router.get("/admin/me", response_model=SessionStatusResponse, summary="Verify Admin session status")
async def get_admin_me(request: Request, db: AsyncSession = Depends(get_db_session)):
    token = bearer_or_cookie_token(request, ADMIN_COOKIE_NAME)
    if not token:
        return SessionStatusResponse(authenticated=False)

    try:
        payload = decode_access_token(token, token_type=TOKEN_TYPE_ADMIN)
    except Exception:
        return SessionStatusResponse(authenticated=False)

    role = str(payload.get("role") or "").upper()
    if role not in ADMIN_ROLES:
        return SessionStatusResponse(authenticated=False)

    # Confirm the account still exists and is active.
    result = await db.execute(select(User).where(User.id == payload.get("sub")))
    user = result.scalar_one_or_none()
    if user is not None and (user.status or "ACTIVE").upper() != "ACTIVE":
        return SessionStatusResponse(authenticated=False)

    return SessionStatusResponse(
        authenticated=True,
        user=AuthenticatedUser(
            id=str(payload.get("sub")),
            email=str(payload.get("email")),
            name=(user.full_name if user else None),
            role=role,
        ),
    )


# ============================================================================
# CUSTOMER AUTHENTICATION
# ============================================================================

@router.post("/customer/login", response_model=LoginResponse, summary="Customer email/password authentication")
async def customer_login(
    payload: CustomerLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    limiter = auth_limiter()
    limit_key = limiter.client_key(request, "customer_login", payload.email)
    await limiter.hit(limit_key)

    email = payload.email.strip()
    result = await db.execute(select(User).where(User.email == email, User.role == "CUSTOMER"))
    user = result.scalar_one_or_none()

    # The previous implementation accepted three hardcoded email/password pairs
    # and minted a session with no database user at all. That backdoor is gone;
    # an explicit, opt-in demo account exists for local development only.
    if user is None and settings.ENABLE_DEMO_ACCOUNTS and not settings.is_production:
        if email.lower() in ("customer@example.com", "demo@travelogix.com") and payload.password == "Password123!":
            await limiter.reset(limit_key)
            return await _issue_demo_customer_session(response, email, "Demo Customer")

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect.",
        )

    if (user.status or "ACTIVE").upper() != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not active.",
        )

    await limiter.reset(limit_key)

    token = create_access_token(
        data={"sub": user.id, "email": user.email, "name": user.full_name, "role": "CUSTOMER"},
        token_type=TOKEN_TYPE_CUSTOMER,
    )
    _set_session_cookie(response, CUSTOMER_COOKIE_NAME, token)

    return LoginResponse(
        message="Customer login successful.",
        user=AuthenticatedUser(id=user.id, email=user.email, name=user.full_name, role="CUSTOMER"),
    )


async def _issue_demo_customer_session(response: Response, email: str, name: str) -> LoginResponse:
    user_id = "cust-demo-001"
    token = create_access_token(
        data={"sub": user_id, "email": email, "name": name, "role": "CUSTOMER"},
        token_type=TOKEN_TYPE_CUSTOMER,
    )
    _set_session_cookie(response, CUSTOMER_COOKIE_NAME, token)
    return LoginResponse(
        message="Demo customer login successful.",
        user=AuthenticatedUser(id=user_id, email=email, name=name, role="CUSTOMER"),
    )


@router.post("/customer/register", response_model=LoginResponse, summary="Customer registration endpoint")
async def customer_register(
    payload: CustomerRegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    limiter = auth_limiter()
    limit_key = limiter.client_key(request, "customer_register")
    await limiter.hit(limit_key)

    email = payload.email.strip()
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none() is not None:
        # Same generic message as a failed login: registration must not be a
        # user-enumeration oracle.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration could not be completed with those details.",
        )

    try:
        hashed_pw = hash_password(payload.password)
    except PasswordTooLongError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    new_user = User(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=hashed_pw,
        full_name=payload.full_name.strip(),
        phone=(payload.phone or "").strip() or None,
        role="CUSTOMER",
        status="ACTIVE",
        is_demo=False,
    )
    db.add(new_user)
    await db.commit()

    token = create_access_token(
        data={"sub": new_user.id, "email": new_user.email, "name": new_user.full_name, "role": "CUSTOMER"},
        token_type=TOKEN_TYPE_CUSTOMER,
    )
    _set_session_cookie(response, CUSTOMER_COOKIE_NAME, token)

    return LoginResponse(
        message="Registration successful.",
        user=AuthenticatedUser(
            id=new_user.id, email=new_user.email, name=new_user.full_name, role="CUSTOMER"
        ),
    )


@router.get("/customer/google/diagnostics", summary="Safe Google OAuth Configuration Diagnostics")
async def get_google_auth_diagnostics():
    """Returns safe configuration status without exposing client secrets."""
    configured = GoogleAuthService.is_configured()
    secret_set = bool(settings.google_client_secret) and configured

    return {
        "google_oauth_configured": configured,
        "client_id_configured": configured,
        "client_id_masked": GoogleAuthService.get_masked_client_id(),
        "client_secret_configured": secret_set,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }


@router.get("/customer/google/login", summary="Initiate official Google OAuth login redirect")
async def customer_google_login_redirect():
    """Generate a state token, store it in an httpOnly cookie, and redirect to Google."""
    if not GoogleAuthService.is_configured():
        return RedirectResponse(
            url=f"{settings.FRONTEND_BASE_URL}/login?error=google_oauth_not_configured",
            status_code=status.HTTP_302_FOUND,
        )

    state_token = secrets.token_urlsafe(24)
    redirect_res = RedirectResponse(
        url=GoogleAuthService.get_authorization_url(state=state_token),
        status_code=status.HTTP_302_FOUND,
    )
    redirect_res.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=state_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=600,  # 10 minutes
    )
    return redirect_res


@router.get("/customer/google/callback", summary="Official Google OAuth callback handler")
async def customer_google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Validate the OAuth state, exchange the code, then establish the session.

    The state check previously failed *open*: `if cookie_state and state and
    cookie_state != state` skipped validation entirely whenever the cookie was
    missing, enabling login CSRF / session fixation.
    """
    failure_url = f"{settings.FRONTEND_BASE_URL}/login?error=google_login_failed"
    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE)

    if not cookie_state or not state or not constant_time_compare(cookie_state, state):
        logger.warning("Rejected a Google OAuth callback with a missing or mismatched state token.")
        response = RedirectResponse(url=failure_url, status_code=status.HTTP_302_FOUND)
        _clear_session_cookie(response, OAUTH_STATE_COOKIE)
        return response

    if error or not code:
        response = RedirectResponse(url=failure_url, status_code=status.HTTP_302_FOUND)
        _clear_session_cookie(response, OAUTH_STATE_COOKIE)
        return response

    try:
        user_info = await GoogleAuthService.exchange_code_and_get_user_info(code)

        # Only a Google-verified address may be used to claim an account.
        if user_info.get("email_verified") is False:
            logger.warning("Rejected a Google login for an unverified email address.")
            return RedirectResponse(url=failure_url, status_code=status.HTTP_302_FOUND)

        email = user_info["email"].strip().lower()
        name = user_info.get("name") or email.split("@")[0]
        google_id = user_info.get("google_id") or str(uuid.uuid4())

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if user is not None:
            if (user.status or "ACTIVE").upper() != "ACTIVE":
                return RedirectResponse(url=failure_url, status_code=status.HTTP_302_FOUND)
            user_id = user.id
            full_name = user.full_name or name
        else:
            user = User(
                id=f"cust-g-{google_id[:12]}",
                email=email,
                # A random unguessable password: this account signs in via Google.
                hashed_password=hash_password(secrets.token_urlsafe(32)),
                full_name=name,
                role="CUSTOMER",
                status="ACTIVE",
                is_demo=False,
            )
            db.add(user)
            await db.commit()
            user_id = user.id
            full_name = name

        token = create_access_token(
            data={"sub": user_id, "email": email, "name": full_name, "role": "CUSTOMER"},
            token_type=TOKEN_TYPE_CUSTOMER,
        )

        redirect_res = RedirectResponse(
            url=f"{settings.FRONTEND_BASE_URL}/ai-assistant",
            status_code=status.HTTP_302_FOUND,
        )
        _set_session_cookie(redirect_res, CUSTOMER_COOKIE_NAME, token)
        _clear_session_cookie(redirect_res, OAUTH_STATE_COOKIE)
        return redirect_res

    except Exception as exc:
        logger.error(f"Google OAuth callback failed: {exc}")
        response = RedirectResponse(url=failure_url, status_code=status.HTTP_302_FOUND)
        _clear_session_cookie(response, OAUTH_STATE_COOKIE)
        return response


@router.post("/customer/logout", response_model=LogoutResponse, summary="Customer session logout")
async def customer_logout(response: Response):
    _clear_session_cookie(response, CUSTOMER_COOKIE_NAME)
    return LogoutResponse(message="Customer session logged out successfully.")


@router.get("/customer/me", response_model=SessionStatusResponse, summary="Verify Customer session status")
async def get_customer_me(request: Request, db: AsyncSession = Depends(get_db_session)):
    token = bearer_or_cookie_token(request, CUSTOMER_COOKIE_NAME)
    if not token:
        return SessionStatusResponse(authenticated=False)

    try:
        payload = decode_access_token(token, token_type=TOKEN_TYPE_CUSTOMER)
    except Exception:
        return SessionStatusResponse(authenticated=False)

    if str(payload.get("role") or "").upper() != "CUSTOMER":
        return SessionStatusResponse(authenticated=False)

    user = None
    try:
        result = await db.execute(select(User).where(User.id == payload.get("sub")))
        user = result.scalar_one_or_none()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(f"Could not load the customer for a session check: {exc}")

    if user is not None and (user.status or "ACTIVE").upper() != "ACTIVE":
        return SessionStatusResponse(authenticated=False)

    return SessionStatusResponse(
        authenticated=True,
        user=AuthenticatedUser(
            id=str(payload.get("sub")),
            email=str(payload.get("email")),
            name=str(payload.get("name") or (user.full_name if user else "Customer")),
            role="CUSTOMER",
        ),
    )


@router.post("/customer/forgot-password", summary="Initiate customer password reset")
async def customer_forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    limiter = auth_limiter()
    limit_key = limiter.client_key(request, "customer_forgot_password", payload.email)
    await limiter.hit(limit_key)

    email = payload.email.strip().lower()

    result = await db.execute(select(User).where(func.lower(User.email) == email, User.role == "CUSTOMER"))
    user = result.scalar_one_or_none()

    if user is not None and (user.status or "ACTIVE").upper() == "ACTIVE":
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

        reset_record = PasswordResetToken(
            id=str(uuid.uuid4()),
            customer_email=user.email,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
        )
        db.add(reset_record)
        await db.commit()

        EmailService.send_password_reset_email(user.email, raw_token)

    return {
        "success": True,
        "message": "If an account exists for this email, a password reset link has been sent.",
    }


@router.post("/customer/reset-password", summary="Reset customer password using valid token")
async def customer_reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    limiter = auth_limiter()
    limit_key = limiter.client_key(request, "customer_reset_password")
    await limiter.hit(limit_key)

    if payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match.",
        )

    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long.",
        )

    token_hash = hashlib.sha256(payload.token.strip().encode("utf-8")).hexdigest()
    now_utc = datetime.now(timezone.utc)

    stmt = select(PasswordResetToken).where(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > now_utc,
    )
    res = await db.execute(stmt)
    token_record = res.scalar_one_or_none()

    if token_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset link. Please request a new one.",
        )

    user_res = await db.execute(
        select(User).where(
            func.lower(User.email) == token_record.customer_email.lower(),
            User.role == "CUSTOMER",
        )
    )
    user = user_res.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer account not found for this reset token.",
        )

    try:
        new_hashed_pw = hash_password(payload.new_password)
    except PasswordTooLongError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    user.hashed_password = new_hashed_pw
    token_record.used_at = now_utc

    await db.commit()

    return {
        "success": True,
        "message": "Password reset successful. You can now sign in with your new password.",
    }

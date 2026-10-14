import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
import jwt
import bcrypt

from app.core.config import get_settings
from app.core.logging import logger

# bcrypt hashes at most 72 bytes; longer input raises inside the library, which
# used to surface as an unhandled 500 on registration.
MAX_PASSWORD_BYTES = 72

TOKEN_TYPE_CUSTOMER = "customer"
TOKEN_TYPE_ADMIN = "admin"

# Roles allowed into the logistics console.
ADMIN_ROLES = frozenset({"ADMIN", "LOGISTICS_ADMIN", "SUPERADMIN"})


class PasswordTooLongError(ValueError):
    """Raised when a password exceeds the bcrypt 72-byte limit."""


def password_byte_length(password: str) -> int:
    return len((password or "").encode("utf-8"))


def validate_password_length(password: str) -> None:
    """Reject passwords bcrypt cannot represent, with an actionable error."""
    if password_byte_length(password) > MAX_PASSWORD_BYTES:
        raise PasswordTooLongError(
            f"Password must be at most {MAX_PASSWORD_BYTES} bytes ({password_byte_length(password)} given)."
        )


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    validate_password_length(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Only malformed-hash errors are treated as a failed login; anything else is
    logged, so a broken stored hash is not silently reported as "wrong password".
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        logger.debug(f"Password verification rejected a malformed hash: {exc}")
        return False
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Unexpected error during password verification: {exc}")
        return False


def constant_time_compare(left: str, right: str) -> bool:
    """Timing-safe string comparison for secrets and OAuth state values."""
    return hmac.compare_digest((left or "").encode("utf-8"), (right or "").encode("utf-8"))


def _secret_for_type(token_type: str) -> str:
    settings = get_settings()
    if token_type == TOKEN_TYPE_ADMIN:
        return settings.admin_session_secret
    return settings.customer_session_secret


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    secret_key: Optional[str] = None,
    token_type: str = TOKEN_TYPE_CUSTOMER,
) -> str:
    """
    Create a signed JWT access token.

    Admin and customer tokens are signed with *different* secrets and carry a
    ``typ`` claim, so one family can never be replayed as the other.
    """
    settings = get_settings()
    key = secret_key or _secret_for_type(token_type)

    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode = dict(data)
    to_encode.update({
        "iat": now,
        "nbf": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
        "typ": token_type,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    })
    return jwt.encode(to_encode, key, algorithm=settings.ALGORITHM)


def _decode_with(token: str, key: str) -> Dict[str, Any]:
    settings = get_settings()
    return jwt.decode(
        token,
        key,
        algorithms=[settings.ALGORITHM],
        audience=settings.JWT_AUDIENCE,
        issuer=settings.JWT_ISSUER,
        options={"require": ["exp", "iat", "sub", "typ", "aud", "iss"]},
    )


def decode_access_token(token: str, token_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Decode and fully validate a JWT access token.

    When ``token_type`` is omitted both families are tried (used by the
    ``/me`` endpoints, which must work out who is asking before they know).
    """
    if not token:
        raise jwt.InvalidTokenError("Missing token")

    if token_type is not None:
        payload = _decode_with(token, _secret_for_type(token_type))
        if payload.get("typ") != token_type:
            raise jwt.InvalidTokenError("Token type mismatch")
        return payload

    last_error: Exception = jwt.InvalidTokenError("Unrecognised token")
    for candidate in (TOKEN_TYPE_ADMIN, TOKEN_TYPE_CUSTOMER):
        try:
            payload = _decode_with(token, _secret_for_type(candidate))
            if payload.get("typ") == candidate:
                return payload
        except jwt.InvalidTokenError as exc:
            last_error = exc
    raise last_error


def token_role(payload: Dict[str, Any]) -> str:
    return str(payload.get("role") or "").upper()


def is_admin_payload(payload: Dict[str, Any]) -> bool:
    return payload.get("typ") == TOKEN_TYPE_ADMIN and token_role(payload) in ADMIN_ROLES


def is_customer_payload(payload: Dict[str, Any]) -> bool:
    return payload.get("typ") == TOKEN_TYPE_CUSTOMER and token_role(payload) == "CUSTOMER"


def bearer_or_cookie_token(request, cookie_name: str) -> Optional[str]:
    """Read a session token from the named cookie, else an Authorization header."""
    try:
        token = request.cookies.get(cookie_name)
    except Exception:  # pragma: no cover - request without cookies
        token = None
    if token:
        return token

    header = ""
    try:
        header = request.headers.get("Authorization") or ""
    except Exception:  # pragma: no cover
        header = ""
    if header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip() or None
    return None


__all__ = [
    "ADMIN_ROLES",
    "MAX_PASSWORD_BYTES",
    "PasswordTooLongError",
    "TOKEN_TYPE_ADMIN",
    "TOKEN_TYPE_CUSTOMER",
    "bearer_or_cookie_token",
    "constant_time_compare",
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "is_admin_payload",
    "is_customer_payload",
    "password_byte_length",
    "token_role",
    "validate_password_length",
    "verify_password",
]

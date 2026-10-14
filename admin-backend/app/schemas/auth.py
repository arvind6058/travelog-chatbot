"""Request/response schemas for the authentication endpoints."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.security import MAX_PASSWORD_BYTES


class AdminLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=MAX_PASSWORD_BYTES)


class CustomerLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=MAX_PASSWORD_BYTES)


class CustomerRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=MAX_PASSWORD_BYTES)
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=32)


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(..., min_length=1, description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=MAX_PASSWORD_BYTES, description="New password")
    confirm_password: str = Field(..., min_length=8, max_length=MAX_PASSWORD_BYTES, description="Confirm password")


class AuthenticatedUser(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    role: str


class LoginResponse(BaseModel):
    success: bool = True
    message: str
    user: AuthenticatedUser


class SessionStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[AuthenticatedUser] = None


class LogoutResponse(BaseModel):
    success: bool = True
    message: str

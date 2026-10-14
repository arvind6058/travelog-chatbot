from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logging import logger


class AppException(Exception):
    """Base application exception returning standardized JSON responses."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND", details: Optional[Dict[str, Any]] = None):
        super().__init__(code=code, message=message, status_code=status.HTTP_404_NOT_FOUND, details=details)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Invalid authentication credentials", code: str = "AUTHENTICATION_FAILED", details: Optional[Dict[str, Any]] = None):
        super().__init__(code=code, message=message, status_code=status.HTTP_401_UNAUTHORIZED, details=details)


class PermissionDeniedError(AppException):
    def __init__(self, message: str = "Access denied: insufficient permissions", code: str = "PERMISSION_DENIED", details: Optional[Dict[str, Any]] = None):
        super().__init__(code=code, message=message, status_code=status.HTTP_403_FORBIDDEN, details=details)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation failed", code: str = "VALIDATION_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(code=code, message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)


class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict occurred", code: str = "CONFLICT", details: Optional[Dict[str, Any]] = None):
        super().__init__(code=code, message=message, status_code=status.HTTP_409_CONFLICT, details=details)


class ProviderUnavailableError(AppException):
    def __init__(self, provider_name: str, message: str = "Data unavailable from the configured provider", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="PROVIDER_UNAVAILABLE",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"provider": provider_name, **(details or {})},
        )


def format_error_response(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        payload["error"]["details"] = details
    return payload


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(f"AppException: code={exc.code} message={exc.message} path={request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(code=exc.code, message=exc.message, details=exc.details),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    error_details = [{"loc": err.get("loc"), "msg": err.get("msg"), "type": err.get("type")} for err in errors]
    first_msg = errors[0].get("msg") if errors else "Request validation failed"
    logger.warning(f"Validation error on {request.url.path}: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_error_response(
            code="VALIDATION_ERROR",
            message=f"Invalid request parameters: {first_msg}",
            details={"errors": error_details},
        ),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = f"HTTP_{exc.status_code}"
    message = str(exc.detail) if exc.detail else "HTTP error"
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(code=code, message=message),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled exception on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred.",
        ),
    )

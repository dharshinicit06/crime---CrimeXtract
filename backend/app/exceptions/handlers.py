"""Custom exception classes and FastAPI exception handlers."""

from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from jose import JWTError

from app.logging import get_logger

logger = get_logger(__name__)


# ─── Custom Exceptions ──────────────────────────────────────────


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found", error_code: str = "NOT_FOUND") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
        )


class ConflictException(AppException):
    """Resource conflict (e.g., duplicate entry)."""

    def __init__(self, message: str = "Resource already exists", error_code: str = "CONFLICT") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
        )


class UnauthorizedException(AppException):
    """Authentication failure."""

    def __init__(self, message: str = "Not authenticated", error_code: str = "UNAUTHORIZED") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
        )


class ForbiddenException(AppException):
    """Authorization failure."""

    def __init__(self, message: str = "Permission denied", error_code: str = "FORBIDDEN") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
        )


class BadRequestException(AppException):
    """Bad request."""

    def __init__(self, message: str = "Bad request", error_code: str = "BAD_REQUEST") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
        )


# ─── Exception Handlers ─────────────────────────────────────────


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Handle custom application exceptions."""
        logger.warning(
            "App exception: %s (code=%s)",
            exc.message,
            exc.error_code,
            extra={"path": str(request.url), "status_code": exc.status_code},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "error_code": exc.error_code,
                **({"details": exc.details} if exc.details else {}),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = [
            {
                "loc": list(error.get("loc", [])),
                "msg": error.get("msg", ""),
                "type": error.get("type", ""),
            }
            for error in exc.errors()
        ]
        logger.warning(
            "Validation error: %s",
            errors,
            extra={"path": str(request.url)},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": errors, "error_code": "VALIDATION_ERROR"},
        )

    @app.exception_handler(JWTError)
    async def jwt_error_handler(request: Request, exc: JWTError) -> JSONResponse:
        """Handle JWT errors."""
        logger.warning("JWT error: %s", str(exc))
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired token", "error_code": "INVALID_TOKEN"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unhandled exceptions."""
        logger.exception("Unhandled exception: %s", str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
        )

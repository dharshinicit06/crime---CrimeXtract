"""FastAPI middleware for automatically auditing API requests."""

import time
from collections.abc import Awaitable, Callable
from typing import Optional

from fastapi import Request, Response
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware

from app.audit_log.models import AuditAction
from app.audit_log.services import AuditLogService
from app.config import settings
from app.core.database import async_session_factory
from app.logging import get_logger

logger = get_logger(__name__)


def _should_skip(path: str) -> bool:
    """Determine whether a request path should be excluded from audit logging."""
    prefix = settings.API_V1_PREFIX

    skip_paths = {
        "/",
        f"{prefix}/health",
        f"{prefix}/version",
        f"{prefix}/docs",
        f"{prefix}/redoc",
        f"{prefix}/openapi.json",
        f"{prefix}/audit-logs/",
        f"{prefix}/audit-logs/stats",
    }

    skip_prefixes = (
        "/docs",
        "/redoc",
        "/openapi.json",
        "/swagger",
        f"{prefix}/docs",
        f"{prefix}/redoc",
        f"{prefix}/openapi.json",
    )

    if path in skip_paths:
        return True

    if any(path.startswith(p) for p in skip_prefixes):
        return True

    return False


def _extract_user_info(
    request: Request,
) -> tuple[Optional[int], Optional[int]]:
    """Extract user information from JWT.

    Returns:
        Tuple of (user_id, role_id).
    """

    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        return None, None

    token = auth_header[7:]

    try:
        from app.auth.jwt import verify_token

        payload = verify_token(token)

        sub = payload.get("sub")
        role_id = payload.get("role_id")

        user_id = int(sub) if sub is not None else None
        role_id = int(role_id) if role_id is not None else None

        return user_id, role_id

    except JWTError:
        return None, None

    except Exception:
        logger.exception("Failed to decode JWT.")
        return None, None


def _map_http_method_to_action(method: str) -> AuditAction:
    mapping = {
        "POST": AuditAction.CREATE,
        "GET": AuditAction.READ,
        "PUT": AuditAction.UPDATE,
        "PATCH": AuditAction.UPDATE,
        "DELETE": AuditAction.DELETE,
    }

    return mapping.get(method.upper(), AuditAction.API_CALL)


def _extract_resource_info(
    path: str,
) -> tuple[Optional[str], Optional[str]]:
    """Extract resource type and ID from URL."""

    cleaned = path

    if cleaned.startswith("/api/v1/"):
        cleaned = cleaned[8:]
    elif cleaned.startswith("/api/"):
        cleaned = cleaned[5:]

    parts = [p for p in cleaned.split("/") if p]

    if not parts:
        return None, None

    resource_type = parts[0]
    resource_id = None

    if len(parts) > 1:
        candidate = parts[1]

        if len(candidate) == 36 and "-" in candidate:
            resource_id = candidate

        elif candidate.isdigit():
            resource_id = candidate

    return resource_type, resource_id


class AuditMiddleware(BaseHTTPMiddleware):
    """Automatically stores audit logs for every API request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:

        path = request.url.path

        if _should_skip(path):
            return await call_next(request)

        start_time = time.perf_counter()

        ip_address = request.client.host if request.client else None

        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()

        user_agent = request.headers.get("User-Agent")
        method = request.method

        user_id, role_id = _extract_user_info(request)

        action = _map_http_method_to_action(method)

        resource_type, resource_id = _extract_resource_info(path)

        status_code = 500
        duration_ms = 0

        try:
            response = await call_next(request)

            status_code = response.status_code

            return response

        finally:

            duration_ms = int(
                (time.perf_counter() - start_time) * 1000
            )

            try:

                async with async_session_factory() as session:

                    service = AuditLogService(session=session)

                    await service.log(
                        action=action,
                        user_id=user_id,
                        user_role=role_id,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        method=method,
                        path=path,
                        status_code=status_code,
                        duration_ms=duration_ms,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        message=f"{method} {path} -> {status_code} ({duration_ms} ms)",
                    )

                    await session.commit()

            except Exception:
                logger.exception("Failed to save audit log.")

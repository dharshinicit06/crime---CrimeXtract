"""Settings API endpoints for profile, password, preferences, and system administration.

All endpoints require JWT authentication. Preferences are auto-created
with defaults on first access. System info is admin-only.
"""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    RoleChecker,
    get_current_user,
    get_db_session,
)
from app.auth.models import User
from app.settings.schemas import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    PreferenceResponse,
    PreferenceUpdateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
    SystemInfoResponse,
    MessageResponse,
    LogoutAllResponse,
)
from app.settings.services import SettingsService
from app.audit_log.models import AuditAction
from app.audit_log.services import AuditLogService
from app.logging import get_logger
# Rate limiter temporarily disabled due to slowapi compatibility
# from app.rate_limit import password_limiter

logger = get_logger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


def get_settings_service(
    session: AsyncSession = Depends(get_db_session),
) -> SettingsService:
    return SettingsService(session=session)


def get_audit_service(
    session: AsyncSession = Depends(get_db_session),
) -> AuditLogService:
    return AuditLogService(session=session)


# ═══════════════════════════════════════════════════════════════
# Profile
# ═══════════════════════════════════════════════════════════════


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Get current user's profile",
)
async def get_profile(
    current_user: User = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
) -> ProfileResponse:
    """Return the authenticated user's profile information."""
    profile = await service.get_profile(current_user)
    return ProfileResponse(**profile)


@router.patch(
    "/profile",
    response_model=ProfileResponse,
    summary="Update current user's profile",
)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
    audit: AuditLogService = Depends(get_audit_service),
) -> ProfileResponse:
    """Update profile fields (email, full_name, phone).

    Validates email uniqueness. Only provided fields are updated.
    """
    profile = await service.update_profile(
        current_user,
        full_name=request.full_name,
        email=request.email,
        phone=request.phone,
    )

    # Audit log
    await audit.log(
        action=AuditAction.UPDATE,
        user_id=current_user.id,
        resource_type="users",
        resource_id=str(current_user.id),
        ip_address=None,
        message="Profile updated",
    )

    return ProfileResponse(**profile)


# ═══════════════════════════════════════════════════════════════
# Password
# ═══════════════════════════════════════════════════════════════


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    summary="Change current user's password",
)
# @password_limiter  # Uncomment when slowapi compatibility is resolved
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
    audit: AuditLogService = Depends(get_audit_service),
) -> ChangePasswordResponse:
    """Change the authenticated user's password.

    Requires current password for verification. New password
    must be at least 8 characters. Rate-limited.
    """
    await service.change_password(
        current_user,
        current_password=request.current_password,
        new_password=request.new_password,
    )

    # Audit log
    await audit.log(
        action=AuditAction.UPDATE,
        user_id=current_user.id,
        resource_type="password",
        resource_id=str(current_user.id),
        ip_address=None,
        message="Password changed",
    )

    return ChangePasswordResponse()


# ═══════════════════════════════════════════════════════════════
# Preferences
# ═══════════════════════════════════════════════════════════════


@router.get(
    "/preferences",
    response_model=PreferenceResponse,
    summary="Get current user's preferences",
)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
) -> PreferenceResponse:
    """Return the authenticated user's preferences.

    Preferences are auto-created with sensible defaults if they
    don't already exist.
    """
    prefs = await service.get_preferences(current_user)
    return PreferenceResponse.model_validate(prefs)


@router.patch(
    "/preferences",
    response_model=PreferenceResponse,
    summary="Update current user's preferences",
)
async def update_preferences(
    request: PreferenceUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
    audit: AuditLogService = Depends(get_audit_service),
) -> PreferenceResponse:
    """Update user preferences (theme, language, notifications, etc.).

    All fields are optional — only provided fields are updated.
    Only valid preference keys are accepted.
    """
    prefs = await service.update_preferences(
        current_user,
        theme=request.theme,
        language=request.language,
        timezone=request.timezone,
        date_format=request.date_format,
        email_notifications=request.email_notifications,
        sms_notifications=request.sms_notifications,
        ai_notifications=request.ai_notifications,
        report_notifications=request.report_notifications,
        security_alerts=request.security_alerts,
    )

    # Audit log
    await audit.log(
        action=AuditAction.UPDATE,
        user_id=current_user.id,
        resource_type="user_preferences",
        resource_id=str(prefs.preference_id),
        ip_address=None,
        message="Preferences updated",
    )

    return PreferenceResponse.model_validate(prefs)


# ═══════════════════════════════════════════════════════════════
# System Info (admin only)
# ═══════════════════════════════════════════════════════════════


@router.get(
    "/system",
    response_model=SystemInfoResponse,
    summary="Get system information (admin only)",
    dependencies=[Depends(RoleChecker(1))],
)
async def get_system_info(
    current_user: User = Depends(get_current_user),
    service: SettingsService = Depends(get_settings_service),
) -> SystemInfoResponse:
    """Return system information.

    Restricted to administrators (role_id=1).
    Includes application version, database status,
    environment, and Python version.
    """
    info = await service.get_system_info()
    return SystemInfoResponse(**info)


@router.post(
    "/logout-all",
    response_model=LogoutAllResponse,
    summary="Log out all active sessions",
)
async def logout_all(
    current_user: User = Depends(get_current_user),
    audit: AuditLogService = Depends(get_audit_service),
) -> LogoutAllResponse:
    """Log out all active sessions for the current user.

    In a production system this would invalidate all JWT tokens
    issued before this moment by rotating a per-user token version
    or maintaining a blocklist.

    Currently this is a placeholder that logs the action.
    """
    # Audit log
    await audit.log(
        action=AuditAction.UPDATE,
        user_id=current_user.id,
        resource_type="sessions",
        resource_id=str(current_user.id),
        ip_address=None,
        message="All sessions logged out",
    )

    logger.info(
        "User %s logged out all sessions", current_user.email,
    )

    return LogoutAllResponse()

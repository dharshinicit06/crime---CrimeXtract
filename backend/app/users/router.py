"""User management API endpoints with role-aware RBAC.

Permissions:
  - Admin (role_id=1): full CRUD, status toggle, password reset
  - Investigator (role_id=2): view own profile only
  - Analyst (role_id=3): view own profile only
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    RoleChecker,
    get_current_user,
    get_db_session,
)
from app.auth.models import User
from app.exceptions.handlers import ForbiddenException
from app.users.schemas import (
    UserCreateRequest,
    UserFilterParams,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
    UserPasswordResetRequest,
    UserStatusUpdateRequest,
)
from app.users.services import UserService
from app.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["user-management"])


def get_user_service(
    session: AsyncSession = Depends(get_db_session),
) -> UserService:
    return UserService(session=session)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    dependencies=[Depends(RoleChecker(1))],
)
async def create_user(
    request: UserCreateRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Create a user. Admin only (role_id=1)."""
    user = await service.create(
        actor=current_user,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        phone=request.phone,
        role_id=request.role_id,
        is_active=request.is_active,
    )
    return UserResponse.model_validate(user)


@router.get(
    "/",
    response_model=UserListResponse,
    summary="List users (admin only)",
    dependencies=[Depends(RoleChecker(1))],
)
async def list_users(
    filters: UserFilterParams = Depends(),
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserListResponse:
    """List users with search, role/active filters, and sorting. Admin only."""
    return await service.list_users(
        actor=current_user,
        page=filters.page,
        page_size=filters.page_size,
        search=filters.search,
        role_id=filters.role_id,
        is_active=filters.is_active,
        sort_by=filters.sort_by,
        sort_order=filters.sort_order,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user by ID",
)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Get a user profile.

    Admin (role_id=1) can view any profile.
    Non-admin users can only view their own profile.
    """
    # Non-admin users can only see themselves
    if current_user.role_id != 1 and current_user.id != user_id:
        raise ForbiddenException(
            message="You can only view your own profile",
            error_code="ACCESS_DENIED",
        )

    user = await service.get(user_id)
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user",
    dependencies=[Depends(RoleChecker(1))],
)
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Update a user's fields. Admin only."""
    user = await service.update(
        actor=current_user,
        user_id=user_id,
        email=request.email,
        full_name=request.full_name,
        phone=request.phone,
        role_id=request.role_id,
        is_active=request.is_active,
    )
    return UserResponse.model_validate(user)


@router.post(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Activate or deactivate a user (soft toggle)",
    dependencies=[Depends(RoleChecker(1))],
)
async def toggle_user_status(
    user_id: int,
    request: UserStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Activate or deactivate a user account. Admin only. Soft delete (is_active=0)."""
    user = await service.update(
        actor=current_user,
        user_id=user_id,
        is_active=request.is_active,
    )
    return UserResponse.model_validate(user)


@router.post(
    "/{user_id}/reset-password",
    response_model=UserResponse,
    summary="Reset a user's password",
    dependencies=[Depends(RoleChecker(1))],
)
async def reset_user_password(
    user_id: int,
    request: UserPasswordResetRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Reset a user's password. Admin only."""
    user = await service.reset_password(
        actor=current_user,
        user_id=user_id,
        new_password=request.new_password,
    )
    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    response_model=UserResponse,
    summary="Soft-delete a user (deactivate)",
    dependencies=[Depends(RoleChecker(1))],
)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Soft-delete a user by setting is_active=False. Admin only."""
    user = await service.soft_delete(actor=current_user, user_id=user_id)
    return UserResponse.model_validate(user)

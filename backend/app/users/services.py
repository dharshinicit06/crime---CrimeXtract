"""User management business logic with search, filter, pagination, and soft-delete."""

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.auth.hashing import hash_password
from app.auth.models import User
from app.auth.role_models import Role
from app.exceptions.handlers import (
    ConflictException,
    NotFoundException,
    UnauthorizedException,
)
from app.logging import get_logger

logger = get_logger(__name__)


# Role name mapping (matching the roles table)
ROLE_NAMES_MAP = {1: "Admin", 2: "Investigator", 3: "Analyst"}


class UserService:
    """Handles user CRUD with admin-level access controls."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ─── Helpers ────────────────────────────────────────────────

    async def _get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def _validate_role_promotion(
        self, actor: User, target_role_id: int
    ) -> None:
        """Only role_id=1 (Admin) can assign role_id=1."""
        if target_role_id == 1 and actor.role_id != 1:
            raise UnauthorizedException(
                message="Only admins can assign the Admin role",
                error_code="ROLE_PROMOTION_DENIED",
            )

    def _enrich_with_role_name(self, user: User) -> dict:
        """Add role_name to a user dict/object for response."""
        user_dict = {
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "role_id": user.role_id or 3,
            "role_name": ROLE_NAMES_MAP.get(user.role_id, "Officer"),
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
        return user_dict

    # ─── Build search / filter query ────────────────────────────

    def _build_list_query(
        self,
        search: Optional[str] = None,
        role_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> tuple:
        """Build a select query with optional search and filters.

        Returns (filtered_query, count_query).
        """
        base = select(User)

        if search:
            like_pattern = f"%{search}%"
            base = base.where(
                or_(
                    User.email.ilike(like_pattern),
                    User.full_name.ilike(like_pattern),
                )
            )

        if role_id is not None:
            base = base.where(User.role_id == role_id)

        if is_active is not None:
            base = base.where(User.is_active == is_active)

        count_q = select(func.count()).select_from(base.subquery())
        return base, count_q

    # ─── CRUD ───────────────────────────────────────────────────

    async def create(
        self, actor: User, **kwargs
    ) -> User:
        """Create a new user with admin-level validation."""
        email = kwargs.get("email", "")

        # Check uniqueness
        if await self._get_by_email(email):
            raise ConflictException(
                message=f"Email '{email}' is already registered",
                error_code="EMAIL_TAKEN",
            )

        target_role_id = kwargs.get("role_id", 3)
        await self._validate_role_promotion(actor, target_role_id)

        password = kwargs.pop("password", "")
        hashed = hash_password(password) if password else hash_password("Changeme1!")

        user = User(
            email=email,
            password_hash=hashed,
            full_name=kwargs.get("full_name", ""),
            phone=kwargs.get("phone"),
            role_id=target_role_id,
            is_active=kwargs.get("is_active", True),
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        logger.info(
            "Admin %s created user %s (role_id=%s)",
            actor.email, user.email, user.role_id,
        )
        return user

    async def get(self, user_id: int) -> User:
        """Get a user by ID."""
        user = await self.session.get(User, user_id)
        if not user:
            raise NotFoundException(
                message=f"User '{user_id}' not found",
                error_code="USER_NOT_FOUND",
            )
        return user

    async def list_users(
        self,
        actor: User,
        *,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        role_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> dict:
        """List users with pagination, filtering, and search."""
        query, count_query = self._build_list_query(
            search=search, role_id=role_id, is_active=is_active
        )

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Sorting
        allowed_sorts = {"email", "full_name", "role_id", "is_active", "created_at", "updated_at"}
        if sort_by and sort_by in allowed_sorts:
            sort_col = getattr(User, sort_by)
            query = query.order_by(
                sort_col.desc() if sort_order == "desc" else sort_col.asc()
            )
        else:
            query = query.order_by(User.created_at.desc())

        # Pagination
        from app.utils.pagination import paginate
        offset, limit, page_info = paginate(total, page, page_size)
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        users = list(result.scalars().all())

        logger.info(
            "User %s listed users (page=%d, total=%d)",
            actor.email, page, total,
        )

        # Enrich with role_name
        items = [self._enrich_with_role_name(u) for u in users]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": page_info.total_pages,
        }

    async def update(self, actor: User, user_id: int, **kwargs) -> User:
        """Update a user's profile fields."""
        user = await self.get(user_id)

        # Role promotion check
        if "role_id" in kwargs and kwargs["role_id"] is not None:
            await self._validate_role_promotion(actor, kwargs["role_id"])

        # Email uniqueness check
        new_email = kwargs.get("email")
        if new_email and new_email != user.email:
            existing = await self._get_by_email(new_email)
            if existing:
                raise ConflictException(
                    message=f"Email '{new_email}' is already taken",
                    error_code="EMAIL_TAKEN",
                )

        updatable = {"email", "full_name", "phone", "role_id", "is_active"}
        for key, value in kwargs.items():
            if key in updatable and value is not None:
                setattr(user, key, value)

        await self.session.flush()
        await self.session.refresh(user)

        logger.info(
            "Admin %s updated user %s", actor.email, user.email,
        )
        return user

    async def soft_delete(self, actor: User, user_id: int) -> User:
        """Soft-delete a user by setting is_active=False."""
        user = await self.get(user_id)

        if user.id == actor.id:
            raise UnauthorizedException(
                message="You cannot deactivate your own account",
                error_code="SELF_DEACTIVATION_DENIED",
            )

        user.is_active = False
        await self.session.flush()
        await self.session.refresh(user)

        logger.info(
            "Admin %s deactivated user %s", actor.email, user.email,
        )
        return user

    async def reset_password(self, actor: User, user_id: int, new_password: str) -> User:
        """Reset a user's password."""
        user = await self.get(user_id)
        user.password_hash = hash_password(new_password)
        await self.session.flush()
        await self.session.refresh(user)

        logger.info(
            "Admin %s reset password for user %s", actor.email, user.email,
        )
        return user

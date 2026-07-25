"""Base service with repository injection."""

from typing import Any, Generic, Optional, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base
from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType]):
    """Generic service with common business logic.

    Usage:
        class UserService(BaseService[User]):
            pass

        service = UserService(model=User, session=db_session)
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession) -> None:
        self.repository = BaseRepository(model=model, session=session)
        self.session = session

    async def create(self, **kwargs: Any) -> ModelType:
        """Create a new record with business validation."""
        return await self.repository.create(**kwargs)

    async def get(self, id: str) -> Optional[ModelType]:
        """Get a record by ID."""
        return await self.repository.get(id)

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[dict] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ):
        """Get paginated records."""
        return await self.repository.get_multi(
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def update(self, id: str, **kwargs: Any) -> Optional[ModelType]:
        """Update a record."""
        return await self.repository.update(id, **kwargs)

    async def delete(self, id: str) -> bool:
        """Delete a record."""
        return await self.repository.delete(id)

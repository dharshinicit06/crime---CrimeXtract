"""Base repository with common CRUD operations."""

from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository with async CRUD operations.

    Usage:
        class UserRepository(BaseRepository[User]):
            pass

        repo = UserRepository(model=User, session=db_session)
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def create(self, **kwargs: Any) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get(self, id: str) -> Optional[ModelType]:
        """Get a record by primary key."""
        return await self.session.get(self.model, id)

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> Tuple[List[ModelType], int]:
        """Get paginated records with optional filters."""
        query = select(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Sorting
        if sort_by and hasattr(self.model, sort_by):
            sort_column = getattr(self.model, sort_by)
            query = query.order_by(sort_column.desc() if sort_order == "desc" else sort_column.asc())
        else:
            query = query.order_by(self.model.created_at.desc())  # type: ignore[attr-defined]

        # Pagination
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def update(self, id: str, **kwargs: Any) -> Optional[ModelType]:
        """Update a record by primary key."""
        instance = await self.get(id)
        if not instance:
            return None
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: str) -> bool:
        """Delete a record by primary key. Returns True if deleted."""
        instance = await self.get(id)
        if not instance:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def exists(self, **filters: Any) -> bool:
        """Check if a record matching all filters exists."""
        query = select(self.model).limit(1)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

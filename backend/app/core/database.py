"""Database engine, session factory, and session lifecycle management.

NOTE: The single SQLAlchemy DeclarativeBase is defined in app/models/base.py.
This module only contains engine, session factory, and database utilities.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.logging import get_logger
from app.models.base import Base

logger = get_logger(__name__)

try:
    engine = create_async_engine(
        settings.database_url_async,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=False,
    )
except ModuleNotFoundError as exc:
    # Give a clearer error message if a DB driver is missing (e.g. asyncmy for MySQL)
    missing = str(exc).split("'")[1] if "'" in str(exc) else str(exc)
    raise RuntimeError(
        f"Database driver '{missing}' is not installed.\n"
        "If you are using MySQL, install the async driver (e.g. 'pip install asyncmy')\n"
        "or change your DATABASE_URL to use PostgreSQL (postgresql+asyncpg://...)."
    ) from exc

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def initialize_database() -> None:
    """Create all tables (for testing). In production use Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def dispose_engine() -> None:
    """Dispose of the database engine on shutdown."""
    await engine.dispose()
    logger.info("Database engine disposed")

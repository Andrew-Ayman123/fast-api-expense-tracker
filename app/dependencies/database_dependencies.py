"""Dependency for database connections using SQLAlchemy with async support."""
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.dependencies.settings_dependencies import get_env_settings
from app.exceptions.db_connection_async_support_missing import DBConnectionAsyncSupportMissingError
from app.utils.conditional_cache_util import conditional_lru_cache


@conditional_lru_cache()
def get_database_engine() -> AsyncEngine:
    """Get the database connection instance.

    Returns:
        DatabaseConnection: The database connection instance.

    """
    settings = get_env_settings()

    # Force the use of async support engine for PostgreSQL
    if "postgresql://" in settings.database_url:
        raise DBConnectionAsyncSupportMissingError(
            db_connection=settings.database_url,
            needed_engine="postgresql+asyncpg://",
        )

    return create_async_engine(
        settings.database_url,
        echo=settings.database_logging,
        future=True,
    )


@conditional_lru_cache()
def get_session_maker(engine: Annotated[AsyncEngine, Depends(get_database_engine)]) -> async_sessionmaker[AsyncSession]:
    """Get the session maker instance.

    Returns:
        async_sessionmaker[AsyncSession]: The session maker instance.

    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_database_session(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)],
) -> AsyncGenerator[AsyncSession, None]:
    """Get a database session instance.

    This is typically used as a FastAPI dependency.

    Yields:
        AsyncSession: The database session instance.

    """
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

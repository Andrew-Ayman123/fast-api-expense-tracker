"""Defines the dependency injection setup for the FastAPI application.

It provides functions to retrieve instances of database connections, repositories, and services.
These instances are cached for performance and to ensure that the same instance is reused across requests.
"""

from collections.abc import AsyncGenerator, Callable
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config.environment import Settings
from app.exceptions.db_connection_async_support_missing import DBConnectionAsyncSupportMissingError
from app.repositories.interfaces.user_repository_interface import UserRepositoryInterface
from app.repositories.user_pg_repository_impl import UserPGRepository
from app.services.jwt_service import JWTService
from app.services.user_service import UserService


def conditional_lru_cache() -> Callable:
    """Apply LRU cache conditionally based on the environment."""

    def decorator(func: Callable) -> Callable:
        # No caching in testing mode because shared loopback in engine cause errors
        if Settings().testing:
            return func
        return lru_cache()(func)

    return decorator


@lru_cache
def get_env_settings() -> Settings:
    """Get the application settings instance.

    Returns:
        Settings: The application settings instance with environment variables loaded.

    """
    return Settings()


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

def get_user_repository(session: Annotated[AsyncSession, Depends(get_database_session)]) -> UserRepositoryInterface:
    """Get the User repository instance.

    Args:
        session (AsyncSession, optional): An optional AsyncSession instance.
            If not provided, a new one will be created. Defaults to Depends(get_database_session).


    Returns:
        UserPGRepository: The User repository instance.

    """
    return UserPGRepository(session=session)


def get_user_service(
    user_repository: Annotated[UserRepositoryInterface, Depends(get_user_repository)],
) -> UserService:
    """Get the User service instance.

    Args:
        user_repository (UserRepositoryInterface): The User repository instance.

    Returns:
        UserService: The User service instance.

    """
    return UserService(
        user_repository=user_repository,
    )


# It's ok to cache JWTService because it is stateless and does not hold any mutable state
@lru_cache
def get_jwt_service() -> JWTService:
    """Get the JWT service instance.

    Returns:
        JWTService: The JWT service instance.

    """
    return JWTService(
        secret_key=get_env_settings().jwt_secret_key,
        algorithm=get_env_settings().jwt_algorithm,
        expiration_minutes=get_env_settings().jwt_expiration_minutes,
    )

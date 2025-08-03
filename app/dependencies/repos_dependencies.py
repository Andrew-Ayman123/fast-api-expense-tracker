"""Dependency for repositories, providing access to the User repository."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database_dependencies import get_database_session
from app.repositories.interfaces.user_repository_interface import UserRepositoryInterface
from app.repositories.user_pg_repository_impl import UserPGRepository


def get_user_repository(session: Annotated[AsyncSession, Depends(get_database_session)]) -> UserRepositoryInterface:
    """Get the User repository instance.

    Args:
        session (AsyncSession, optional): An optional AsyncSession instance.
            If not provided, a new one will be created. Defaults to Depends(get_database_session).


    Returns:
        UserPGRepository: The User repository instance.

    """
    return UserPGRepository(session=session)

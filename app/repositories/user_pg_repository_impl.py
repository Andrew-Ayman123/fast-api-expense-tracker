"""PostgreSQL implementation of User repository.

This module provides a PostgreSQL implementation of the UserRepositoryInterface
using SQLAlchemy ORM for database operations with async session.
"""

import uuid

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import UserModel
from app.repositories.interfaces.user_repository_interface import UserRepositoryInterface
from app.utils.logger_util import get_logger


class UserPGRepository(UserRepositoryInterface):
    """PostgreSQL implementation of User repository using SQLAlchemy ORM with async session."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the UserPGRepository with an async session.

        Args:
            session (AsyncSession): An instance of SQLAlchemy AsyncSession for database operations.

        """
        self.session = session

    async def create_user(self, email: str, username: str, password_hash: str) -> UserModel | None:
        """Create a new user in the PostgreSQL database.

        Args:
            email (str): The user's email.
            username (str): The user's username.
            password_hash (str): The user's hashed password.

        Returns:
            UserModel | None: The created user data.

        Raises:
            IntegrityError: If a user with the same email or username already exists.

        """
        get_logger().debug("Creating new user with email: %s", email)

        new_user = UserModel(
            id=uuid.uuid4(),
            email=email,
            username=username,
            password=password_hash,
        )

        self.session.add(new_user)

        await self.session.commit()
        await self.session.refresh(new_user)

        return new_user

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserModel | None:
        """Get user data by ID.

        Args:
            user_id (UUID): The user's UUID.

        Returns:
            UserModel | None: The user data if found, else None.

        """
        query = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> UserModel | None:
        """Get user data by email.

        Args:
            email (str): The user's email.

        Returns:
            UserModel | None: The user data if found, else None.

        """
        query = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_user(self, user_id: uuid.UUID, email: str | None = None, username: str | None = None, password_hash: str | None = None) -> UserModel | None:  # noqa: E501
        """Update user data.

        Args:
            user_id (UUID): The user's UUID.
            email (str, optional): The new email for the user.
            username (str, optional): The new username for the user.
            password_hash (str, optional): The new hashed password for the user.

        Returns:
            UserModel | None: The updated user data if successful, else None.

        """
        query = update(UserModel).where(UserModel.id == user_id).values(
            email=email,
            username=username,
            password=password_hash,
        ).returning(UserModel)

        result = await self.session.execute(query)
        updated_user = result.scalar_one_or_none()

        if updated_user:
            await self.session.commit()
            return updated_user

        get_logger().warning("No user found with ID: %s", user_id)
        return None

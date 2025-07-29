"""User Service Module.

This module defines the UserService class, which provides methods for managing users.
It interacts with the UserRepositoryInterface to perform CRUD operations on users.
"""

import uuid

from sqlalchemy.exc import IntegrityError

from app.exceptions.user_exception import (
    UserAlreadyExistsError,
    UserIDNotFoundError,
    WrongEmailOrPasswordError,
)
from app.models.user_model import UserModel
from app.repositories.user_repository_interface import UserRepositoryInterface
from app.schemas.user_schema import UserCreateRequest, UserLoginRequest
from app.utils.password_hash_util import hash_password, verify_password


class UserService:
    """Service class for managing users."""

    def __init__(self, user_repository: UserRepositoryInterface) -> None:
        """Initialize the UserService with a repository instance.

        Args:
            user_repository (UserRepositoryInterface): An instance of UserRepositoryInterface for database operations.

        """
        self.user_repository = user_repository

    async def create_user(self, user_data: UserCreateRequest) -> UserModel:
        """Create a new user.

        Args:
            user_data (UserCreateRequest): The data for creating a new user.

        Returns:
            UserResponse: The created user data.

        """
        password_hash = hash_password(user_data.password)
        try:
            user = await self.user_repository.create_user(user_data.email, user_data.username, password_hash)
            if not user:
                raise UserAlreadyExistsError(user_data.email)
        except IntegrityError as e:
            raise UserAlreadyExistsError(user_data.email) from e
        else:
            return user

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserModel:
        """Get user by UUID.

        Args:
            user_id (UUID): The user's UUID.

        Returns:
            UserResponse | None: The user data if found, else None.

        """
        user = await self.user_repository.get_user_by_id(user_id)
        if not user:
            raise UserIDNotFoundError(user_id)
        return user

    async def verify_user_exists(self, user_login_request: UserLoginRequest) -> UserModel:
        """Check if a user exists by email and password hash.

        Args:
            user_login_request (UserLoginRequest): The login request containing email and password.

        Returns:
            UserModel: The user data if found.

        """
        user = await self.user_repository.get_user_by_email(user_login_request.email)
        if not user:
            raise WrongEmailOrPasswordError

        if not verify_password(user_login_request.password, user.password):
            raise WrongEmailOrPasswordError

        return user

"""User repository interface module.

This module defines the abstract interface for User repository operations.
"""

import uuid
from abc import ABC, abstractmethod

from app.models.user_model import UserModel


class UserRepositoryInterface(ABC):
    """Abstract base class for user repository operations."""

    @abstractmethod
    async def create_user(self, email: str, username: str, password_hash: str) -> UserModel | None:
        """Create a new user and return the user model."""

    @abstractmethod
    async def get_user_by_id(self, user_id: uuid.UUID) -> UserModel | None:
        """Get user data by ID."""

    @abstractmethod
    async def get_user_by_email(self, email: str) -> UserModel | None:
        """Get user data by email."""

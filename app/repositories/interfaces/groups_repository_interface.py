"""Group repository interface module.

This module defines the abstract interface for Group repository operations.
"""

import uuid
from abc import ABC, abstractmethod

from app.models.group_model import GroupModel


class GroupRepositoryInterface(ABC):
    """Abstract base class for group repository operations."""

    @abstractmethod
    async def create_group(self, name: str, created_by_id: uuid.UUID , description: str) -> GroupModel | None:
        """Create a new group and return the group model."""

    @abstractmethod
    async def get_group_by_id(self, group_id: uuid.UUID) -> GroupModel | None:
        """Get group data by ID."""

    @abstractmethod
    async def get_all_groups(self, user_id: uuid.UUID , page: int , limit:int) -> list[GroupModel]:
        """Retrieve a list of all groups for a user."""

    @abstractmethod
    async def delete_group(self, group_id: uuid.UUID) -> None:
        """Delete a group by its ID."""

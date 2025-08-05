"""Group repository interface module.

This module defines the abstract interface for Group repository operations.
"""

import uuid
from abc import ABC, abstractmethod

from app.models import GroupModel


class GroupRepositoryInterface(ABC):
    """Abstract base class for group repository operations."""

    @abstractmethod
    async def create_group(self, name: str, created_by_id: uuid.UUID, description: str | None) -> GroupModel | None:
        """Create a new group and return the group model."""

    @abstractmethod
    async def get_group_by_id(self, group_id: uuid.UUID) -> GroupModel | None:
        """Get group data by ID."""

    @abstractmethod
    async def get_all_groups(self, user_id: uuid.UUID, offset: int, limit: int) -> list[GroupModel]:
        """Retrieve a list of all groups for a user."""

    @abstractmethod
    async def delete_group(self, group_id: uuid.UUID) -> None:
        """Delete a group by its ID."""

    @abstractmethod
    async def update_group(
        self, group_id: uuid.UUID, name: str, description: str | None = None,
    ) -> GroupModel | None:
        """Update a group by its ID and return the updated group model."""

    @abstractmethod
    async def count_groups(self, user_id: uuid.UUID) -> int:
        """Count the number of groups a user is a member of."""

"""Group member repository interface module.

This module defines the abstract interface for GroupMember repository operations.
"""

import uuid
from abc import ABC, abstractmethod

from app.models.group_members_model import GroupMemberModel


class GroupMemberRepositoryInterface(ABC):
    """Abstract base class for group member repository operations."""

    @abstractmethod
    async def add_member(self, user_id: uuid.UUID, group_id: uuid.UUID) -> GroupMemberModel | None:
        """Add a user as a member to a group."""

    @abstractmethod
    async def get_members_by_group_id(self, group_id: uuid.UUID) -> list[GroupMemberModel]:
        """Retrieve all members in a group."""

    @abstractmethod
    async def remove_member(self, user_id: uuid.UUID, group_id: uuid.UUID) -> None:
        """Remove a user from a group."""

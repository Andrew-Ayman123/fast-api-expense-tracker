"""Group member repository interface module.

This module defines the abstract interface for GroupMember repository operations.
"""

import uuid
from abc import ABC, abstractmethod

from app.models.group_members_model import GroupMemberModel
from app.models.group_members_role_enum import GroupMembersRoleEnum


class GroupMemberRepositoryInterface(ABC):
    """Abstract base class for group member repository operations."""

    @abstractmethod
    async def add_member(self, user_id: uuid.UUID, group_id: uuid.UUID) -> GroupMemberModel | None:
        """Add a user as a member to a group."""

    @abstractmethod
    async def get_members_by_group_id(self, group_id: uuid.UUID, offset: int, limit: int) -> list[GroupMemberModel]:
        """Retrieve all members in a group."""

    @abstractmethod
    async def remove_member(self, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
        """Remove a user from a group."""

    @abstractmethod
    async def update_member_role(
        self, user_id: uuid.UUID, group_id: uuid.UUID, new_role: str,
    ) -> GroupMemberModel | None:
        """Update the role of a member in a group."""

    @abstractmethod
    async def get_user_role_in_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> GroupMembersRoleEnum | None:
        """Get a user's role in a specific group."""

    @abstractmethod
    async def is_user_member_of_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
        """Check if a user is a member of a group."""

    @abstractmethod
    async def count_members_in_group(self, group_id: uuid.UUID) -> int:
        """Count the number of members in a group."""

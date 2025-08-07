"""Group Service Module.

This module defines the GroupService class, which provides methods for managing groups.
It interacts with the GroupRepositoryInterface and GroupMemberRepositoryInterface
to perform CRUD operations on groups and their members.
"""

import uuid
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.exceptions.group_exception import (
    GroupCreationError,
    GroupMemberAddError,
    GroupMemberNotFoundError,
    GroupMemberRemoveError,
    GroupMemberRoleUpdateError,
    GroupNotFoundError,
    GroupOwnerCannotLeaveError,
)
from app.exceptions.user_exception import UserEmailNotFoundError, UserIDNotFoundError, UserNotAuthorizedError
from app.models import GroupMembersRoleEnum, GroupModel, UserModel
from app.repositories.interfaces.groups_members_interface import GroupMemberRepositoryInterface
from app.repositories.interfaces.groups_repository_interface import GroupRepositoryInterface
from app.repositories.interfaces.user_repository_interface import UserRepositoryInterface
from app.schemas.group_schema import (
    GroupCreateRequest,
    GroupMemberAddRequest,
    GroupUpdateRequest,
)


class GroupService:
    """Service class for managing groups and their members."""

    def __init__(
        self,
        group_repository: GroupRepositoryInterface,
        group_member_repository: GroupMemberRepositoryInterface,
        user_repository: UserRepositoryInterface,
    ) -> None:
        """Initialize the GroupService with repository instances."""
        self.group_repository = group_repository
        self.group_member_repository = group_member_repository
        self.user_repository = user_repository

    async def create_group(
        self,
        group_data: GroupCreateRequest,
        created_by_id: uuid.UUID,
        group_id: uuid.UUID | None = None,  # Optional group ID for sync purposes
        created_at: datetime | None = None,  # Optional creation timestamp
    ) -> tuple[GroupModel, int, GroupMembersRoleEnum]:
        """Create a new group and add the creator as an admin."""
        try:
            group = await self.group_repository.create_group(
                name=group_data.name,
                created_by_id=created_by_id,
                description=group_data.description,
                group_id=group_id,  # Use provided ID or generate a new one
                created_at=created_at,  # Use provided timestamp
            )

            if not group:
                raise GroupCreationError

            await self.group_member_repository.add_member(
                user_id=created_by_id,
                group_id=group.id,
                role=GroupMembersRoleEnum.ADMIN,
            )
            # Get member count for the response
            member_count = await self.group_member_repository.count_members_in_group(group.id)

        except IntegrityError as e:
            msg = f"Group with id {group_id} already exists"
            raise GroupCreationError(msg) from e
        else:
            return (group, member_count, GroupMembersRoleEnum.ADMIN)

    async def get_group_by_id(
        self,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[GroupModel, int, GroupMembersRoleEnum]:
        """Get a group by its ID if the user is a member."""
        group = await self.group_repository.get_group_by_id(group_id)
        if not group:
            raise GroupNotFoundError(group_id)

        user_role = await self.get_user_role_in_group(user_id, group_id)
        member_count = await self.group_member_repository.count_members_in_group(group_id)
        return (group, member_count, user_role)

    async def get_user_groups(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[tuple[GroupModel, int, GroupMembersRoleEnum]], int]:
        """Get all groups that a user is a member of with pagination."""
        offset = (page - 1) * limit
        groups = await self.group_repository.get_all_groups(user_id, offset, limit)
        total_groups = await self.group_repository.count_groups(user_id)

        groups_with_role = []
        for group in groups:
            user_role = await self.get_user_role_in_group(user_id, group.id)
            member_count = await self.group_member_repository.count_members_in_group(group.id)
            groups_with_role.append((group, member_count, user_role))

        return (groups_with_role, total_groups)

    async def update_group(
        self,
        group_id: uuid.UUID,
        group_data: GroupUpdateRequest,
        user_id: uuid.UUID,
        updated_at: datetime | None = None,  # Optional update timestamp
    ) -> tuple[GroupModel, int, GroupMembersRoleEnum]:
        """Update a group if the user is an admin."""
        updated_group = await self.group_repository.update_group(
            group_id=group_id,
            name=group_data.name,
            description=group_data.description,
            updated_at=updated_at,  # Use provided timestamp
        )

        if not updated_group:
            raise GroupNotFoundError(group_id)

        member_count = await self.group_member_repository.count_members_in_group(group_id)
        user_role = await self.get_user_role_in_group(user_id, group_id)

        return (updated_group, member_count, user_role)

    async def delete_group(self, group_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a group if only its created by that user."""
        group = await self.group_repository.get_group_by_id(group_id)
        if not group:
            raise GroupNotFoundError(group_id)

        if group.created_by != user_id:
            raise UserNotAuthorizedError(user_id)

        await self.group_repository.delete_group(group_id)

    async def get_group_members(
        self,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[UserModel], list[GroupMembersRoleEnum], int]:
        """Get all members of a group if the user is a member."""
        offset = (page - 1) * limit
        members = await self.group_member_repository.get_members_by_group_id(group_id, offset, limit)
        total_members = await self.group_member_repository.count_members_in_group(group_id)

        member_user_list = await self.user_repository.get_many_users_by_ids([member.user_id for member in members])
        if not member_user_list:
            raise UserIDNotFoundError(members[0].user_id if members else user_id)

        member_user_role_list = [member.role for member in members]
        return (member_user_list, member_user_role_list, total_members)

    async def add_member(
        self,
        group_id: uuid.UUID,
        member_data: GroupMemberAddRequest,
    ) -> tuple[UserModel, GroupMembersRoleEnum]:
        """Add a new member to a group if the requesting user is an admin."""
        user_to_add = await self.user_repository.get_user_by_email(member_data.email)
        if not user_to_add:
            raise UserEmailNotFoundError(member_data.email)

        member = await self.group_member_repository.add_member(
            user_id=user_to_add.id,
            group_id=group_id,
            role=GroupMembersRoleEnum(member_data.role),
        )
        if not member:
            raise GroupMemberAddError(member_data.email, group_id)

        return (user_to_add, member.role)

    async def remove_member(
        self,
        group_id: uuid.UUID,
        member_user_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
    ) -> None:
        """Remove a member from a group if the requesting user is an admin."""
        if requesting_user_id == member_user_id:
            group = await self.group_repository.get_group_by_id(group_id)
            if group and group.created_by == requesting_user_id:
                raise GroupOwnerCannotLeaveError(requesting_user_id, group_id)

        is_removed = await self.group_member_repository.remove_member(member_user_id, group_id)

        if not is_removed:
            raise GroupMemberRemoveError(member_user_id, group_id)

    async def update_member_role(
        self,
        group_id: uuid.UUID,
        member_user_id: uuid.UUID,
        new_role: str,
    ) -> None:
        """Update a member's role if the requesting user is an admin."""
        # deny demote if the user is the group owner
        group = await self.group_repository.get_group_by_id(group_id)
        if not group:
            raise GroupNotFoundError(group_id)
        if group.created_by == member_user_id and new_role != GroupMembersRoleEnum.ADMIN:
            raise GroupMemberRoleUpdateError(member_user_id, group_id, "Owner cannot be demoted")

        updated_member = await self.group_member_repository.update_member_role(
            user_id=member_user_id,
            group_id=group_id,
            role=new_role,
        )
        if not updated_member:
            raise GroupMemberRoleUpdateError(member_user_id, group_id)

    async def is_user_member_of_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
        """Check if a user is a member of a group."""
        return await self.group_member_repository.is_user_member_of_group(user_id, group_id)

    async def is_user_admin_of_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
        """Check if a user is an admin of a group."""
        return await self.get_user_role_in_group(user_id, group_id) == GroupMembersRoleEnum.ADMIN

    async def get_user_role_in_group(self, user_id: uuid.UUID, group_id: uuid.UUID) -> GroupMembersRoleEnum:
        """Get a user's role in a specific group."""
        role = await self.group_member_repository.get_user_role_in_group(user_id, group_id)
        if role is None:
            raise GroupMemberNotFoundError(user_id, group_id)

        return role

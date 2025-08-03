"""PostgreSQL implementation of the Group repository interface.

This module provides the implementation of the Group repository interface using SQLAlchemy ORM with async session.
"""

import uuid

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.group_members_model import GroupMemberModel
from app.models.group_members_role_enum import GroupMembersRoleEnum
from app.repositories.interfaces.groups_members_interface import GroupMemberRepositoryInterface
from app.utils.logger_util import get_logger


class GroupMemberPGRepository(GroupMemberRepositoryInterface):
    """PostgreSQL implementation of GroupMember repository using SQLAlchemy ORM with async session."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize the GroupMemberPGRepository with an async session.

        Args:
            db_session (AsyncSession): An instance of SQLAlchemy AsyncSession for database operations.

        Returns:
            None
        Raises:
            None

        """
        self.db = db_session

    async def add_member(self, user_id: uuid.UUID, group_id: uuid.UUID) -> GroupMemberModel | None:
        """Add a user as a member to a group.

        Args:
            user_id (uuid.UUID): The ID of the user to be added.
            group_id (uuid.UUID): The ID of the group to which the user will be added.

        Returns:
            GroupMemberModel | None: The created group member data or None if the operation fails.

        Raises:
            IntegrityError: If a member with the same user_id and group_id already exists.

        """
        new_member = GroupMemberModel(
            id=uuid.uuid4(),
            user_id=user_id,
            group_id=group_id,
        )

        self.db.add(new_member)
        await self.db.commit()
        await self.db.refresh(new_member)

        return new_member

    async def get_members_by_group_id(self, group_id: uuid.UUID , page: int , limit: int) -> list[GroupMemberModel]:  # noqa: D417
        """Retrieve all members in a group.

        Args:
            group_id (uuid.UUID): The ID of the group for which to retrieve members.

        Returns:
            list[GroupMemberModel]: A list of GroupMemberModel instances representing the members of the group.

        Raises:
            None

        """
        result = await self.db.execute(select(GroupMemberModel).where(GroupMemberModel.group_id == group_id).offset(page * limit).limit(limit))  # noqa: E501
        return list(result.scalars().all())

    async def remove_member(self, user_id: uuid.UUID, group_id: uuid.UUID) -> None:
        """Remove a user from a group.

        Args:
            user_id (uuid.UUID): The ID of the user to be removed.
            group_id (uuid.UUID): The ID of the group from which the user will be removed.

        Returns:
            None

        Raises:
            NoResultFound: If no member with the specified user_id and group_id exists.

        """
        query = select(GroupMemberModel).where(
            GroupMemberModel.user_id == user_id,
            GroupMemberModel.group_id == group_id,
        )
        result = await self.db.execute(query)
        member = result.scalar_one_or_none()

        if member:
            await self.db.delete(member)
            await self.db.commit()
        else:
            get_logger().warning("No member found with user_id: %s and group_id: %s", user_id, group_id)

    async def update_member_role(
    self, user_id: uuid.UUID, group_id: uuid.UUID, role: GroupMembersRoleEnum,
) -> GroupMemberModel | None:
        """Update the role of a member in a group.

        Args:
            user_id (uuid.UUID): The ID of the user whose role is to be updated.
            group_id (uuid.UUID): The ID of the group in which the user's role is to be updated.
            role (GroupMembersRoleEnum): The new role to assign to the user.

        Returns:
            GroupMemberModel | None: The updated group member data or None if the operation fails.

        Raises:
            NoResultFound: If no member with the specified user_id and group_id exists.

        """
        stmt = (
            update(GroupMemberModel)
            .where(
                GroupMemberModel.user_id == user_id,
                GroupMemberModel.group_id == group_id,
            )
            .values(role=role)
            .returning(GroupMemberModel)
            .execution_options(synchronize_session="fetch")
        )

        result = await self.db.execute(stmt)
        updated_member = result.scalar_one_or_none()

        if updated_member:
            await self.db.commit()
            return updated_member

        get_logger().warning("No member found with user_id: %s and group_id: %s", user_id, group_id)
        return None

    async def count_members_in_group(self, group_id: uuid.UUID) -> int:
        """Count the number of members in a group.

        Args:
            group_id (uuid.UUID): The ID of the group for which to count members.

        Returns:
            int: The number of members in the specified group.

        Raises:
            None

        """
        result = await self.db.execute(
            select(func.count(GroupMemberModel.id)).where(GroupMemberModel.group_id == group_id),
        )
        return result.scalar_one_or_none() or 0

"""PostgreSQL implementation of Group repository.

This module provides a PostgreSQL implementation of the GroupRepositoryInterface
using SQLAlchemy ORM for database operations with async session.
"""

import uuid

from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import GroupModel
from app.models.group_members_model import GroupMemberModel
from app.repositories.interfaces.groups_repository_interface import GroupRepositoryInterface
from app.utils.logger_util import get_logger


class GroupPGRepository(GroupRepositoryInterface):
    """PostgreSQL implementation of Group repository using SQLAlchemy ORM with async session."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the GroupPGRepository with an async session.

        Args:
            session (AsyncSession): An instance of SQLAlchemy AsyncSession for database operations.

        """
        self.session = session

    async def create_group(self, name: str, created_by_id: uuid.UUID, description: str | None) -> GroupModel | None:
        """Create a new group and return the group model.

        Args:
            name (str): The name of the group.
            created_by_id (uuid.UUID): The ID of the user who created the group.
            description (str): A description of the group.

        Returns:
            GroupModel | None: The created group data.

        Raises:
            IntegrityError: If a group with the same name already exists.

        """
        get_logger().debug("Creating group with name: %s", name)

        new_group = GroupModel(
            id=uuid.uuid4(),
            name=name,
            created_by=created_by_id,
            description=description,
        )

        self.session.add(new_group)
        await self.session.commit()
        await self.session.refresh(new_group)

        return new_group

    async def get_group_by_id(self, group_id: uuid.UUID) -> GroupModel | None:
        """Get group data by ID.

        Args:
            group_id (uuid.UUID): The ID of the group to retrieve.

        Returns:
            GroupModel | None: The group data if found, otherwise None.

        Raises:
            NoResultFound: If no group with the given ID exists.

        """
        query = select(GroupModel).where(GroupModel.id == group_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_groups(self, user_id: uuid.UUID, offset: int, limit: int) -> list[GroupModel]:  # noqa: D417
        """Retrieve a list of all groups for a user.

        This includes groups created by the user and groups where the user is a member.

        Args:
            user_id (uuid.UUID): The ID of the user whose groups to retrieve.

        Returns:
            list[GroupModel]: A list of GroupModel instances associated with the user.

        Raises:
            NoResultFound: If no groups are found for the user.

        """
        # Query to get groups where user is creator OR a member
        query = (
            select(GroupModel)
            .outerjoin(GroupMemberModel, GroupModel.id == GroupMemberModel.group_id)
            .where(
                or_(
                    GroupModel.created_by == user_id,
                    GroupMemberModel.user_id == user_id,
                ),
            )
            .distinct()
            .offset(offset)
            .limit(limit)
        )

        get_logger().debug("Retrieving groups for user ID: %s, offset: %s, limit: %s", user_id, offset, limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_group(self, group_id: uuid.UUID) -> None:
        """Delete a group by its ID.

        Args:
            group_id (uuid.UUID): The ID of the group to delete.

        Returns:
            None: If the group was successfully deleted.

        Raises:
            NoResultFound: If no group with the given ID exists.

        """
        query = select(GroupModel).where(GroupModel.id == group_id)
        result = await self.session.execute(query)
        group = result.scalar_one_or_none()

        if group:
            await self.session.delete(group)
            await self.session.commit()
            get_logger().debug("Group with ID %s deleted successfully", group_id)

    async def count_groups(self, user_id: uuid.UUID) -> int:
        """Count the number of groups for a user.

        This includes groups created by the user and groups where the user is a member.

        Args:
            user_id (uuid.UUID): The ID of the user whose groups to count.

        Returns:
            int: The number of groups associated with the user.

        """
        query = (
            select(func.count(func.distinct(GroupModel.id)))
            .select_from(GroupModel)
            .outerjoin(GroupMemberModel, GroupModel.id == GroupMemberModel.group_id)
            .where(
                or_(
                    GroupModel.created_by == user_id,
                    GroupMemberModel.user_id == user_id,
                ),
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one() or 0

    async def update_group(self, group_id: uuid.UUID, name: str, description: str | None = None) -> GroupModel | None:
        """Update a group's name and description.

        Args:
            group_id (uuid.UUID): The ID of the group to update.
            name (str): The new name for the group.
            description (str): The new description for the group.

        Returns:
            GroupModel | None: The updated group data if successful, otherwise None.

        Raises:
            NoResultFound: If no group with the given ID exists.

        """
        query = select(GroupModel).where(GroupModel.id == group_id)
        result = await self.session.execute(query)
        group = result.scalar_one_or_none()

        if group:
            group.name = name
            group.description = description
            await self.session.commit()
            await self.session.refresh(group)
            return group

        get_logger().warning("No group found with ID: %s", group_id)
        return None

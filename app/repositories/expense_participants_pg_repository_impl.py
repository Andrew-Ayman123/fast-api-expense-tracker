"""PostgreSQL implementation of the Expense participant repository interface.

This module provides the implementation of the Expense participant repository interface
using SQLAlchemy ORM with async session.
"""

import uuid

from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import ExpenseParticipantModel
from app.models.user_model import UserModel
from app.repositories.interfaces.expense_participants_interface import ExpenseParticipantRepositoryInterface
from app.utils.logger_util import get_logger


class ExpenseParticipantsPGRepository(ExpenseParticipantRepositoryInterface):
    """PostgreSQL implementation of Expense participant repository using SQLAlchemy ORM with async session."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the ExpenseParticipantsPGRepository with an async session.

        Args:
            session (AsyncSession): An instance of SQLAlchemy AsyncSession for database operations.

        Returns:
            None

        """
        self.session = session

    async def add_participant(self, user_id: uuid.UUID, expense_id: uuid.UUID) -> ExpenseParticipantModel:
        """Add a new expense participant.

        Args:
            user_id (uuid.UUID): The ID of the user to be added as a participant.
            expense_id (uuid.UUID): The ID of the expense to add the participant to.

        Returns:
            ExpenseParticipantModel: The added participant data.

        """
        participant = ExpenseParticipantModel(user_id=user_id, expense_id=expense_id)
        self.session.add(participant)
        await self.session.commit()
        await self.session.refresh(participant)
        return participant

    async def remove_participant(self, user_id: uuid.UUID, expense_id: uuid.UUID) -> bool:
        """Remove an expense participant.

        Args:
            user_id (uuid.UUID): The ID of the user to be removed as a participant.
            expense_id (uuid.UUID): The ID of the expense to remove the participant from.

        Returns:
            None

        """
        get_logger().debug("Removing participant %s from expense %s", user_id, expense_id)

        query = delete(ExpenseParticipantModel).where(
            ExpenseParticipantModel.user_id == user_id,
            ExpenseParticipantModel.expense_id == expense_id,
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0

    async def list_participants(self, expense_id: uuid.UUID) -> list[UserModel]:
        """List all participants for a specific expense.

        Args:
            expense_id (uuid.UUID): The ID of the expense to list participants for.
            offset (int): The offset for pagination.
            limit (int): The number of participants per page.

        Returns:
            list[UserModel]: A list of participants for the specified expense.

        """
        get_logger().debug("Listing participants for expense ID: %s", expense_id)

        query = select(UserModel).join(ExpenseParticipantModel).where(
            ExpenseParticipantModel.expense_id == expense_id,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def is_user_participant(self, expense_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Check if a user is a participant in a specific expense.

        Args:
            expense_id (uuid.UUID): The ID of the expense to check.
            user_id (uuid.UUID): The ID of the user to check.

        Returns:
            bool: True if the user is a participant, False otherwise.

        """
        get_logger().debug("Checking if user %s is a participant in expense %s", user_id, expense_id)

        query = select(ExpenseParticipantModel).where(
            ExpenseParticipantModel.expense_id == expense_id,
            ExpenseParticipantModel.user_id == user_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def count_participants(self, expense_id: uuid.UUID) -> int:
        """Count the number of participants for a specific expense.

        Args:
            expense_id (uuid.UUID): The ID of the expense to count participants for.

        Returns:
            int: The count of participants for the specified expense.

        """
        get_logger().debug("Counting participants for expense ID: %s", expense_id)

        query = select(func.count(ExpenseParticipantModel.id)).where(
            ExpenseParticipantModel.id == expense_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one()

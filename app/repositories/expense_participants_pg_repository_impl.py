"""PostgreSQL implementation of the Expense participant repository interface.

This module provides the implementation of the Expense participant repository interface
using SQLAlchemy ORM with async session.
"""

import uuid

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.expense_participants_model import ExpenseParticipantModel
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

    async def add_participant(self, participant: ExpenseParticipantModel) -> ExpenseParticipantModel:
        """Add a new expense participant.

        Args:
            participant (ExpenseParticipantModel): The participant to be added.

        Returns:
            ExpenseParticipantModel: The added participant data.

        """
        get_logger().debug("Adding expense participant with ID: %s", participant.id)

        self.session.add(participant)
        await self.session.commit()
        await self.session.refresh(participant)

        return participant

    async def remove_participant(self, participant_id: uuid.UUID) -> None:
        """Remove an expense participant.

        Args:
            participant_id (uuid.UUID): The ID of the participant to be removed.

        Returns:
            None

        """
        get_logger().debug("Removing expense participant with ID: %s", participant_id)

        query = update(ExpenseParticipantModel).where(ExpenseParticipantModel.id == participant_id).values(
            is_active=False,
        )
        await self.session.execute(query)
        await self.session.commit()

    async def get_participant(self, participant_id: uuid.UUID) -> ExpenseParticipantModel | None:
        """Get an expense participant by ID.

        Args:
            participant_id (uuid.UUID): The ID of the participant to retrieve.

        Returns:
            ExpenseParticipantModel: The retrieved participant data.

        """
        get_logger().debug("Getting expense participant with ID: %s", participant_id)

        query = select(ExpenseParticipantModel).where(ExpenseParticipantModel.id == participant_id)
        result = await self.session.execute(query)
        participant = result.scalar_one_or_none()

        if not participant:
            get_logger().warning("Expense participant with ID %s not found", participant_id)
            return None

        return participant

    async def list_participants(self, expense_id: uuid.UUID, page: int, limit: int) -> list[ExpenseParticipantModel]:
        """List all participants for a specific expense.

        Args:
            expense_id (uuid.UUID): The ID of the expense to list participants for.
            page (int): The page number for pagination.
            limit (int): The number of participants per page.

        Returns:
            list[ExpenseParticipantModel]: A list of participants for the specified expense.

        """
        get_logger().debug("Listing participants for expense ID: %s, page: %s, limit: %s", expense_id, page, limit)

        query = select(ExpenseParticipantModel).where(
            ExpenseParticipantModel.id == expense_id,
        ).offset(page * limit).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
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

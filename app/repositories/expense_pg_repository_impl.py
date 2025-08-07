"""PostgreSQL implementation of the Expense repository interface.

This module provides the implementation of the Expense repository interface
using SQLAlchemy ORM with async session.
"""

import uuid
from datetime import date

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import ExpenseCategoryEnum, ExpenseModel
from app.models.expense_participants_model import ExpenseParticipantModel
from app.repositories.interfaces.expense_repository_interface import ExpenseRepositoryInterface
from app.utils.logger_util import get_logger


class ExpensePGRepository(ExpenseRepositoryInterface):
    """PostgreSQL implementation of Expense repository using SQLAlchemy ORM with async session."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the ExpensePGRepository with an async session.

        Args:
            session (AsyncSession): An instance of SQLAlchemy AsyncSession for database operations.

        """
        self.session = session

    async def create_expense(  # noqa: PLR0913
        self,
        title: str,
        amount: float,
        group_id: uuid.UUID,
        payer_id: uuid.UUID,
        category: ExpenseCategoryEnum,
        expense_date: date,
        expense_id: uuid.UUID | None = None,  # Optional expense ID for sync purposes
    ) -> ExpenseModel | None:
        """Create a new expense for a group.

        Args:
            title (str): The title of the expense.
            amount (float): The amount of the expense.
            group_id (uuid.UUID): The ID of the group to which the expense belongs.
            payer_id (uuid.UUID): The ID of the user who created the expense.
            category (ExpenseCategoryEnum): The category of the expense.
            expense_date (date): The date of the expense.
            expense_id (uuid.UUID | None): Optional ID for the expense, used for sync purposes.


        Returns:
            ExpenseModel | None: The created expense data.

        Raises:
            IntegrityError: If an expense with the same title already exists in the group.

        """
        get_logger().debug("Creating expense with title: %s", title)

        new_expense = ExpenseModel(
            id=expense_id or uuid.uuid4(),  # Use provided ID or generate a new one
            title=title,
            amount=amount,
            group_id=group_id,
            payer_id=payer_id,
            category=category,
            date=expense_date,
        )

        self.session.add(new_expense)
        await self.session.commit()
        await self.session.refresh(new_expense)

        return new_expense

    async def get_expenses_by_group(self, group_id: uuid.UUID, offset: int, limit: int) -> list[ExpenseModel]:  # noqa: D417
        """Retrieve all expenses in a group.

        Args:
            group_id (uuid.UUID): The ID of the group to retrieve expenses for.

        Returns:
            list[ExpenseModel]: A list of expenses in the specified group.

        """
        get_logger().debug("Retrieving expenses for group ID: %s", group_id)

        result = await self.session.execute(
            select(ExpenseModel).where(ExpenseModel.group_id == group_id).offset(offset).limit(limit),
        )
        return list(result.scalars().all())

    async def delete_expense(self, expense_id: uuid.UUID) -> bool:
        """Delete an expense by its ID.

        Args:
            expense_id (uuid.UUID): The ID of the expense to delete.

        Returns:
            None: If the deletion is successful.

        Raises:
            NoResultFound: If no expense with the given ID exists.

        """
        get_logger().debug("Deleting expense with ID: %s", expense_id)

        query = select(ExpenseModel).where(ExpenseModel.id == expense_id)
        result = await self.session.execute(query)
        expense = result.scalar_one_or_none()

        if expense is None:
            return False

        await self.session.delete(expense)
        await self.session.commit()
        get_logger().debug("Expense with ID %s deleted successfully", expense_id)
        return True

    async def get_expense_by_id(self, expense_id: uuid.UUID) -> ExpenseModel | None:
        """Get expense data by ID.

        Args:
            expense_id (uuid.UUID): The ID of the expense to retrieve.

        Returns:
            ExpenseModel | None: The expense data if found, otherwise None.

        """
        query = select(ExpenseModel).where(ExpenseModel.id == expense_id)
        result = await self.session.execute(query)
        get_logger().debug("Retrieving expense with ID: %s", expense_id)
        return result.scalar_one_or_none()

    async def count_expenses_by_group(self, group_id: uuid.UUID) -> int:
        """Count the number of expenses in a group.

        Args:
            group_id (uuid.UUID): The ID of the group to count expenses for.

        Returns:
            int: The number of expenses in the specified group.

        """
        query = select(func.count(ExpenseModel.id)).where(ExpenseModel.group_id == group_id)
        result = await self.session.execute(query)
        count = result.scalar_one_or_none()
        get_logger().debug("Counting expenses for group ID: %s, found: %s", group_id, count)
        return count or 0

    async def update_expense(
        self,
        expense_id: uuid.UUID,
        title: str | None = None,
        amount: float | None = None,
        category: ExpenseCategoryEnum | None = None,
        expense_date: date | None = None,
    ) -> ExpenseModel | None:
        """Update an existing expense.

        Args:
            expense_id (uuid.UUID): The ID of the expense to update.
            title (str): The new title of the expense.
            amount (float): The new amount of the expense.
            category (ExpenseCategoryEnum): The new category of the expense.
            expense_date (date): The new date of the expense.

        Returns:
            ExpenseModel | None: The updated expense data or None if not found.

        """
        get_logger().debug("Updating expense with ID: %s", expense_id)

        stmt = (
            update(ExpenseModel)
            .where(ExpenseModel.id == expense_id)
            .values(title=title, amount=amount, category=category, date=expense_date)
            .returning(ExpenseModel)
            .execution_options(synchronize_session="fetch")
        )

        result = await self.session.execute(stmt)
        updated_expense = result.scalar_one_or_none()

        if updated_expense:
            await self.session.commit()
            return updated_expense

        get_logger().warning("No expense found with ID: %s", expense_id)
        return None

    async def count_expenses_in_group(self, group_id: uuid.UUID) -> int:
        """Count the number of expenses in a group.

        Args:
            group_id (uuid.UUID): The ID of the group to count expenses for.

        Returns:
            int: The number of expenses in the specified group.

        """
        query = select(func.count(ExpenseModel.id)).where(ExpenseModel.group_id == group_id)
        result = await self.session.execute(query)
        count = result.scalar_one_or_none()
        get_logger().debug("Counting expenses for group ID: %s, found: %s", group_id, count)
        return count or 0

    async def get_expenses_for_user_in_group(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
    ) -> list[ExpenseModel]:
        """Get all expenses in a group where the user is either a payer or participant.

        Args:
            user_id (uuid.UUID): The ID of the user.
            group_id (uuid.UUID): The ID of the group.

        Returns:
            list[ExpenseModel]: List of expenses where the user is involved.

        """
        # Query for expenses where user is either payer or participant
        query = (
            select(ExpenseModel)
            .where(ExpenseModel.group_id == group_id)
            .where(
                (ExpenseModel.payer_id == user_id)
                | (
                    ExpenseModel.id.in_(
                        select(ExpenseParticipantModel.expense_id).where(
                            ExpenseParticipantModel.user_id == user_id,
                        ),
                    )
                ),
            )
            .order_by(ExpenseModel.created_at.desc())
        )

        result = await self.session.execute(query)
        expenses = list(result.scalars().all())
        get_logger().debug(
            "Retrieved %s expenses for user ID: %s in group ID: %s",
            len(expenses),
            user_id,
            group_id,
        )
        return expenses

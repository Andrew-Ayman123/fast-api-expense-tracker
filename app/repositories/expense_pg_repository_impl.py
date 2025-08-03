"""PostgreSQL implementation of the Expense repository interface.

This module provides the implementation of the Expense repository interface
using SQLAlchemy ORM with async session.
"""

import uuid

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.expense_category_enum import ExpenseCategoryEnum
from app.models.expense_model import ExpenseModel
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

    async def create_expense(self, title: str, amount: float, group_id: uuid.UUID,
                             created_by: uuid.UUID, category: ExpenseCategoryEnum) -> ExpenseModel | None:
        """Create a new expense for a group.

        Args:
            title (str): The title of the expense.
            amount (float): The amount of the expense.
            group_id (uuid.UUID): The ID of the group to which the expense belongs.
            created_by (uuid.UUID): The ID of the user who created the expense.
            category (ExpenseCategoryEnum): The category of the expense.

        Returns:
            ExpenseModel | None: The created expense data.

        Raises:
            IntegrityError: If an expense with the same title already exists in the group.

        """
        get_logger().debug("Creating expense with title: %s", title)

        new_expense = ExpenseModel(
            id=uuid.uuid4(),
            title=title,
            amount=amount,
            group_id=group_id,
            created_by=created_by,
            category=category,
        )

        self.session.add(new_expense)
        await self.session.commit()
        await self.session.refresh(new_expense)

        return new_expense

    async def get_expenses_by_group(self, group_id: uuid.UUID , page: int , limit: int) -> list[ExpenseModel]:  # noqa: D417
        """Retrieve all expenses in a group.

        Args:
            group_id (uuid.UUID): The ID of the group to retrieve expenses for.

        Returns:
            list[ExpenseModel]: A list of expenses in the specified group.

        """
        get_logger().debug("Retrieving expenses for group ID: %s", group_id)

        result = await self.session.execute(
            select(ExpenseModel).where(ExpenseModel.group_id == group_id).offset(page * limit).limit(limit),

        )
        return list(result.scalars().all())

    async def delete_expense(self, expense_id: uuid.UUID) -> None:
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
            return

        await self.session.delete(expense)
        await self.session.commit()
        get_logger().debug("Expense with ID %s deleted successfully", expense_id)

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
        self, expense_id: uuid.UUID, title: str, amount: float, category: ExpenseCategoryEnum,
    ) -> ExpenseModel | None:
        """Update an existing expense.

        Args:
            expense_id (uuid.UUID): The ID of the expense to update.
            title (str): The new title of the expense.
            amount (float): The new amount of the expense.
            category (ExpenseCategoryEnum): The new category of the expense.

        Returns:
            ExpenseModel | None: The updated expense data or None if not found.

        """
        get_logger().debug("Updating expense with ID: %s", expense_id)

        stmt = (
            update(ExpenseModel)
            .where(ExpenseModel.id == expense_id)
            .values(title=title, amount=amount, category=category)
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

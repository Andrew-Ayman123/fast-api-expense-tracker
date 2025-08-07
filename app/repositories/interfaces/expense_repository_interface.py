"""Expense repository interface module.

This module defines the abstract interface for Expense repository operations.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import date

from app.models import ExpenseCategoryEnum, ExpenseModel


class ExpenseRepositoryInterface(ABC):
    """Abstract base class for expense repository operations."""

    @abstractmethod
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
        """Create a new expense for a group."""

    @abstractmethod
    async def get_expenses_by_group(self, group_id: uuid.UUID, offset: int, limit: int) -> list[ExpenseModel]:
        """Retrieve all expenses in a group."""

    @abstractmethod
    async def get_expense_by_id(self, expense_id: uuid.UUID) -> ExpenseModel | None:
        """Get an expense by its ID."""

    @abstractmethod
    async def delete_expense(self, expense_id: uuid.UUID) -> bool:
        """Delete an expense by its ID."""

    @abstractmethod
    async def update_expense(
        self,
        expense_id: uuid.UUID,
        title: str | None = None,
        amount: float | None = None,
        category: ExpenseCategoryEnum | None = None,
        expense_date: date | None = None,
    ) -> ExpenseModel | None:
        """Update an expense by its ID and return the updated expense model."""

    @abstractmethod
    async def count_expenses_in_group(self, group_id: uuid.UUID) -> int:
        """Count the number of expenses in a group."""

    @abstractmethod
    async def get_expenses_for_user_in_group(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
    ) -> list[ExpenseModel]:
        """Get all expenses in a group where the user is either a payer or participant."""

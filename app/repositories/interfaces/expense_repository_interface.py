"""Expense repository interface module.

This module defines the abstract interface for Expense repository operations.
"""

import uuid
from abc import ABC, abstractmethod

from app.models.expense_category_enum import ExpenseCategoryEnum
from app.models.expense_model import ExpenseModel


class ExpenseRepositoryInterface(ABC):
    """Abstract base class for expense repository operations."""

    @abstractmethod
    async def create_expense(self, title: str, amount: float, group_id: uuid.UUID,
                             created_by: uuid.UUID, category: ExpenseCategoryEnum) -> ExpenseModel | None:
        """Create a new expense for a group."""

    @abstractmethod
    async def get_expenses_by_group(self, group_id: uuid.UUID , page: int , limit: int) -> list[ExpenseModel]:
        """Retrieve all expenses in a group."""

    @abstractmethod
    async def delete_expense(self, expense_id: uuid.UUID) -> None:
        """Delete an expense by its ID."""

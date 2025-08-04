"""Expense participant repository interface module.

This module defines the abstract interface for Expense participant repository operations.
"""
import uuid
from abc import ABC, abstractmethod

from app.models import ExpenseParticipantModel
from app.models.user_model import UserModel


class ExpenseParticipantRepositoryInterface(ABC):
    """Abstract base class for expense participant repository operations."""

    @abstractmethod
    async def add_participant(self, user_id: uuid.UUID, expense_id: uuid.UUID) -> ExpenseParticipantModel:
        """Add a new expense participant."""
        ...

    @abstractmethod
    async def remove_participant(self, user_id: uuid.UUID, expense_id: uuid.UUID) -> bool:
        """Remove an expense participant."""
        ...

    @abstractmethod
    async def list_participants(self, expense_id: uuid.UUID) -> list[UserModel]:
        """List all participants for a specific expense."""
        ...

    @abstractmethod
    async def is_user_participant(self, expense_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Check if a user is a participant in a specific expense."""
        ...

    @abstractmethod
    async def count_participants(self, expense_id: uuid.UUID) -> int:
        """Count the number of participants for a specific expense."""
        ...

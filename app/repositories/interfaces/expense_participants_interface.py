"""Expense participant repository interface module.

This module defines the abstract interface for Expense participant repository operations.
"""
import uuid
from abc import ABC, abstractmethod

from app.models.expense_participants_model import ExpenseParticipantModel


class ExpenseParticipantRepositoryInterface(ABC):
    """Abstract base class for expense participant repository operations."""

    @abstractmethod
    async def add_participant(self, participant: ExpenseParticipantModel) -> ExpenseParticipantModel:
        """Add a new expense participant."""
        ...

    @abstractmethod
    async def remove_participant(self, participant_id: uuid.UUID) -> None:
        """Remove an expense participant."""
        ...

    @abstractmethod
    async def get_participant(self, participant_id: uuid.UUID) -> ExpenseParticipantModel | None:
        """Get an expense participant by ID."""
        ...

    @abstractmethod
    async def list_participants(self, expense_id: uuid.UUID, page: int, limit: int) -> list[ExpenseParticipantModel]:
        """List all participants for a specific expense."""
        ...

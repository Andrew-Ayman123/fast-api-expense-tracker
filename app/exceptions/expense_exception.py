"""Exceptions for expense-related operations.

This module defines custom exceptions for expense operations such as creation, management, and calculations.
These exceptions can be raised by the ExpenseService to handle specific error cases.
"""

import uuid

from fastapi import status

from app.exceptions.application_exception import ApplicationError


class ExpenseCreationError(ApplicationError):
    """Exception raised when expense creation fails."""

    def __init__(self, message: str = "Failed to create expense") -> None:
        """Initialize with a custom message."""
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class ExpenseNotFoundError(ApplicationError):
    """Exception raised when an expense is not found."""

    def __init__(self, expense_id: uuid.UUID) -> None:
        """Initialize with the expense ID that was not found."""
        self.expense_id = expense_id
        message = f"Expense with ID {self.expense_id} not found."
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class ExpenseAccessDeniedError(ApplicationError):
    """Exception raised when a user is not authorized to access an expense."""

    def __init__(self, user_id: uuid.UUID, expense_id: uuid.UUID, action: str = "access") -> None:
        """Initialize with user ID, expense ID, and action."""
        self.user_id = user_id
        self.expense_id = expense_id
        self.action = action
        message = f"User {self.user_id} is not authorized to {self.action} expense {self.expense_id}."
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class ExpenseParticipantNotInGroupError(ApplicationError):
    """Exception raised when an expense participant is not a member of the group."""

    def __init__(self, user_id: uuid.UUID, group_id: uuid.UUID) -> None:
        """Initialize with user ID and group ID."""
        self.user_id = user_id
        self.group_id = group_id
        message = f"User {self.user_id} is not a member of group {self.group_id} and cannot participate in expenses."
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class ExpensePayerNotInGroupError(ApplicationError):
    """Exception raised when an expense payer is not a member of the group."""

    def __init__(self, payer_id: uuid.UUID, group_id: uuid.UUID) -> None:
        """Initialize with payer ID and group ID."""
        self.payer_id = payer_id
        self.group_id = group_id
        message = f"Payer {self.payer_id} is not a member of group {self.group_id}."
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class ExpenseUpdateError(ApplicationError):
    """Exception raised when expense update fails."""

    def __init__(self, expense_id: uuid.UUID, message: str = "Failed to update expense") -> None:
        """Initialize with expense ID and custom message."""
        self.expense_id = expense_id
        formatted_message = f"{message} (Expense ID: {self.expense_id})"
        super().__init__(formatted_message, status_code=status.HTTP_400_BAD_REQUEST)


class ExpenseDeletionError(ApplicationError):
    """Exception raised when expense deletion fails."""

    def __init__(self, expense_id: uuid.UUID, message: str = "Failed to delete expense") -> None:
        """Initialize with expense ID and custom message."""
        self.expense_id = expense_id
        formatted_message = f"{message} (Expense ID: {self.expense_id})"
        super().__init__(formatted_message, status_code=status.HTTP_400_BAD_REQUEST)


class ExpenseCalculationError(ApplicationError):
    """Exception raised when expense calculation fails."""

    def __init__(self, message: str = "Failed to calculate expense balances") -> None:
        """Initialize with a custom message."""
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExpenseInvalidAmountError(ApplicationError):
    """Exception raised when expense amount is invalid."""

    def __init__(self, amount: float) -> None:
        """Initialize with the invalid amount."""
        self.amount = amount
        message = f"Invalid expense amount: {self.amount}. Amount must be positive."
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class ExpenseInvalidParticipantsError(ApplicationError):
    """Exception raised when expense participants list is invalid."""

    def __init__(self, message: str = "Invalid participants list") -> None:
        """Initialize with a custom message."""
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class ExpenseParticipantRetrievalError(ApplicationError):
    """Exception raised when retrieving expense participants fails."""

    def __init__(self, message: str = "Failed to retrieve participant details") -> None:
        """Initialize with a custom message."""
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

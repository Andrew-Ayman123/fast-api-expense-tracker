"""Exceptions for user-related operations.

This module defines custom exceptions for user operations such as creation, retrieval, and authentication.
These exceptions can be raised by the UserService or UserRepository to handle specific error cases.
"""

import uuid

from fastapi import status

from app.exceptions.application_exception import ApplicationError


class WrongEmailOrPasswordError(ApplicationError):
    """Exception raised when the email or password is incorrect."""

    def __init__(self) -> None:
        """Initialize the exception with a default message."""
        super().__init__("Wrong email or password.", status_code=status.HTTP_401_UNAUTHORIZED)


class UserAlreadyExistsError(ApplicationError):
    """Exception raised when a user with the same email already exists."""

    def __init__(self, email: str) -> None:
        """Initialize with the email that already exists."""
        self.email = email
        message = f"User with email {self.email} already exists."
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)


class UserIDNotFoundError(ApplicationError):
    """Exception raised when a user is not found."""

    def __init__(self, user_id: uuid.UUID) -> None:
        """Initialize with the user ID that was not found."""
        self.user_id = user_id
        message = f"User with ID {self.user_id} not found."
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class UserNotAuthorizedError(ApplicationError):
    """Exception raised when a user is not authorized to perform an action."""

    def __init__(self, user_id: uuid.UUID) -> None:
        """Initialize with the user ID that is not authorized."""
        self.user_id = user_id
        message = f"User with ID {self.user_id} is not authorized to perform this action."
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class UserEmailNotFoundError(ApplicationError):
    """Exception raised when a user with a specific email is not found."""

    def __init__(self, email: str) -> None:
        """Initialize with the email that was not found."""
        self.email = email
        message = f"User with email {email} not found"
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)

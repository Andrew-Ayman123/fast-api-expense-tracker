"""Exceptions for user-related operations.

This module defines custom exceptions for user operations such as creation, retrieval, and authentication.
These exceptions can be raised by the UserService or UserRepository to handle specific error cases.
"""

import uuid


class WrongEmailOrPasswordError(Exception):
    """Exception raised when the email or password is incorrect."""

    def __init__(self) -> None:
        """Initialize the exception with a default message."""
        super().__init__("Wrong email or password.")


class UserAlreadyExistsError(Exception):
    """Exception raised when a user with the same email already exists."""

    def __init__(self, email: str) -> None:
        """Initialize with the email that already exists."""
        self.email = email
        super().__init__(f"User with email {self.email} already exists.")


class UserIDNotFoundError(Exception):
    """Exception raised when a user is not found."""

    def __init__(self, user_id: uuid.UUID) -> None:
        """Initialize with the user ID that was not found."""
        self.user_id = user_id
        super().__init__(f"User with ID {self.user_id} not found.")


class UserNotAuthorizedError(Exception):
    """Exception raised when a user is not authorized to perform an action."""

    def __init__(self, user_id: uuid.UUID) -> None:
        """Initialize with the user ID that is not authorized."""
        self.user_id = user_id
        super().__init__(f"User with ID {self.user_id} is not authorized to perform this action.")

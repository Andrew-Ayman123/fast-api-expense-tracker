"""Exceptions for JWT-related operations.

This module defines custom exceptions for JWT operations such as token generation, validation, and decoding.
These exceptions can be raised by the JWTService to handle specific error cases.
"""

from fastapi import status

from app.exceptions.application_exception import ApplicationError


class JWTTokenExpiredError(ApplicationError):
    """Exception raised when a JWT token has expired."""

    def __init__(self, message: str = "Token has expired") -> None:
        """Initialize with a custom message."""
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class JWTTokenInvalidError(ApplicationError):
    """Exception raised when a JWT token is invalid."""

    def __init__(self, message: str = "Invalid token") -> None:
        """Initialize with a custom message."""
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class JWTTokenMissingUserIDError(ApplicationError):
    """Exception raised when a JWT token is missing user_id."""

    def __init__(self, message: str = "user_id not found in token") -> None:
        """Initialize with a custom message."""
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class JWTRefreshTokenInvalidError(ApplicationError):
    """Exception raised when a refresh token is invalid."""

    def __init__(self, message: str = "Invalid refresh token") -> None:
        """Initialize with a custom message."""
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)

"""Exception for missing environment variables."""

from fastapi import status

from app.exceptions.application_exception import ApplicationError


class MissingEnvironmentVariableError(ApplicationError):
    """Exception raised when an expected environment variable is missing."""

    def __init__(self, var_name: str) -> None:
        """Initialize the exception with the name of the missing variable."""
        message = f"Missing required environment variable: {var_name}"
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

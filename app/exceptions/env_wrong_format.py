"""Exception for environment variable format errors.

This exception is raised when an environment variable does not match the expected format.
"""

from fastapi import status

from app.exceptions.application_exception import ApplicationError


class EnvironmentVariableFormatError(ApplicationError):
    """Exception raised for errors in the format of environment variables."""

    def __init__(self, var_name: str, var_value: str, expected_format: str) -> None:
        """Initialize the exception with the name of the variable and expected format."""
        message = (
            f"Environment variable '{var_name}' with value '{var_value}' "
            f"is not in the expected format: {expected_format}"
        )
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

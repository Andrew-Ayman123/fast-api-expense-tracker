"""Exception for environment variable format errors.

This exception is raised when an environment variable does not match the expected format.
"""


class EnvironmentVariableFormatError(Exception):
    """Exception raised for errors in the format of environment variables."""

    def __init__(self, var_name: str, var_value: str, expected_format: str) -> None:
        """Initialize the exception with the name of the variable and expected format."""
        super().__init__(
            f"Environment variable '{var_name}' with value '{var_value}' "
            f"is not in the expected format: {expected_format}",
        )

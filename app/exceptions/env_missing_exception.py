"""Exception for missing environment variables."""


class MissingEnvironmentVariableError(Exception):
    """Exception raised when an expected environment variable is missing."""

    def __init__(self, var_name: str) -> None:
        """Initialize the exception with the name of the missing variable."""
        super().__init__(f"Missing required environment variable: {var_name}")

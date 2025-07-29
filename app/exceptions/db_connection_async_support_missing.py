"""Exception for missing async database connection support."""


class DBConnectionAsyncSupportMissingError(Exception):
    """Exception raised when async database connection support is missing."""

    def __init__(self, db_connection: str, needed_engine: str) -> None:
        """Initialize the exception with a message."""
        message = f"Database connection '{db_connection}' does not support async operations. Needed: {needed_engine}"
        super().__init__(message)

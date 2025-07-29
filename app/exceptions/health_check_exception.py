"""Custom exceptions for health check operations in the application."""


class HealthCheckDatabaseNotHealthyError(Exception):
    """Custom exception for unhealthy database connections."""

    def __init__(self) -> None:
        """Initialize the exception with a custom message."""
        super().__init__("Database connection is not healthy.")

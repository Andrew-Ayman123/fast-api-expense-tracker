"""Utility to create standardized error responses for the API."""
from typing import Any

from app.schemas.error_schema import ErrorData


def create_error_data(message: str, details: dict[str, Any] | None = None) -> ErrorData:
    """Create standardized error response format."""
    if details is None:
        details = {}
    return ErrorData(
        message=message,
        details=details,
    )

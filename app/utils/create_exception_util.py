"""Utility to create standardized error responses for the API."""
from typing import Any

from fastapi import HTTPException

from app.schemas.error_schema import ErrorData


def create_http_exception(
    message: str | Exception,
    status_code: int = 400,
    details: dict[str, Any] | None = None,
) -> HTTPException:
    """Create standardized HTTPException."""
    if details is None:
        details = {}
    return HTTPException(
        status_code=status_code,
        detail=ErrorData(
            message=str(message),
            details=details,
        ).model_dump(),
    )

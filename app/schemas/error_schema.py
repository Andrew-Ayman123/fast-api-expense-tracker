"""Error Schema for FastAPI Application."""

from typing import Any

from pydantic import BaseModel


class ErrorData(BaseModel):
    """Schema for error data."""

    message: str
    details: dict[str, Any] = {}

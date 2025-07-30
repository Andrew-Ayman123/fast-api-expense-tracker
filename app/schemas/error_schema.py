"""Error Schema for FastAPI Application."""

from typing import Any

from pydantic import BaseModel


class ErrorData(BaseModel):
    """Schema for error data."""

    message: str
    details: dict[str, Any] = {}

    def json_serializable(self) -> str:
        """Convert the model to a JSON serializable format."""
        return self.model_dump_json()

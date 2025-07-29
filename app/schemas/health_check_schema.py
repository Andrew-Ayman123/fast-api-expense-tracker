"""Pydantic schemas for request/response serialization."""

from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""

    status: str

    class Config:
        """Configuration for Pydantic model."""

        from_attributes = True

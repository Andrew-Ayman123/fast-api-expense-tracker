"""Pydantic schemas for request/response serialization."""

from pydantic import BaseModel


class HealthCheckData(BaseModel):
    """Schema for health check data."""

    status: str

    class Config:
        """Configuration for Pydantic model."""

        from_attributes = True


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""

    data: HealthCheckData

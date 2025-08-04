"""Sync schema definitions for FastAPI application."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# Sync Operation Schemas
class SyncChangeData(BaseModel):
    """Schema for individual sync change data."""

    type: str = Field(..., pattern="^(create|update|delete)$")
    entity: str = Field(..., pattern="^(expense|group)$")
    entity_id: UUID | None = None  # Required for update/delete operations
    data: dict[str, Any] | None = None  # Required for create/update operations
    timestamp: datetime

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class SyncBulkRequest(BaseModel):
    """Schema for bulk sync request."""

    changes: list[SyncChangeData]


class SyncOperationData(BaseModel):
    """Schema for sync operation response data."""

    operation_id: str


class SyncStatusData(BaseModel):
    """Schema for sync status response data."""

    operation_id: str
    status: str  # "pending", "processing", "completed", "failed"
    created_at: datetime
    completed_at: datetime | None = None
    notifications: list[str]

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


# Complete Response Schemas
class SyncBulkResponse(BaseModel):
    """Schema for bulk sync response."""

    data: SyncOperationData


class SyncStatusResponse(BaseModel):
    """Schema for sync status response."""

    data: SyncStatusData

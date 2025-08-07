"""Sync schema definitions for FastAPI application."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


# Data schemas for sync operations
class SyncExpenseCreateData(BaseModel):
    """Schema for expense creation data."""

    title: str = Field(..., max_length=255)
    amount: float = Field(..., gt=0)
    payer_id: UUID
    category: str = Field(..., pattern="^(Food|Transport|Accommodation|Entertainment|Other)$")
    date: date
    is_payer_included: bool
    participants_id: list[UUID]
    group_id: UUID  # Required for create operations, linking expense to a group


class SyncExpenseUpdateData(BaseModel):
    """Schema for expense update data."""

    title: str = Field(..., max_length=255)
    amount: float = Field(..., gt=0)
    payer_id: UUID
    category: str = Field(..., pattern="^(Food|Transport|Accommodation|Entertainment|Other)$")
    date: date
    is_payer_included: bool
    participants_id: list[UUID]


class SyncGroupCreateData(BaseModel):
    """Schema for group creation data."""

    name: str = Field(..., max_length=200)
    description: str | None = None


class SyncGroupUpdateData(BaseModel):
    """Schema for group update data."""

    name: str = Field(..., max_length=200)
    description: str | None = None


# Sync Operation Schemas
class SyncChangeData(BaseModel):
    """Schema for individual sync change data."""

    type: str = Field(..., pattern="^(create|update|delete)$")
    entity: str = Field(..., pattern="^(expense|group)$")
    entity_id: UUID  # Required for create/update/delete operations
    data: SyncExpenseCreateData | SyncExpenseUpdateData | SyncGroupCreateData | SyncGroupUpdateData | None = (
        None  # Required for create/update operations
    )
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
    completed_at: datetime | None = None  # Optional, only if completed or failed
    notifications: list[str]

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


# Complete Response Schemas
class SyncBulkResponseData(BaseModel):
    """Schema for bulk sync response."""

    operation_id: str

class SyncBulkResponse(BaseModel):
    """Schema for bulk sync response."""

    data: SyncBulkResponseData


class SyncStatusResponse(BaseModel):
    """Schema for sync status response."""

    data: SyncStatusData

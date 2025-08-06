"""Expense schema definitions for FastAPI application."""

from datetime import date, datetime
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, Field


# Participant Schemas
class ExpenseParticipantData(BaseModel):
    """Schema for expense participant data."""

    id: UUID
    username: str
    email: str

    class Config:
        """Pydantic model configuration."""

        from_attributes = True

# Payer Schema
class ExpensePayerData(BaseModel):
    """Schema for expense payer data."""

    id: UUID
    username: str
    email: str

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


# Base Expense Data Schemas
class ExpenseListItemData(BaseModel):
    """Schema for expense list item data."""

    id: UUID
    group_id: UUID
    title: str
    amount: float
    payer: ExpensePayerData
    category: str  = Field(..., pattern="^(Food|Transport|Accommodation|Entertainment|Other)$")
    date: date
    created_at: datetime
    participants: list[ExpenseParticipantData]


    class Config:
        """Pydantic model configuration."""

        from_attributes = True
        json_encoders: ClassVar[dict] = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


class ExpenseDetailData(BaseModel):
    """Schema for detailed expense data."""

    id: UUID
    group_id: UUID
    group_name: str
    title: str
    amount: float
    category: str = Field(..., pattern="^(Food|Transport|Accommodation|Entertainment|Other)$")
    date: date
    created_at: datetime
    updated_at: datetime
    payer: ExpensePayerData
    participants: list[ExpenseParticipantData]

    class Config:
        """Pydantic model configuration."""

        from_attributes = True
        json_encoders: ClassVar[dict] = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


class ExpenseCreateData(BaseModel):
    """Schema for expense creation response data."""

    id: UUID
    group_id: UUID
    title: str
    amount: float
    payer: ExpensePayerData
    category: str  = Field(..., pattern="^(Food|Transport|Accommodation|Entertainment|Other)$")
    date: date
    created_at: datetime
    updated_at: datetime
    participants: list[ExpenseParticipantData]

    class Config:
        """Pydantic model configuration."""

        from_attributes = True
        json_encoders: ClassVar[dict] = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }


# Balance Schema
class UserBalanceData(BaseModel):
    """Schema for user balance data."""

    user_id: UUID
    net_balance: float
    expenses: dict[str, float]  # expense_id -> balance_amount

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


# Pagination Schema
class PaginationData(BaseModel):
    """Schema for pagination information."""

    page: int
    limit: int
    total: int
    pages: int


# Request Schemas
class ExpenseCreateRequest(BaseModel):
    """Schema for creating a new expense."""

    title: str = Field(..., max_length=255)
    amount: float = Field(..., gt=0)
    payer_id: UUID
    category: str = Field(..., pattern="^(Food|Transport|Accommodation|Entertainment|Other)$")
    date: date
    is_payer_included: bool
    participants_id: list[UUID]


class ExpenseUpdateRequest(BaseModel):
    """Schema for updating an expense."""

    title: str = Field(..., max_length=255)
    amount: float = Field(..., gt=0)
    payer_id: UUID
    category: str = Field(..., pattern="^(Food|Transport|Accommodation|Entertainment|Other)$")
    date: date
    is_payer_included: bool
    participants_id: list[UUID]


# Response Data Schemas
class ExpenseCreateResponseData(BaseModel):
    """Schema for expense creation response data."""

    expense: ExpenseCreateData


class ExpenseDetailResponseData(BaseModel):
    """Schema for expense detail response data."""

    expense: ExpenseDetailData


class ExpenseListData(BaseModel):
    """Schema for expense list response data."""

    expenses: list[ExpenseListItemData]
    pagination: PaginationData


class ExpenseUpdateData(BaseModel):
    """Schema for expense update response data."""

    expense: ExpenseCreateData  # Same structure as create


class UserBalanceResponseData(BaseModel):
    """Schema for user balance response data."""

    user_id: UUID
    net_balance: float
    expenses: dict[UUID, float]


# Complete Response Schemas
class ExpenseCreateResponse(BaseModel):
    """Schema for expense creation response."""

    data: ExpenseCreateResponseData


class ExpenseDetailResponse(BaseModel):
    """Schema for expense detail response."""

    data: ExpenseDetailResponseData


class ExpenseListResponse(BaseModel):
    """Schema for expense list response."""

    data: ExpenseListData


class ExpenseUpdateResponse(BaseModel):
    """Schema for expense update response."""

    data: ExpenseUpdateData


class UserBalanceResponse(BaseModel):
    """Schema for user balance response."""

    data: UserBalanceResponseData

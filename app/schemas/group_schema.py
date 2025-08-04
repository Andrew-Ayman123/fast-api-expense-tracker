"""Group schema definitions for FastAPI application."""

from datetime import datetime
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, Field


# Base Group Data Schemas
class GroupData(BaseModel):
    """Schema for basic group data."""

    id: UUID
    name: str
    description: str | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    member_count: int
    user_role: str  = Field(..., pattern="^(Admin|Member)$")

    class Config:
        """Pydantic model configuration."""

        from_attributes = True
        json_encoders: ClassVar[dict] = {datetime: lambda v: v.isoformat()}


# Member Schemas
class GroupMemberData(BaseModel):
    """Schema for group member data."""

    id: UUID
    email: str
    username: str
    role: str  = Field(..., pattern="^(Admin|Member)$")

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class PaginationData(BaseModel):
    """Schema for pagination information."""

    page: int
    limit: int
    total: int
    pages: int


# Request Schemas
class GroupCreateRequest(BaseModel):
    """Schema for creating a new group."""

    name: str = Field(..., max_length=200)
    description: str | None = None


class GroupUpdateRequest(BaseModel):
    """Schema for updating a group."""

    name: str = Field(..., max_length=200)
    description: str | None = None


class GroupMemberAddRequest(BaseModel):
    """Schema for adding a member to a group."""

    email: str
    role: str = Field(..., pattern="^(Admin|Member)$")


class GroupMemberRoleUpdateRequest(BaseModel):
    """Schema for updating a member's role."""

    role: str = Field(..., pattern="^(Admin|Member)$")


# Response Data Schemas
class GroupCreateData(BaseModel):
    """Schema for group creation response data."""

    group: GroupData


class GroupDetailData(BaseModel):
    """Schema for group detail response data."""

    group: GroupData


class GroupListData(BaseModel):
    """Schema for group list response data."""

    groups: list[GroupData]
    pagination: PaginationData


class GroupMembersListData(BaseModel):
    """Schema for group members list response data."""

    members: list[GroupMemberData]
    pagination: PaginationData


class GroupMemberAddData(BaseModel):
    """Schema for group member add response data."""

    member: GroupMemberData


# Complete Response Schemas
class GroupCreateResponse(BaseModel):
    """Schema for group creation response."""

    data: GroupCreateData


class GroupDetailResponse(BaseModel):
    """Schema for group detail response."""

    data: GroupDetailData


class GroupListResponse(BaseModel):
    """Schema for group list response."""

    data: GroupListData


class GroupUpdateResponse(BaseModel):
    """Schema for group update response."""

    data: GroupCreateData  # Same structure as create


class GroupMembersListResponse(BaseModel):
    """Schema for group members list response."""

    data: GroupMembersListData


class GroupMemberAddResponse(BaseModel):
    """Schema for group member add response."""

    data: GroupMemberAddData

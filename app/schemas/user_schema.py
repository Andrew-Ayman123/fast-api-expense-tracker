"""User schema definitions for FastAPI application."""

from datetime import datetime
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel


class UserCreateRequest(BaseModel):
    """Schema for creating a new user."""

    email: str
    username: str
    password: str


class UserLoginRequest(BaseModel):
    """Schema for user login."""

    email: str
    password: str


class UserResponse(BaseModel):
    """Schema for returning user data."""

    id: UUID
    email: str
    username: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic model configuration."""

        from_attributes = True
        json_encoders: ClassVar[dict] = {datetime: lambda v: v.isoformat()}


class UserResponseWithToken(UserResponse):
    """Schema for returning user data with JWT token."""

    token: str

    class Config:
        """Pydantic model configuration."""

        from_attributes = True
        json_encoders: ClassVar[dict] = {datetime: lambda v: v.isoformat()}

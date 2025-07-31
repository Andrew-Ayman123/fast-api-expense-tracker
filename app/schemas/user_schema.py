"""User schema definitions for FastAPI application."""

from datetime import datetime
from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreateRequest(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    username: str
    password: str


class UserLoginRequest(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


class UserData(BaseModel):
    """Schema for user data without tokens."""

    id: UUID
    email: str
    username: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic model configuration."""

        from_attributes = True
        json_encoders: ClassVar[dict] = {datetime: lambda v: v.isoformat()}


class UserWithTokensData(BaseModel):
    """Schema for user data with authentication tokens."""

    user: UserData
    token: str
    refresh_token: str


class TokenRefreshData(BaseModel):
    """Schema for token refresh response data."""

    token: str
    refresh_token: str


class UserProfileData(BaseModel):
    """Schema for user profile data."""

    user: UserData


# Complete Response Schemas
class UserRegisterResponse(BaseModel):
    """Schema for user registration response."""

    data: UserWithTokensData


class UserLoginResponse(BaseModel):
    """Schema for user login response."""

    data: UserWithTokensData


class TokenRefreshResponse(BaseModel):
    """Schema for token refresh response."""

    data: TokenRefreshData


class UserProfileResponse(BaseModel):
    """Schema for user profile response."""

    data: UserProfileData

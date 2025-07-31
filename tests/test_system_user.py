"""System tests for User API endpoints."""

import logging

import pytest
from fastapi import status
from httpx import AsyncClient, Response

from app.models.user_model import UserModel
from app.schemas.user_schema import (
    RefreshTokenRequest,
    UserCreateRequest,
    UserLoginRequest,
)

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("reset_user_data_function")
class TestUserAPI:
    """System tests for user registration, login, profile, and token refresh."""

    async def _register_user(self, client: AsyncClient, user: UserModel) -> Response:
        return await client.post(
            "/users/register",
            json=UserCreateRequest(
                email=user.email,
                username=user.username,
                password=user.password,
            ).model_dump(),
        )

    async def _login_user(self, client: AsyncClient, user: UserModel) -> Response:
        return await client.post(
            "/users/login",
            json=UserLoginRequest(
                email=user.email,
                password=user.password,
            ).model_dump(),
        )

    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient, sample_user_data: UserModel) -> None:
        """Test successful user registration."""
        response = await self._register_user(client, sample_user_data)

        assert response.status_code == status.HTTP_200_OK
        json = response.json()
        assert "token" in json["data"]
        assert "refresh_token" in json["data"]
        assert json["data"]["user"]["email"] == sample_user_data.email

    @pytest.mark.asyncio
    async def test_register_user_conflict(self, client: AsyncClient, sample_user_data: UserModel) -> None:
        """Test registering an already existing user returns conflict."""
        await self._register_user(client, sample_user_data)
        response = await self._register_user(client, sample_user_data)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"]["message"] == "User already exists"

    @pytest.mark.asyncio
    async def test_login_user_success(self, client: AsyncClient, sample_user_data: UserModel) -> None:
        """Test login with correct credentials."""
        await self._register_user(client, sample_user_data)
        response = await self._login_user(client, sample_user_data)

        assert response.status_code == status.HTTP_200_OK
        json = response.json()
        assert "token" in json["data"]
        assert "refresh_token" in json["data"]
        assert json["data"]["user"]["email"] == sample_user_data.email

    @pytest.mark.asyncio
    async def test_login_wrong_credentials(self, client: AsyncClient) -> None:
        """Test login failure with wrong credentials."""
        response = await client.post(
            "/users/login",
            json=UserLoginRequest(email="wrong@example.com", password="badpassword").model_dump(),  # noqa: S106
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Invalid credentials"

    @pytest.mark.asyncio
    async def test_get_profile_success(
        self, client: AsyncClient, auth_token_header: dict, sample_user_data: UserModel,
    ) -> None:
        """Test profile retrieval with valid token."""
        response = await client.get("/users/me", headers=auth_token_header)
        assert response.status_code == status.HTTP_200_OK
        json = response.json()
        assert json["data"]["user"]["email"] == sample_user_data.email

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, client: AsyncClient) -> None:
        """Test profile retrieval without JWT token."""
        response = await client.get("/users/me")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, sample_user_data: UserModel) -> None:
        """Test token refresh with valid refresh token."""
        await self._register_user(client, sample_user_data)
        login_response = await self._login_user(client, sample_user_data)

        refresh_token = login_response.json()["data"]["refresh_token"]

        response = await client.post(
            "/users/refresh",
            json=RefreshTokenRequest(refresh_token=refresh_token).model_dump(),
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert "token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient) -> None:
        """Test refresh token failure with invalid token."""
        response = await client.post(
            "/users/refresh",
            json=RefreshTokenRequest(refresh_token="invalid.token.value").model_dump(),  # noqa: S106
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"]["message"] == "Invalid or expired refresh token"

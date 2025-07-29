"""System tests for User API endpoints."""

import logging

import pytest
from fastapi import status
from httpx import AsyncClient, Response

from app.models.user_model import UserModel
from app.schemas.user_schema import UserCreateRequest, UserLoginRequest

logger = logging.getLogger(__name__)

@pytest.mark.usefixtures("reset_user_data_function")
class TestUserAPI:
    """System tests for user registration, login, and profile endpoints."""

    @pytest.mark.asyncio
    async def test_register_user_conflict(
        self,
        client: AsyncClient,
        sample_user_data: UserModel,
    ) -> None:
        """Test registering a user that already exists returns conflict."""
        sample_user_create_data = UserCreateRequest(
            email=sample_user_data.email,
            username=sample_user_data.username,
            password=sample_user_data.password,
        )
        response: Response = await client.post(
            "/user/register",
            json=sample_user_create_data.model_dump(),
            follow_redirects=False,
        )
        assert response.status_code == status.HTTP_200_OK, "User registration failed on first attempt"
        assert "token" in response.json(), "Token not found in registration response"
        assert response.json()["email"] == sample_user_create_data.email, "Email mismatch in registration response"

        response = await client.post(
            "/user/register",
            json=sample_user_create_data.model_dump(),
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_409_CONFLICT, (
            "Expected conflict status code for duplicate user registration"
        )

    @pytest.mark.asyncio
    async def test_login_user(
        self,
        client: AsyncClient,
        auth_token_header: dict[str, str],  # noqa: ARG002
        sample_user_data: UserModel,
    ) -> None:
        """Test successful login of a registered user."""
        sample_user_login_data = UserLoginRequest(
            email=sample_user_data.email,
            password=sample_user_data.password,
        )
        response: Response = await client.post("/user/login", json=sample_user_login_data.model_dump())

        assert response.status_code == status.HTTP_200_OK
        assert "token" in response.json()

    @pytest.mark.asyncio
    async def test_login_wrong_credentials(self, client: AsyncClient) -> None:
        """Test login failure with incorrect credentials."""
        sample_user_login_data = UserLoginRequest(
            email="wrong_email@example.com",
            password="wrong_password",  # noqa: S106
        )
        response: Response = await client.post("/user/login", json=sample_user_login_data.model_dump())

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Wrong email or password"

    @pytest.mark.asyncio
    async def test_get_profile_success(
        self,
        client: AsyncClient,
        auth_token_header: dict[str, str],
        sample_user_data: UserModel,
    ) -> None:
        """Test successful retrieval of user profile with valid JWT."""
        response: Response = await client.get("/user/profile", headers=auth_token_header)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == sample_user_data.email

    @pytest.mark.asyncio
    async def test_get_profile_unauthorized(self, client: AsyncClient) -> None:
        """Test unauthorized access to profile without token."""
        response: Response = await client.get("/user/profile")

        assert response.status_code == status.HTTP_403_FORBIDDEN

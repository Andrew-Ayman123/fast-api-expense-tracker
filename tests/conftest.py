"""Fixtures for testing FastAPI application with pytest and httpx."""

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import status
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database_dependencies import get_database_engine, get_session_maker
from app.main import app
from app.models import GroupModel, UserModel
from app.schemas.user_schema import UserCreateRequest


@pytest_asyncio.fixture()
async def client_v1() -> AsyncGenerator[AsyncClient, None]:
    """Fixture to create an AsyncClient for testing FastAPI endpoints.

    It deletes all the data from the users table before yielding the client.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver/api/v1") as async_client:
        yield async_client


@pytest_asyncio.fixture()
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fixture for a clean test database session.

    It deletes all the data from the users table before yielding the session.
    Used mainly for repository unit tests.
    """
    session_maker = get_session_maker(get_database_engine())
    async with session_maker() as session:
        yield session


@pytest.fixture
def sample_user_data() -> UserModel:
    """Sample user data for testing."""
    return UserModel(
        id=uuid.uuid4(),
        password="hashed_password_123",  # noqa: S106
        email="testuser@example.com",
        username="Test User",
    )


@pytest.fixture
def sample_group_data() -> GroupModel:
    """Sample group data for testing."""
    return GroupModel(
        id=uuid.uuid4(),
        name="Test Group",
        description="A test group for expense tracking",
        created_by=uuid.uuid4(),  # Will be replaced with actual user ID in tests
    )


@pytest_asyncio.fixture()
async def auth_token_header(client: AsyncClient, sample_user_data: UserModel) -> dict[str, str]:
    """Return the authorization header with the current token.

    It registers a sample user(from the sample_user_data fixture) and returns the token in the header.
    """
    response: Response = await client.post(
        "/users/register",
        json=UserCreateRequest(
            email=sample_user_data.email,
            username=sample_user_data.username,
            password=sample_user_data.password,
        ).model_dump(),
    )
    assert response.status_code == status.HTTP_200_OK
    json_data = response.json()
    assert "data" in json_data
    assert "token" in json_data["data"]
    assert "refresh_token" in json_data["data"]
    assert json_data["data"]["user"]["email"] == sample_user_data.email

    token = json_data["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def reset_user_data_function() -> AsyncGenerator[None, None]:
    """Reset user data in the database for function scope tests."""
    async with get_session_maker(get_database_engine())() as session:
        await session.execute(text("DELETE FROM users"))
        await session.commit()
        yield

"""Fixtures for testing FastAPI application with pytest and httpx."""

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_database_engine, get_session_maker
from app.main import app
from app.models.user_model import UserModel
from app.schemas.user_schema import UserCreateRequest


@pytest_asyncio.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
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


@pytest_asyncio.fixture()
async def auth_token_header(client: AsyncClient, sample_user_data: UserModel) -> dict[str, str]:
    """Return the authorization header with the current token.

    It registers a sample user(from the sample_user_data fixture) and returns the token in the header.
    """
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
    assert response.status_code == 200, "User registration failed"
    assert "token" in response.json(), "Token not found in registration response"
    assert response.json()["email"] == sample_user_create_data.email, "Email mismatch in registration response"

    token = response.json().get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


@pytest_asyncio.fixture(scope="function")
async def reset_user_data_function() -> AsyncGenerator[None, None]:
    """Reset user data in the database for function scope tests."""
    async with get_session_maker(get_database_engine())() as session:
        await session.execute(text("DELETE FROM users"))
        await session.commit()
        yield

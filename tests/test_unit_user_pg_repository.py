"""Unit tests for UserRepositoryInterface.

This module contains unit tests for the UserRepositoryInterface using a concrete
test implementation to verify the expected behavior of all interface methods.
"""

import uuid
from collections.abc import AsyncGenerator
from copy import copy

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.models.user_model import UserModel
from app.repositories.user_pg_repository_impl import UserPGRepository


@pytest.mark.usefixtures("reset_user_data_function")
class TestUserRepository:
    """Test suite for UserPGRepository."""

    @pytest_asyncio.fixture()
    async def user_repo(self, test_db_session: AsyncSession) -> AsyncGenerator[UserPGRepository, None]:
        """Fixture to create a UserPGRepository with test DB session."""
        yield UserPGRepository(session=test_db_session)

    @pytest.mark.asyncio
    async def test_create_user_success(
        self,
        user_repo: UserPGRepository,
        sample_user_data: UserModel,
    ) -> None:
        """Test successful user creation."""
        result = await user_repo.create_user(
            email=sample_user_data.email,
            username=sample_user_data.username,
            password_hash=sample_user_data.password,
        )
        assert result is not None
        assert isinstance(result, UserModel)
        assert result.email == sample_user_data.email
        assert result.username == sample_user_data.username
        assert result.password == sample_user_data.password
        assert isinstance(result.id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self,
        user_repo: UserPGRepository,
        sample_user_data: UserModel,
    ) -> None:
        """Test user creation with duplicate email should fail."""
        first_user = await user_repo.create_user(
            email=sample_user_data.email,
            username=sample_user_data.username,
            password_hash=sample_user_data.password,
        )
        assert first_user is not None

        with pytest.raises(IntegrityError):
            await user_repo.create_user(
                email=sample_user_data.email,
                username=sample_user_data.username,
                password_hash=sample_user_data.password,
            )

        await user_repo.session.rollback()

        result = await user_repo.session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar_one()

        assert count == 1, "There should be only one user in the database after duplicate creation attempt."

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(
        self,
        user_repo: UserPGRepository,
        sample_user_data: UserModel,
    ) -> None:
        """Test successful user retrieval by ID."""
        created_user = await user_repo.create_user(
            email=sample_user_data.email,
            username=sample_user_data.username,
            password_hash=sample_user_data.password,
        )
        assert created_user is not None

        result = await user_repo.get_user_by_id(created_user.id)

        assert result is not None
        assert result.id == created_user.id
        assert result.email == sample_user_data.email
        assert result.username == sample_user_data.username
        assert result.password == sample_user_data.password

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_repo: UserPGRepository) -> None:
        """Test user retrieval by ID when user doesn't exist."""
        non_existent_id = uuid.uuid4()

        result = await user_repo.get_user_by_id(non_existent_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(
        self,
        user_repo: UserPGRepository,
        sample_user_data: UserModel,
    ) -> None:
        """Test successful user retrieval by email."""
        created_user = await user_repo.create_user(
            email=sample_user_data.email,
            username=sample_user_data.username,
            password_hash=sample_user_data.password,
        )
        assert created_user is not None

        result = await user_repo.get_user_by_email(sample_user_data.email)

        assert result is not None
        assert result.id == created_user.id
        assert result.email == sample_user_data.email
        assert result.username == sample_user_data.username
        assert result.password == sample_user_data.password

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_repo: UserPGRepository) -> None:
        """Test user retrieval by email when user doesn't exist."""
        non_existent_email = "nonexistent@example.com"

        result = await user_repo.get_user_by_email(non_existent_email)

        assert result is None

    @pytest.mark.asyncio
    async def test_create_multiple_users(self, user_repo: UserPGRepository) -> None:
        """Test creating multiple users with different data."""
        users_data = [
            UserModel(
                id=uuid.uuid4(),
                email=f"user{i}@example.com",
                username=f"user{i}",
                password=f"hash{i}",
            )
            for i in range(5)
        ]

        created_users = []
        for user_data in users_data:
            user = await user_repo.create_user(
                email=user_data.email,
                username=user_data.username,
                password_hash=user_data.password,
            )
            assert user is not None
            created_users.append(user)

        for i, user in enumerate(created_users):
            retrieved_by_id = await user_repo.get_user_by_id(user.id)
            retrieved_by_email = await user_repo.get_user_by_email(users_data[i].email)

            assert retrieved_by_id is not None
            assert retrieved_by_email is not None
            assert retrieved_by_id.id == retrieved_by_email.id == user.id

    @pytest.mark.asyncio
    async def test_email_case_sensitivity(
        self,
        user_repo: UserPGRepository,
        sample_user_data: UserModel,
    ) -> None:
        """Test email case sensitivity behavior."""
        lower_email = sample_user_data.email.lower()
        user_data = copy(sample_user_data)
        user_data.email = lower_email

        created_user = await user_repo.create_user(
            email=user_data.email,
            username=user_data.username,
            password_hash=user_data.password,
        )
        assert created_user is not None

        upper_email = lower_email.upper()
        result = await user_repo.get_user_by_email(upper_email)

        assert result is None

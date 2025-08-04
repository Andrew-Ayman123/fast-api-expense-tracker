"""System tests for Balance API endpoints."""

import logging
import uuid

import pytest
from fastapi import status
from httpx import AsyncClient

from app.schemas.group_schema import GroupCreateRequest

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("reset_user_data_function")
class TestBalanceAPI:
    """System tests for user balance retrieval."""

    async def _create_group(self, client: AsyncClient, auth_headers: dict, group_name: str = "Test Group") -> str:
        """Create a group and return its ID."""
        response = await client.post(
            "/groups",
            headers=auth_headers,
            json=GroupCreateRequest(
                name=group_name,
                description="Test group for balance testing",
            ).model_dump(),
        )
        assert response.status_code == status.HTTP_200_OK
        return response.json()["data"]["group"]["id"]

    @pytest.mark.asyncio
    async def test_get_user_balance_success(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test successful user balance retrieval."""
        # Create a group first
        group_id = await self._create_group(client, auth_token_header)

        # Get the user ID from the auth token
        user_response = await client.get("/users/profile", headers=auth_token_header)
        user_id = user_response.json()["data"]["user"]["id"]

        response = await client.get(
            f"/groups/{group_id}/members/{user_id}/balance",
            headers=auth_token_header,
        )

        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "data" in json_data
        assert "user_id" in json_data["data"]
        assert "net_balance" in json_data["data"]
        assert "expenses" in json_data["data"]
        assert json_data["data"]["user_id"] == user_id
        assert isinstance(json_data["data"]["net_balance"], (int, float))
        assert isinstance(json_data["data"]["expenses"], dict)

    @pytest.mark.asyncio
    async def test_get_user_balance_unauthorized(self, client: AsyncClient) -> None:
        """Test user balance retrieval without authentication."""
        fake_group_id = str(uuid.uuid4())
        fake_user_id = str(uuid.uuid4())

        response = await client.get(f"/groups/{fake_group_id}/members/{fake_user_id}/balance")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_user_balance_invalid_group(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test user balance retrieval with invalid group ID."""
        fake_group_id = str(uuid.uuid4())
        user_response = await client.get("/users/profile", headers=auth_token_header)
        user_id = user_response.json()["data"]["user"]["id"]

        response = await client.get(
            f"/groups/{fake_group_id}/members/{user_id}/balance",
            headers=auth_token_header,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_user_balance_invalid_user(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test user balance retrieval with invalid user ID."""
        group_id = await self._create_group(client, auth_token_header)
        fake_user_id = str(uuid.uuid4())

        response = await client.get(
            f"/groups/{group_id}/members/{fake_user_id}/balance",
            headers=auth_token_header,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_user_balance_not_group_member(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test user balance retrieval for user not in group."""
        # Create group
        group_id = await self._create_group(client, auth_token_header)

        # Register another user
        other_user_data = {
            "email": "other@example.com",
            "username": "Other User",
            "password": "password123",
        }
        register_response = await client.post(
            "/users/register",
            json=other_user_data,
        )
        assert register_response.status_code == status.HTTP_200_OK
        other_user_id = register_response.json()["data"]["user"]["id"]

        # Try to get balance for user not in group
        response = await client.get(
            f"/groups/{group_id}/members/{other_user_id}/balance",
            headers=auth_token_header,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_user_balance_with_multiple_expenses(  # noqa: PLR0915
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test user balance calculation with multiple expenses and different participants."""
        # Create group
        group_id = await self._create_group(client, auth_token_header)

        # Get the first user (admin) ID
        user_response = await client.get("/users/profile", headers=auth_token_header)
        admin_user_id = user_response.json()["data"]["user"]["id"]

        # Register second user
        user2_data = {
            "email": "user2@example.com",
            "username": "User Two",
            "password": "password123",
        }
        register_response2 = await client.post("/users/register", json=user2_data)
        assert register_response2.status_code == status.HTTP_200_OK
        user2_id = register_response2.json()["data"]["user"]["id"]

        # Register third user
        user3_data = {
            "email": "user3@example.com",
            "username": "User Three",
            "password": "password123",
        }
        register_response3 = await client.post("/users/register", json=user3_data)
        assert register_response3.status_code == status.HTTP_200_OK
        user3_id = register_response3.json()["data"]["user"]["id"]

        # Add second and third users to the group (admin required)
        add_member2_response = await client.post(
            f"/groups/{group_id}/members",
            headers=auth_token_header,
            json={"email": user2_data["email"], "role": "Member"},
        )
        assert add_member2_response.status_code == status.HTTP_200_OK

        add_member3_response = await client.post(
            f"/groups/{group_id}/members",
            headers=auth_token_header,
            json={"email": user3_data["email"], "role": "Member"},
        )
        assert add_member3_response.status_code == status.HTTP_200_OK

        # Create first expense: Admin pays $300, split between all 3 users
        expense1_data = {
            "title": "Restaurant Dinner",
            "amount": 300.0,
            "payer_id": admin_user_id,
            "category": "Food",
            "date": "2024-01-01",
            "is_payer_included": True,
            "participants_id": [admin_user_id, user2_id, user3_id],
        }
        expense1_response = await client.post(
            f"/groups/{group_id}/expenses",
            headers=auth_token_header,
            json=expense1_data,
        )
        assert expense1_response.status_code == status.HTTP_200_OK
        expense1_id = expense1_response.json()["data"]["expense"]["id"]

        # Create second expense: User2 pays $150, split between User2 and User3
        expense2_data = {
            "title": "Coffee Shop",
            "amount": 150.0,
            "payer_id": user2_id,
            "category": "Food",
            "date": "2024-01-02",
            "is_payer_included": True,
            "participants_id": [user2_id, user3_id],
        }
        expense2_response = await client.post(
            f"/groups/{group_id}/expenses",
            headers=auth_token_header,
            json=expense2_data,
        )
        assert expense2_response.status_code == status.HTTP_200_OK
        expense2_id = expense2_response.json()["data"]["expense"]["id"]

        # Create third expense: User3 pays $90, split between all 3 users
        expense3_data = {
            "title": "Transport",
            "amount": 90.0,
            "payer_id": user3_id,
            "category": "Transport",
            "date": "2024-01-03",
            "is_payer_included": True,
            "participants_id": [admin_user_id, user2_id, user3_id],
        }
        expense3_response = await client.post(
            f"/groups/{group_id}/expenses",
            headers=auth_token_header,
            json=expense3_data,
        )
        assert expense3_response.status_code == status.HTTP_200_OK
        expense3_id = expense3_response.json()["data"]["expense"]["id"]

        # Test Admin User balance
        # Admin paid: $300, owes: $100 (expense1) + $30 (expense3) = $130
        # Net balance: $300 - $130 = $170 (Admin should receive $170)
        admin_balance_response = await client.get(
            f"/groups/{group_id}/members/{admin_user_id}/balance",
            headers=auth_token_header,
        )
        assert admin_balance_response.status_code == status.HTTP_200_OK
        admin_balance_data = admin_balance_response.json()["data"]
        assert admin_balance_data["user_id"] == admin_user_id
        assert admin_balance_data["net_balance"] == 170.0
        assert len(admin_balance_data["expenses"]) == 2  # participates in expense1 and expense3
        assert expense1_id in admin_balance_data["expenses"]
        assert expense3_id in admin_balance_data["expenses"]

        # Test User2 balance
        # User2 paid: $150, owes: $100 (expense1) + $30 (expense3) = $130
        # Net balance: $150 - $130 = $20 (User2 should receive $20)
        user2_balance_response = await client.get(
            f"/groups/{group_id}/members/{user2_id}/balance",
            headers=auth_token_header,
        )
        assert user2_balance_response.status_code == status.HTTP_200_OK
        user2_balance_data = user2_balance_response.json()["data"]
        assert user2_balance_data["user_id"] == user2_id
        assert user2_balance_data["net_balance"] == 20.0
        assert len(user2_balance_data["expenses"]) == 3  # participates in all expenses
        assert expense1_id in user2_balance_data["expenses"]
        assert expense2_id in user2_balance_data["expenses"]
        assert expense3_id in user2_balance_data["expenses"]

        # Test User3 balance
        # User3 paid: $90, owes: $100 (expense1) + $75 (expense2) = $175
        # Net balance: $90 - $175 = -$85 (User3 owes $85)
        user3_balance_response = await client.get(
            f"/groups/{group_id}/members/{user3_id}/balance",
            headers=auth_token_header,
        )
        assert user3_balance_response.status_code == status.HTTP_200_OK
        user3_balance_data = user3_balance_response.json()["data"]
        assert user3_balance_data["user_id"] == user3_id
        assert user3_balance_data["net_balance"] == -85.0
        assert len(user3_balance_data["expenses"]) == 3  # participates in all expenses
        assert expense1_id in user3_balance_data["expenses"]
        assert expense2_id in user3_balance_data["expenses"]
        assert expense3_id in user3_balance_data["expenses"]

        # Verify that the balances sum to zero (total paid = total owed)
        total_balance = (
            admin_balance_data["net_balance"] + user2_balance_data["net_balance"] + user3_balance_data["net_balance"]
        )
        assert abs(total_balance) < 0.01  # Allow for small floating point differences

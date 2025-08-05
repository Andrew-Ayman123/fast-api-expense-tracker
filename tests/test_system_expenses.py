"""System tests for Expense API endpoints."""

import json
import logging
import uuid

import pytest
from fastapi import status
from httpx import AsyncClient, Response

from app.schemas.group_schema import GroupCreateRequest

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("reset_user_data_function")
class TestExpenseAPI:
    """System tests for expense creation, listing, detail, update, and deletion."""

    async def _create_group(self, client: AsyncClient, auth_headers: dict, group_name: str = "Test Group") -> str:
        """Create a group and return its ID."""
        response = await client.post(
            "/groups",
            headers=auth_headers,
            json=GroupCreateRequest(
                name=group_name,
                description="Test group for expenses",
            ).model_dump(),
        )
        assert response.status_code == status.HTTP_200_OK
        return response.json()["data"]["group"]["id"]

    async def _create_expense(
        self,
        client: AsyncClient,
        auth_headers: dict,
        group_id: str,
        expense_data: dict,
    ) -> Response:
        """Create an expense using the API."""
        return await client.post(
            f"/groups/{group_id}/expenses",
            headers=auth_headers,
            json=expense_data,
        )

    async def _update_expense(
        self,
        client: AsyncClient,
        auth_headers: dict,
        group_id: str,
        expense_id: str,
        expense_data: dict,
    ) -> Response:
        """Update an expense using the API."""
        return await client.put(
            f"/groups/{group_id}/expenses/{expense_id}",
            headers=auth_headers,
            json=expense_data,
        )

    @pytest.mark.asyncio
    async def test_create_expense_success(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test successful expense creation."""
        # Create a group first
        group_id = await self._create_group(client, auth_token_header)

        # Get the user ID from the auth token
        user_response = await client.get("/users/me", headers=auth_token_header)
        user_id = user_response.json()["data"]["user"]["id"]

        expense_data = {
            "title": "Dinner at Restaurant",
            "amount": 150.50,
            "payer_id": user_id,
            "category": "Food",
            "date": "2024-01-01",
            "is_payer_included": True,
            "participants_id": [user_id],
        }

        response = await self._create_expense(client, auth_token_header, group_id, expense_data)

        assert response.status_code == status.HTTP_200_OK, response.json()
        json_data = response.json()
        assert "data" in json_data
        assert "expense" in json_data["data"]
        expense = json_data["data"]["expense"]
        assert expense["title"] == expense_data["title"]
        assert expense["amount"] == expense_data["amount"]
        assert expense["category"] == expense_data["category"]
        assert "id" in expense
        assert "created_at" in expense
        assert "updated_at" in expense
        assert len(expense["participants"]) == 1

    @pytest.mark.asyncio
    async def test_create_expense_unauthorized(self, client: AsyncClient) -> None:
        """Test expense creation without authentication."""
        fake_group_id = str(uuid.uuid4())
        fake_user_id = str(uuid.uuid4())

        expense_data = {
            "title": "Test Expense",
            "amount": 100.0,
            "payer_id": fake_user_id,
            "category": "Food",
            "date": "2024-01-01",
            "is_payer_included": True,
            "participants_id": [fake_user_id],
        }

        response = await client.post(f"/groups/{fake_group_id}/expenses", json=expense_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_create_expense_invalid_group(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test expense creation with invalid group ID."""
        fake_group_id = str(uuid.uuid4())
        user_response = await client.get("/users/me", headers=auth_token_header)
        user_id = user_response.json()["data"]["user"]["id"]

        expense_data = {
            "title": "Test Expense",
            "amount": 100.0,
            "payer_id": user_id,
            "category": "Food",
            "date": "2024-01-01",
            "is_payer_included": True,
            "participants_id": [user_id],
        }

        response = await self._create_expense(client, auth_token_header, fake_group_id, expense_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND, response.json()

    @pytest.mark.asyncio
    async def test_create_expense_invalid_data(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test expense creation with invalid data."""
        group_id = await self._create_group(client, auth_token_header)

        # Test with invalid amount
        expense_data = {
            "title": "Test Expense",
            "amount": -50.0,  # Negative amount
            "payer_id": str(uuid.uuid4()),
            "category": "Food",
            "date": "2024-01-01",
            "is_payer_included": True,
            "participants_id": [str(uuid.uuid4())],
        }

        response = await self._create_expense(client, auth_token_header, group_id, expense_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_list_expenses_success(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test successful expense listing."""
        group_id = await self._create_group(client, auth_token_header)
        user_response = await client.get("/users/me", headers=auth_token_header)
        user_id = user_response.json()["data"]["user"]["id"]

        # Create an expense first
        expense_data = {
            "title": "Test Expense",
            "amount": 100.0,
            "payer_id": user_id,
            "category": "Food",
            "date": "2024-01-01",
            "is_payer_included": True,
            "participants_id": [user_id],
        }
        await self._create_expense(client, auth_token_header, group_id, expense_data)

        response = await client.get(f"/groups/{group_id}/expenses", headers=auth_token_header)

        assert response.status_code == status.HTTP_200_OK, response.json()
        json_data = response.json()
        assert "data" in json_data
        assert "expenses" in json_data["data"]
        assert "pagination" in json_data["data"]
        expenses = json_data["data"]["expenses"]
        assert len(expenses) == 1, response.json()
        assert expenses[0]["title"] == expense_data["title"]
        assert expenses[0]["amount"] == expense_data["amount"]
        assert len(expenses[0]["participants"]) == 1, json.dumps(json_data, indent=2)

    @pytest.mark.asyncio
    async def test_list_expenses_empty(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test listing expenses when no expenses exist."""
        group_id = await self._create_group(client, auth_token_header)

        response = await client.get(f"/groups/{group_id}/expenses", headers=auth_token_header)

        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "data" in json_data
        assert "expenses" in json_data["data"]
        assert "pagination" in json_data["data"]
        expenses = json_data["data"]["expenses"]
        assert len(expenses) == 0

    @pytest.mark.asyncio
    async def test_list_expenses_pagination(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test expense listing with pagination."""
        group_id = await self._create_group(client, auth_token_header)
        user_response = await client.get("/users/me", headers=auth_token_header)
        user_id = user_response.json()["data"]["user"]["id"]

        # Create multiple expenses
        for i in range(3):
            expense_data = {
                "title": f"Test Expense {i + 1}",
                "amount": 100.0 + i,
                "payer_id": user_id,
                "category": "Food",
                "date": "2024-01-01",
                "is_payer_included": True,
                "participants_id": [user_id],
            }
            await self._create_expense(client, auth_token_header, group_id, expense_data)

        # Test pagination
        response = await client.get(
            f"/groups/{group_id}/expenses?page=1&limit=2",
            headers=auth_token_header,
        )

        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        expenses = json_data["data"]["expenses"]
        pagination = json_data["data"]["pagination"]
        assert len(expenses) == 2
        assert pagination["page"] == 1
        assert pagination["limit"] == 2
        assert pagination["total"] == 3
        assert pagination["pages"] == 2

    @pytest.mark.asyncio
    async def test_get_expense_detail_success(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test successful expense detail retrieval."""
        group_id = await self._create_group(client, auth_token_header)
        user_response = await client.get("/users/me", headers=auth_token_header)
        user_id = user_response.json()["data"]["user"]["id"]

        # Create an expense first
        expense_data = {
            "title": "Detailed Test Expense",
            "amount": 250.75,
            "payer_id": user_id,
            "category": "Entertainment",
            "date": "2024-01-01",
            "is_payer_included": True,
            "participants_id": [user_id],
        }
        create_response = await self._create_expense(client, auth_token_header, group_id, expense_data)
        expense_id = create_response.json()["data"]["expense"]["id"]

        response = await client.get(
            f"/groups/{group_id}/expenses/{expense_id}",
            headers=auth_token_header,
        )

        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "data" in json_data
        assert "expense" in json_data["data"]
        expense = json_data["data"]["expense"]
        assert expense["id"] == expense_id
        assert expense["title"] == expense_data["title"]
        assert expense["amount"] == expense_data["amount"]
        assert expense["category"] == expense_data["category"]
        assert "payer" in expense
        assert "participants" in expense
        assert len(expense["participants"]) == 1

    @pytest.mark.asyncio
    async def test_get_expense_detail_not_found(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test expense detail retrieval for non-existent expense."""
        group_id = await self._create_group(client, auth_token_header)
        fake_expense_id = str(uuid.uuid4())

        response = await client.get(
            f"/groups/{group_id}/expenses/{fake_expense_id}",
            headers=auth_token_header,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_expense_success(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test successful expense update."""
        group_id = await self._create_group(client, auth_token_header)
        user_response = await client.get("/users/me", headers=auth_token_header)
        user_id = user_response.json()["data"]["user"]["id"]

        # Create an expense first
        expense_data = {
            "title": "Original Expense",
            "amount": 100.0,
            "payer_id": user_id,
            "category": "Food",
            "date": "2024-01-01",
            "is_payer_included": True,
            "participants_id": [user_id],
        }
        create_response = await self._create_expense(client, auth_token_header, group_id, expense_data)
        expense_id = create_response.json()["data"]["expense"]["id"]

        # Update the expense
        update_data = {
            "title": "Updated Expense",
            "amount": 200.0,
            "category": "Transport",
            "date": "2024-01-02",
            "payer_id": user_id,
            "participants_id": [
                user_id,
            ],
        }

        response = await self._update_expense(
            client,
            auth_token_header,
            group_id,
            expense_id,
            update_data,
        )

        assert response.status_code == status.HTTP_200_OK, json.dumps(response.json(), indent=2)
        json_data = response.json()
        assert "data" in json_data
        assert "expense" in json_data["data"]
        expense = json_data["data"]["expense"]
        assert expense["id"] == expense_id
        assert expense["title"] == update_data["title"]
        assert expense["amount"] == update_data["amount"]
        assert expense["category"] == update_data["category"]

    @pytest.mark.asyncio
    async def test_update_expense_not_found(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test expense update for non-existent expense."""
        group_id = await self._create_group(client, auth_token_header)
        user_response = await client.get("/users/me", headers=auth_token_header)
        user_id = user_response.json()["data"]["user"]["id"]
        fake_expense_id = str(uuid.uuid4())

        update_data = {
            "title": "Updated Expense",
            "amount": 200.0,
            "category": "Transport",
            "date": "2024-01-02",
            "payer_id": user_id,
            "participants_id": [
               user_id,
            ],
        }

        response = await self._update_expense(
            client,
            auth_token_header,
            group_id,
            fake_expense_id,
            update_data,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_expense_success(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test successful expense deletion."""
        group_id = await self._create_group(client, auth_token_header)
        user_response = await client.get("/users/me", headers=auth_token_header)
        user_id = user_response.json()["data"]["user"]["id"]

        # Create an expense first
        expense_data = {
            "title": "Expense to Delete",
            "amount": 100.0,
            "payer_id": user_id,
            "category": "Food",
            "date": "2024-01-01",
            "is_payer_included": True,
            "participants_id": [user_id],
        }
        create_response = await self._create_expense(client, auth_token_header, group_id, expense_data)
        expense_id = create_response.json()["data"]["expense"]["id"]

        # Delete the expense
        response = await client.delete(
            f"/groups/{group_id}/expenses/{expense_id}",
            headers=auth_token_header,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify the expense is deleted
        get_response = await client.get(
            f"/groups/{group_id}/expenses/{expense_id}",
            headers=auth_token_header,
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_expense_not_found(
        self,
        client: AsyncClient,
        auth_token_header: dict,
    ) -> None:
        """Test expense deletion for non-existent expense."""
        group_id = await self._create_group(client, auth_token_header)
        fake_expense_id = str(uuid.uuid4())

        response = await client.delete(
            f"/groups/{group_id}/expenses/{fake_expense_id}",
            headers=auth_token_header,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_expense_operations_unauthorized(self, client: AsyncClient) -> None:
        """Test all expense operations without authentication."""
        fake_group_id = str(uuid.uuid4())
        fake_expense_id = str(uuid.uuid4())

        # Test list expenses
        response = await client.get(f"/groups/{fake_group_id}/expenses")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Test get expense detail
        response = await client.get(f"/groups/{fake_group_id}/expenses/{fake_expense_id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Test update expense
        response = await client.put(
            f"/groups/{fake_group_id}/expenses/{fake_expense_id}",
            json={"title": "Test"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Test delete expense
        response = await client.delete(f"/groups/{fake_group_id}/expenses/{fake_expense_id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

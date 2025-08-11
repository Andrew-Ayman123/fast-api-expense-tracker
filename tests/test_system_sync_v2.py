"""System tests for Sync API WebSocket endpoints.

Refactored to reduce duplication: all tests now rely on shared helper methods
to create WebSocket clients, open connections, send sync payloads, and gather
results. Each test follows a uniform structure similar to the previous
`test_websocket_invalid_token` style while keeping intent explicit.
"""

import json
import uuid
from typing import Any

import anyio
import pytest
from fastapi import status
from httpx import AsyncClient
from httpx_ws import aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport

from app.main import app
from app.schemas.group_schema import GroupCreateRequest


@pytest.mark.usefixtures("reset_user_data_function")
class TestSyncWebSocketAPI:
    """System tests for WebSocket-based synchronization endpoints."""

    async def _create_group(self, client_v1: AsyncClient, auth_headers: dict, group_name: str = "Test Group") -> str:
        """Create a group and return its ID."""
        response = await client_v1.post(
            "/groups",
            headers=auth_headers,
            json=GroupCreateRequest(
                name=group_name,
                description="Test group for sync testing",
            ).model_dump(),
        )
        assert response.status_code == status.HTTP_200_OK
        return response.json()["data"]["group"]["id"]

    async def _load_sync_data(self, filename: str) -> dict[str, Any]:
        """Load sync test data from JSON file."""
        async with await anyio.open_file(f"./tests/assets/{filename}", "r") as f:
            content = await f.read()
            return json.loads(content)

    async def _replace_placeholders_in_sync_data(
        self,
        client_v1: AsyncClient,
        auth_headers: dict,
        sync_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Replace placeholder values like <user_id> with actual values from the authenticated user."""
        # Get the user ID from the auth token
        user_response = await client_v1.get("/users/me", headers=auth_headers)
        assert user_response.status_code == status.HTTP_200_OK
        user_id = user_response.json()["data"]["user"]["id"]

        # Convert to string to perform replacements
        sync_data_str = json.dumps(sync_data)

        # Replace placeholders
        sync_data_str = sync_data_str.replace("<user_id>", user_id)

        # Convert back to dict
        return json.loads(sync_data_str)

    def _extract_token_from_headers(self, auth_headers: dict[str, str]) -> str:
        """Extract JWT token from authorization headers."""
        auth_value = auth_headers.get("Authorization", "")
        if auth_value.startswith("Bearer "):
            return auth_value[7:]  # Remove "Bearer " prefix
        msg = "Invalid authorization header format"
        raise ValueError(msg)

    # ------------------------------------------------------------------
    # Shared helper methods (WebSocket lifecycle & sync orchestration)
    # ------------------------------------------------------------------
    def _create_ws_client(self) -> AsyncClient:
        """Create a fresh AsyncClient for WebSocket connections (v2 base URL)."""
        transport = ASGIWebSocketTransport(app=app)
        return AsyncClient(transport=transport, base_url="ws://testserver/api/v2")

    def _build_ws_path(self, token: str | None) -> str:
        base = "/sync/bulk/ws"
        return f"{base}?token={token}" if token else base

    async def _connect_and_first_message(self, token: str | None) -> dict[str, Any]:
        """Open a WS (optionally with token) and return the first received message.

        Used for tests expecting an immediate error (invalid/missing token).
        """
        client = self._create_ws_client()
        try:
            async with aconnect_ws(self._build_ws_path(token), client) as websocket: # type: ignore[var-annotated]
                return await websocket.receive_json()
        finally:
            await client.aclose()

    async def _ws_sync(
        self,
        token: str,
        sync_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Perform a sync operation sending `sync_data` and return final message.

        If the first message is an ack it will transparently wait for the second
        (completion/error) message. If no ack is received (e.g. validation error
        on payload), that first message is returned directly.
        """
        client = self._create_ws_client()
        try:
            async with aconnect_ws(self._build_ws_path(token), client) as websocket: # type: ignore[var-annotated]
                # Send payload (only if we have a changes structure; callers ensure shape)
                await websocket.send_json(sync_data)

                first = await websocket.receive_json()
                if first.get("type") == "ack":
                    # Basic validation of ack
                    assert first["status"] == "started"
                    assert "operation_id" in first
                    return await websocket.receive_json()
                return first
        finally:
            await client.aclose()

    async def _get_user_id(self, client_v1: AsyncClient, auth_headers: dict) -> str:
        """Retrieve current authenticated user's ID."""
        resp = await client_v1.get("/users/me", headers=auth_headers)
        assert resp.status_code == status.HTTP_200_OK
        return resp.json()["data"]["user"]["id"]

    @pytest.mark.asyncio
    async def test_websocket_invalid_token(self) -> None:
        """Test WebSocket connection with invalid token."""
        error_message = await self._connect_and_first_message("invalid_token")
        assert error_message["type"] == "error"
        assert error_message["status"] == "failed"
        assert "Invalid token" in error_message["error"]

    @pytest.mark.asyncio
    async def test_websocket_missing_token(self) -> None:
        """Test WebSocket connection without token."""
        error_message = await self._connect_and_first_message(None)
        assert error_message["type"] == "error"
        assert error_message["status"] == "failed"
        assert "Missing token query parameter" in error_message["error"]

    @pytest.mark.asyncio
    async def test_websocket_invalid_payload(self, auth_token_header: dict[str, str]) -> None:
        """Test WebSocket sync with invalid payload structure."""
        token = self._extract_token_from_headers(auth_token_header)
        invalid_data = {
            "changes": [
                {
                    "type": "create",
                    "entity": "expense",
                    # Missing entity_id, data, and timestamp
                },
            ],
        }
        result = await self._ws_sync(token, invalid_data)
        assert result["type"] == "error"
        assert result["status"] == "failed"
        assert "Invalid payload" in result["error"]

    @pytest.mark.asyncio
    async def test_websocket_bulk_sync_healthy_data_1(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test WebSocket bulk sync with healthy data set 1 - creates group and expenses, then updates and deletes."""
        # Load healthy sync data
        sync_data = await self._load_sync_data("sync_healthy_1.json")

        # Replace placeholders with actual user ID
        sync_data = await self._replace_placeholders_in_sync_data(client_v1, auth_token_header, sync_data)

        # Perform WebSocket sync
        token = self._extract_token_from_headers(auth_token_header)
        result = await self._ws_sync(token, sync_data)

        # Check that the task completed successfully
        assert result["type"] == "completed"
        assert result["status"] == "completed"
        assert "operation_id" in result
        assert "notifications" in result
        notifications = result["notifications"]

        # Verify notifications indicate successful operations
        assert len(notifications) == 5  # 1 group create, 2 expense creates, 1 update, 1 delete

        # Check that group creation was successful
        group_create_notification = notifications[0]
        assert "Success: Group" in group_create_notification
        assert "created successfully" in group_create_notification

        # Check that expense creations were successful
        expense1_create_notification = notifications[1]
        assert "Success: Expense" in expense1_create_notification
        assert "created successfully" in expense1_create_notification

        expense2_create_notification = notifications[2]
        assert "Success: Expense" in expense2_create_notification
        assert "created successfully" in expense2_create_notification

        # Check that expense update was successful
        expense_update_notification = notifications[3]
        assert "Success: Expense" in expense_update_notification
        assert "updated successfully" in expense_update_notification

        # Check that expense deletion was successful
        expense_delete_notification = notifications[4]
        assert "Success: Expense" in expense_delete_notification
        assert "deleted successfully" in expense_delete_notification

    @pytest.mark.asyncio
    async def test_websocket_bulk_sync_healthy_data_2(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test WebSocket bulk sync with healthy data set 2 - creates group and expenses, then updates group."""
        sync_data = await self._load_sync_data("sync_healthy_2.json")
        sync_data = await self._replace_placeholders_in_sync_data(client_v1, auth_token_header, sync_data)
        token = self._extract_token_from_headers(auth_token_header)
        result = await self._ws_sync(token, sync_data)
        assert result["status"] == "completed"
        notifications = result["notifications"]
        assert len(notifications) == 5
        for notification in notifications:
            assert "Success:" in notification

    @pytest.mark.asyncio
    async def test_websocket_bulk_sync_unhealthy_data_1(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Unhealthy data set should fail payload validation."""
        sync_data = await self._load_sync_data("sync_unhealthy_1.json")
        sync_data = await self._replace_placeholders_in_sync_data(client_v1, auth_token_header, sync_data)
        token = self._extract_token_from_headers(auth_token_header)
        result = await self._ws_sync(token, sync_data)
        assert result["type"] == "error"
        assert result["status"] == "failed"
        assert "Invalid payload" in result["error"]

    @pytest.mark.asyncio
    async def test_websocket_sync_operations_with_existing_group(
        self, client_v1: AsyncClient, auth_token_header: dict,
    ) -> None:
        """Test WebSocket sync operations with an existing group."""
        group_id = await self._create_group(client_v1, auth_token_header, "Pre-existing Group")
        user_id = await self._get_user_id(client_v1, auth_token_header)
        sync_data = {
            "changes": [
                {
                    "type": "create",
                    "entity": "expense",
                    "entity_id": str(uuid.uuid4()),
                    "data": {
                        "title": "Coffee Meeting",
                        "amount": 15.50,
                        "payer_id": user_id,
                        "category": "Food",
                        "date": "2025-08-07",
                        "is_payer_included": True,
                        "participants_id": [],
                        "group_id": group_id,
                    },
                    "timestamp": "2025-08-07T10:00:00Z",
                },
            ],
        }
        token = self._extract_token_from_headers(auth_token_header)
        result = await self._ws_sync(token, sync_data)
        assert result["status"] == "completed"
        assert len(result["notifications"]) == 1
        assert "Success: Expense" in result["notifications"][0]

    @pytest.mark.asyncio
    async def test_websocket_sync_operations_with_nonexistent_group(self, auth_token_header: dict) -> None:
        """Test WebSocket sync operations with a non-existent group."""
        fake_group_id = str(uuid.uuid4())
        sync_data = {
            "changes": [
                {
                    "type": "create",
                    "entity": "expense",
                    "entity_id": str(uuid.uuid4()),
                    "data": {
                        "title": "Coffee Meeting",
                        "amount": 15.50,
                        "payer_id": "a4981587-160a-4175-90cc-d56a053958dd",
                        "category": "Food",
                        "date": "2025-08-07",
                        "is_payer_included": True,
                        "participants_id": [],
                        "group_id": fake_group_id,
                    },
                    "timestamp": "2025-08-07T10:00:00Z",
                },
            ],
        }
        token = self._extract_token_from_headers(auth_token_header)
        result = await self._ws_sync(token, sync_data)
        assert result["status"] == "completed"
        assert len(result["notifications"]) == 1
        assert "Failed: create expense: group" in result["notifications"][0]
        assert "not found or not accessible" in result["notifications"][0]

    @pytest.mark.asyncio
    async def test_websocket_sync_delete_nonexistent_entities(self, auth_token_header: dict) -> None:
        """Test WebSocket sync delete operations with non-existent entities."""
        fake_expense_id = str(uuid.uuid4())
        fake_group_id = str(uuid.uuid4())
        sync_data = {
            "changes": [
                {
                    "type": "delete",
                    "entity": "expense",
                    "entity_id": fake_expense_id,
                    "timestamp": "2025-08-07T10:00:00Z",
                },
                {"type": "delete", "entity": "group", "entity_id": fake_group_id, "timestamp": "2025-08-07T10:01:00Z"},
            ],
        }
        token = self._extract_token_from_headers(auth_token_header)
        result = await self._ws_sync(token, sync_data)
        assert result["status"] == "completed"
        assert len(result["notifications"]) == 2
        for notification in result["notifications"]:
            assert "Failed:" in notification
            assert "could not be found or might be deleted before" in notification

    @pytest.mark.asyncio
    async def test_websocket_sync_update_nonexistent_entities(self, auth_token_header: dict) -> None:
        """Test WebSocket sync update operations with non-existent entities."""
        fake_expense_id = str(uuid.uuid4())
        fake_group_id = str(uuid.uuid4())
        sync_data = {
            "changes": [
                {
                    "type": "update",
                    "entity": "expense",
                    "entity_id": fake_expense_id,
                    "data": {
                        "title": "Updated Expense",
                        "amount": 25.00,
                        "payer_id": "a4981587-160a-4175-90cc-d56a053958dd",
                        "category": "Food",
                        "date": "2025-08-07",
                        "is_payer_included": True,
                        "participants_id": [],
                    },
                    "timestamp": "2025-08-07T10:00:00Z",
                },
                {
                    "type": "update",
                    "entity": "group",
                    "entity_id": fake_group_id,
                    "data": {"name": "Updated Group", "description": "Updated description"},
                    "timestamp": "2025-08-07T10:01:00Z",
                },
            ],
        }
        token = self._extract_token_from_headers(auth_token_header)
        result = await self._ws_sync(token, sync_data)
        assert result["status"] == "completed"
        assert len(result["notifications"]) == 2
        for notification in result["notifications"]:
            assert "Failed:" in notification

    @pytest.mark.asyncio
    async def test_websocket_sync_mixed_operations(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test WebSocket sync operations with mixed changes."""
        group_id = await self._create_group(client_v1, auth_token_header, "Mixed Test Group")
        user_id = await self._get_user_id(client_v1, auth_token_header)
        fake_expense_id = str(uuid.uuid4())
        sync_data = {
            "changes": [
                {
                    "type": "create",
                    "entity": "expense",
                    "entity_id": str(uuid.uuid4()),
                    "data": {
                        "title": "Valid Expense",
                        "amount": 50.00,
                        "payer_id": user_id,
                        "category": "Food",
                        "date": "2025-08-07",
                        "is_payer_included": True,
                        "participants_id": [],
                        "group_id": group_id,
                    },
                    "timestamp": "2025-08-07T10:00:00Z",
                },
                {
                    "type": "delete",
                    "entity": "expense",
                    "entity_id": fake_expense_id,
                    "timestamp": "2025-08-07T10:01:00Z",
                },
            ],
        }
        token = self._extract_token_from_headers(auth_token_header)
        result = await self._ws_sync(token, sync_data)
        assert result["status"] == "completed"
        assert len(result["notifications"]) == 2
        assert "Success: Expense" in result["notifications"][0]
        assert "Failed:" in result["notifications"][1]

    @pytest.mark.asyncio
    async def test_websocket_sync_empty_changes_list(self, auth_token_header: dict) -> None:
        """Test WebSocket sync operations with an empty changes list."""
        sync_data: dict[str, list] = {"changes": []}
        token = self._extract_token_from_headers(auth_token_header)
        result = await self._ws_sync(token, sync_data)
        assert result["status"] == "completed"
        assert len(result["notifications"]) == 0

    @pytest.mark.asyncio
    async def test_websocket_sync_timestamp_validation(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test WebSocket sync operations with timestamp validation."""
        group_id = await self._create_group(client_v1, auth_token_header, "Timestamp Test Group")
        user_id = await self._get_user_id(client_v1, auth_token_header)
        expense_data = {
            "title": "Original Expense",
            "amount": 100.00,
            "payer_id": user_id,
            "category": "Food",
            "date": "2025-08-07",
            "is_payer_included": True,
            "participants_id": [],
        }
        expense_response = await client_v1.post(
            f"/groups/{group_id}/expenses",
            headers=auth_token_header,
            json=expense_data,
        )
        assert expense_response.status_code == status.HTTP_200_OK
        expense_id = expense_response.json()["data"]["expense"]["id"]
        sync_data = {
            "changes": [
                {
                    "type": "update",
                    "entity": "expense",
                    "entity_id": expense_id,
                    "data": {
                        "title": "Should Not Update",
                        "amount": 200.00,
                        "payer_id": "a4981587-160a-4175-90cc-d56a053958dd",
                        "category": "Food",
                        "date": "2025-08-07",
                        "is_payer_included": True,
                        "participants_id": [],
                    },
                    "timestamp": "2020-01-01T10:00:00Z",
                },
            ],
        }
        token = self._extract_token_from_headers(auth_token_header)
        result = await self._ws_sync(token, sync_data)
        assert result["status"] == "completed"
        assert len(result["notifications"]) == 1
        assert "update discarded (older timestamp)" in result["notifications"][0]

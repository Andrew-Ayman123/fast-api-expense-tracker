"""System tests for Sync API endpoints."""

import asyncio
import json
import logging
import time
import uuid
from typing import Any

import anyio
import pytest
from fastapi import status
from httpx import AsyncClient

from app.schemas.group_schema import GroupCreateRequest

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures("reset_user_data_function")
class TestSyncAPI:
    """System tests for synchronization endpoints including bulk sync and status checking."""

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

    async def _wait_for_task_completion(
        self,
        client_v1: AsyncClient,
        auth_headers: dict,
        operation_id: str,
        max_wait_seconds: int = 30,
    ) -> dict[str, Any]:
        """Wait for a sync task to complete and return the final status."""
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            response = await client_v1.get(f"/sync/status/{operation_id}", headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK

            status_data = response.json()["data"]
            if status_data["status"] in ["completed", "failed"]:
                return status_data

            # Wait a bit before checking again
            await asyncio.sleep(0.5)

        msg = f"Task {operation_id} did not complete within {max_wait_seconds} seconds"
        raise TimeoutError(msg)

    @pytest.mark.asyncio
    async def test_bulk_sync_invalid_data(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test bulk sync with invalid data structure."""
        # Test with missing required fields
        invalid_data = {
            "changes": [
                {
                    "type": "create",
                    "entity": "expense",
                    # Missing entity_id, data, and timestamp
                },
            ],
        }

        response = await client_v1.post(
            "/sync/bulk",
            headers=auth_token_header,
            json=invalid_data,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_bulk_sync_healthy_data_1(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test bulk sync with healthy data set 1 - creates group and expenses, then updates and deletes."""
        # Load healthy sync data
        sync_data = await self._load_sync_data("sync_healthy_1.json")

        # Replace placeholders with actual user ID
        sync_data = await self._replace_placeholders_in_sync_data(client_v1, auth_token_header, sync_data)

        # Start bulk sync operation
        response = await client_v1.post(
            "/sync/bulk",
            headers=auth_token_header,
            json=sync_data,
        )

        assert response.status_code == status.HTTP_200_OK
        operation_data = response.json()["data"]
        assert "operation_id" in operation_data
        operation_id = operation_data["operation_id"]

        # Wait for task completion
        final_status = await self._wait_for_task_completion(client_v1, auth_token_header, operation_id)

        # Check that the task completed successfully
        assert final_status["status"] == "completed"
        assert final_status["operation_id"] == operation_id
        assert "notifications" in final_status
        notifications = final_status["notifications"]

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
    async def test_bulk_sync_healthy_data_2(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test bulk sync with healthy data set 2 - creates group and expenses, then updates group."""
        # Load healthy sync data
        sync_data = await self._load_sync_data("sync_healthy_2.json")

        # Replace placeholders with actual user ID
        sync_data = await self._replace_placeholders_in_sync_data(client_v1, auth_token_header, sync_data)

        # Start bulk sync operation
        response = await client_v1.post(
            "/sync/bulk",
            headers=auth_token_header,
            json=sync_data,
        )

        assert response.status_code == status.HTTP_200_OK
        operation_data = response.json()["data"]
        operation_id = operation_data["operation_id"]

        # Wait for task completion
        final_status = await self._wait_for_task_completion(client_v1, auth_token_header, operation_id)

        # Check that the task completed successfully
        assert final_status["status"] == "completed"
        notifications = final_status["notifications"]

        # Verify all operations were successful
        assert len(notifications) == 5  # 1 group create, 2 expense creates, 1 group update, 1 expense delete

        for notification in notifications:
            assert "Success:" in notification

    @pytest.mark.asyncio
    async def test_bulk_sync_unhealthy_data_1(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test bulk sync with unhealthy data set 1 - contains validation errors."""
        # Load unhealthy sync data
        sync_data = await self._load_sync_data("sync_unhealthy_1.json")

        # Replace placeholders with actual user ID
        sync_data = await self._replace_placeholders_in_sync_data(client_v1, auth_token_header, sync_data)

        # Start bulk sync operation
        response = await client_v1.post(
            "/sync/bulk",
            headers=auth_token_header,
            json=sync_data,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_sync_status_nonexistent_operation(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test sync status check for non-existent operation."""
        fake_operation_id = str(uuid.uuid4())

        response = await client_v1.get(f"/sync/status/{fake_operation_id}", headers=auth_token_header)

        assert response.status_code == status.HTTP_200_OK
        status_data = response.json()["data"]

        # Non-existent operations should return "pending" status in Celery
        assert status_data["operation_id"] == fake_operation_id
        assert status_data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_sync_status_during_processing(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test sync status check during operation processing."""
        # Load sync data with multiple operations to ensure some processing time
        sync_data = await self._load_sync_data("sync_healthy_1.json")

        # Replace placeholders with actual user ID
        sync_data = await self._replace_placeholders_in_sync_data(client_v1, auth_token_header, sync_data)

        # Start bulk sync operation
        response = await client_v1.post(
            "/sync/bulk",
            headers=auth_token_header,
            json=sync_data,
        )

        assert response.status_code == status.HTTP_200_OK
        operation_id = response.json()["data"]["operation_id"]

        # Check status immediately - might catch it in processing state
        response = await client_v1.get(f"/sync/status/{operation_id}", headers=auth_token_header)

        assert response.status_code == status.HTTP_200_OK
        status_data = response.json()["data"]
        assert status_data["operation_id"] == operation_id
        assert status_data["status"] in ["pending", "processing", "completed"]
        assert isinstance(status_data["notifications"], list)

    @pytest.mark.asyncio
    async def test_sync_operations_with_existing_group(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test sync operations that reference existing groups."""
        # First create a group through regular API
        group_id = await self._create_group(client_v1, auth_token_header, "Pre-existing Group")

        # get the user id by users/me
        user_response = await client_v1.get("/users/me", headers=auth_token_header)
        assert user_response.status_code == status.HTTP_200_OK
        user_id = user_response.json()["data"]["user"]["id"]

        # Create sync data that references the existing group
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

        # Start bulk sync operation
        response = await client_v1.post(
            "/sync/bulk",
            headers=auth_token_header,
            json=sync_data,
        )

        assert response.status_code == status.HTTP_200_OK
        operation_id = response.json()["data"]["operation_id"]

        # Wait for completion
        final_status = await self._wait_for_task_completion(client_v1, auth_token_header, operation_id)

        # Should succeed since group exists
        assert final_status["status"] == "completed"
        assert len(final_status["notifications"]) == 1
        assert "Success: Expense" in final_status["notifications"][0]

    @pytest.mark.asyncio
    async def test_sync_operations_with_nonexistent_group(
        self, client_v1: AsyncClient, auth_token_header: dict,
    ) -> None:
        """Test sync operations that reference non-existent groups."""
        fake_group_id = str(uuid.uuid4())

        # Create sync data that references a non-existent group
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

        # Start bulk sync operation
        response = await client_v1.post(
            "/sync/bulk",
            headers=auth_token_header,
            json=sync_data,
        )

        assert response.status_code == status.HTTP_200_OK
        operation_id = response.json()["data"]["operation_id"]

        # Wait for completion
        final_status = await self._wait_for_task_completion(client_v1, auth_token_header, operation_id)

        # Should fail since group doesn't exist
        assert final_status["status"] == "completed"
        assert len(final_status["notifications"]) == 1
        assert "Failed: create expense: group" in final_status["notifications"][0]
        assert "not found or not accessible" in final_status["notifications"][0]

    @pytest.mark.asyncio
    async def test_sync_delete_nonexistent_entities(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test sync delete operations on non-existent entities."""
        fake_expense_id = str(uuid.uuid4())
        fake_group_id = str(uuid.uuid4())

        # Create sync data that tries to delete non-existent entities
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

        # Start bulk sync operation
        response = await client_v1.post(
            "/sync/bulk",
            headers=auth_token_header,
            json=sync_data,
        )

        assert response.status_code == status.HTTP_200_OK
        operation_id = response.json()["data"]["operation_id"]

        # Wait for completion
        final_status = await self._wait_for_task_completion(client_v1, auth_token_header, operation_id)

        # Should complete but with failure notifications
        assert final_status["status"] == "completed"
        assert len(final_status["notifications"]) == 2

        # Both deletions should fail
        for notification in final_status["notifications"]:
            assert "Failed:" in notification
            assert "could not be found or might be deleted before" in notification

    @pytest.mark.asyncio
    async def test_sync_update_nonexistent_entities(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test sync update operations on non-existent entities."""
        fake_expense_id = str(uuid.uuid4())
        fake_group_id = str(uuid.uuid4())

        # Create sync data that tries to update non-existent entities
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

        # Start bulk sync operation
        response = await client_v1.post(
            "/sync/bulk",
            headers=auth_token_header,
            json=sync_data,
        )

        assert response.status_code == status.HTTP_200_OK
        operation_id = response.json()["data"]["operation_id"]

        # Wait for completion
        final_status = await self._wait_for_task_completion(client_v1, auth_token_header, operation_id)

        # Should complete but with failure notifications
        assert final_status["status"] == "completed"
        assert len(final_status["notifications"]) == 2

        # Both updates should fail
        for notification in final_status["notifications"]:
            assert "Failed:" in notification

    @pytest.mark.asyncio
    async def test_sync_mixed_operations(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test sync with mixed successful and failed operations."""
        # Create a group first for some operations to succeed
        group_id = await self._create_group(client_v1, auth_token_header, "Mixed Test Group")
        fake_expense_id = str(uuid.uuid4())

        # get the user id by users/me
        user_response = await client_v1.get("/users/me", headers=auth_token_header)
        assert user_response.status_code == status.HTTP_200_OK
        user_id = user_response.json()["data"]["user"]["id"]

        # Create sync data with mixed operations
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

        # Start bulk sync operation
        response = await client_v1.post(
            "/sync/bulk",
            headers=auth_token_header,
            json=sync_data,
        )

        assert response.status_code == status.HTTP_200_OK
        operation_id = response.json()["data"]["operation_id"]

        # Wait for completion
        final_status = await self._wait_for_task_completion(client_v1, auth_token_header, operation_id)

        # Should complete with mixed results
        assert final_status["status"] == "completed"
        assert len(final_status["notifications"]) == 2

        # First operation should succeed, second should fail
        assert "Success: Expense" in final_status["notifications"][0]
        assert "Failed:" in final_status["notifications"][1]

    @pytest.mark.asyncio
    async def test_sync_empty_changes_list(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test sync with empty changes list."""
        sync_data: dict[str, list] = {"changes": []}

        # Start bulk sync operation
        response = await client_v1.post(
            "/sync/bulk",
            headers=auth_token_header,
            json=sync_data,
        )

        assert response.status_code == status.HTTP_200_OK
        operation_id = response.json()["data"]["operation_id"]

        # Wait for completion
        final_status = await self._wait_for_task_completion(client_v1, auth_token_header, operation_id)

        # Should complete successfully with no notifications
        assert final_status["status"] == "completed"
        assert len(final_status["notifications"]) == 0

    @pytest.mark.asyncio
    async def test_sync_timestamp_validation(self, client_v1: AsyncClient, auth_token_header: dict) -> None:
        """Test sync operations with various timestamp formats."""
        # Create a group and expense first for update operations
        group_id = await self._create_group(client_v1, auth_token_header, "Timestamp Test Group")

        # get the user id by users/me
        user_response = await client_v1.get("/users/me", headers=auth_token_header)
        assert user_response.status_code == status.HTTP_200_OK
        user_id = user_response.json()["data"]["user"]["id"]

        # Create an expense
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

        # Test update with older timestamp (should be discarded)
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
                    "timestamp": "2020-01-01T10:00:00Z",  # Very old timestamp
                },
            ],
        }

        response = await client_v1.post(
            "/sync/bulk",
            headers=auth_token_header,
            json=sync_data,
        )

        assert response.status_code == status.HTTP_200_OK
        operation_id = response.json()["data"]["operation_id"]

        # Wait for completion
        final_status = await self._wait_for_task_completion(client_v1, auth_token_header, operation_id)

        # Should complete but discard the update due to old timestamp
        assert final_status["status"] == "completed"
        assert len(final_status["notifications"]) == 1
        assert "update discarded (older timestamp)" in final_status["notifications"][0]

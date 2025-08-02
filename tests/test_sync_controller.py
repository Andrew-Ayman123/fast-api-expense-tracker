"""Test cases for the SyncController in the FastAPI application."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSyncController:
    """Test suite for the SyncController endpoints in the FastAPI application."""

    @patch("app.services.celery_worker_service.say_hello.delay")
    async def test_hello_task_queued(self, mock_task: "MagicMock", client: AsyncClient) -> None:
        """Test queuing a hello task."""
        mock_task.return_value.id = "mocked-task-id"
        response = await client.get("/sync/hello")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Task queued"
        assert data["task_id"] == "mocked-task-id"

    @patch("app.services.celery_worker_service.say_hello.delay")
    async def test_hello_task_wait_for_result(self, mock_task: MagicMock, client: AsyncClient) -> None:
        """Test queuing a hello task and waiting for result."""
        mock_task.return_value.id = "mocked-task-id"
        mock_task.return_value.get.return_value = "Hello task completed successfully!"
        response = await client.get("/sync/hello?wait=true")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Task completed"
        assert data["task_id"] == "mocked-task-id"
        assert data["result"] == "Hello task completed successfully!"

    @patch("app.interfaces.api.v1.controllers.sync_controller.AsyncResult")
    @patch("app.services.celery_worker_service.say_hello.delay")
    async def test_get_task_result_pending(
        self, mock_task: MagicMock, mock_result: MagicMock, client: AsyncClient,
    ) -> None:
        """Test retrieving result of a queued (not-yet-finished) task."""
        mock_task.return_value.id = "mocked-task-id"
        mock_result_instance = mock_result.return_value
        mock_result_instance.ready.return_value = False
        mock_result_instance.state = "PENDING"
        mock_result.side_effect = lambda task_id, app=None: mock_result_instance  # noqa: ARG005

        response = await client.get("/sync/hello")
        assert response.status_code == status.HTTP_200_OK
        task_id = response.json()["task_id"]

        result_response = await client.get(f"/sync/result/{task_id}")
        assert result_response.status_code == status.HTTP_200_OK
        data = result_response.json()
        assert data["message"] == "Task not completed"
        assert data["task_id"] == task_id
        assert data["status"] == "PENDING"



    @patch("app.interfaces.api.v1.controllers.sync_controller.AsyncResult")
    async def test_get_task_result_invalid_id(self, mock_result: MagicMock, client: AsyncClient) -> None:
        """Test retrieving result with an invalid task ID."""
        mock_result_instance = mock_result.return_value
        mock_result_instance.ready.return_value = False
        mock_result_instance.state = "PENDING"
        mock_result.side_effect = lambda task_id, app=None: mock_result_instance  # noqa: ARG005

        response = await client.get("/sync/result/invalid-id")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Task not completed"
        assert data["task_id"] == "invalid-id"
        assert data["status"] == "PENDING"

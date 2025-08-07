"""Sync Controller for handling bulk synchronization requests."""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.celery_dependencies import get_celery
from app.exceptions.application_exception import ApplicationError
from app.middleware.jwt_auth_middleware import get_current_user_id
from app.schemas.sync_schema import (
    SyncBulkRequest,
    SyncBulkResponse,
    SyncBulkResponseData,
    SyncStatusData,
    SyncStatusResponse,
)
from app.utils.create_exception_util import create_http_exception
from app.utils.logger_util import get_logger
from app.workers.sync_worker import bulk_sync

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/bulk")
async def run_bulk_sync(
    request: SyncBulkRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> SyncBulkResponse:
    """Run a bulk sync operation with the provided changes."""
    try:
        task = bulk_sync.delay(request.model_dump(), current_user_id=str(current_user_id))
        # Return immediately with the task ID as operation ID
        return SyncBulkResponse(data=SyncBulkResponseData(operation_id=task.id))
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        get_logger().error("Error running bulk sync: %s", str(e))
        raise create_http_exception(
            message="Failed to start bulk sync operation",
            status_code=500,
            details={"error": str(e)},
        ) from e


@router.get("/status/{operation_id}")
async def get_sync_status(
    operation_id: str,
    _: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> SyncStatusResponse:
    """Get the status of a sync operation by operation ID."""
    try:
        # Get Celery task result by operation_id (which is the task ID)
        celery_app = get_celery()
        task_result = celery_app.AsyncResult(operation_id)

        # Map Celery states to our status values
        status_mapping = {
            "PENDING": "pending",
            "STARTED": "processing",
            "SUCCESS": "completed",
            "FAILURE": "failed",
            "RETRY": "processing",
            "REVOKED": "failed",
        }

        status = status_mapping.get(task_result.state, "unknown")
        notifications = []
        completed_at = None

        if task_result.state == "SUCCESS":
            # Extract notifications from successful result
            result:list[str] = task_result.result
            if isinstance(result, dict) and "notifications" in result:
                notifications = result["notifications"]
            completed_at = datetime.now(tz=UTC)  # In real app, store actual completion time
        elif task_result.state == "FAILURE":
            # Handle failure case
            notifications = [f"Operation failed: {task_result.info!s}"]
            completed_at = datetime.now(tz=UTC)

        return SyncStatusResponse(
            data=SyncStatusData(
                operation_id=operation_id,
                status=status,
                created_at=datetime.now(tz=UTC),  # In real app, store actual creation time
                completed_at=completed_at,
                notifications=notifications,
            ),
        )
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        get_logger().error("Error getting sync status: %s", str(e))
        raise create_http_exception(
            message="Failed to get sync status",
            status_code=500,
            details={"error": str(e)},
        ) from e

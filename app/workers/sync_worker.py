"""Celery worker for handling bulk synchronization tasks."""

import asyncio
from uuid import UUID

from app.dependencies.celery_dependencies import get_celery, get_sync_service
from app.schemas.sync_schema import SyncBulkRequest

_celery = get_celery()

@_celery.task(name="app.workers.sync_worker.bulk_sync")
def bulk_sync(request: dict, current_user_id: str) -> dict:
    """Celery task for bulk synchronization."""
    return asyncio.run(_bulk_sync_async(request, current_user_id))


async def _bulk_sync_async(request: dict, current_user_id: str) -> dict:
    """Async logic for bulk synchronization."""
    sync_service = get_sync_service()
    current_user_id_parsed = UUID(current_user_id)
    request_parsed = SyncBulkRequest.model_validate(request)

    return await sync_service.handle_bulk_sync(request_parsed, current_user_id_parsed)


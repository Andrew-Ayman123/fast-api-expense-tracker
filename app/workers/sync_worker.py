"""Celery worker for handling bulk synchronization tasks."""

import asyncio
from uuid import UUID

from app.dependencies.celery_dependencies import get_celery
from app.dependencies.services_dependencies import get_sync_service
from app.schemas.sync_schema import SyncBulkRequest

_celery = get_celery()

@_celery.task(name="app.workers.sync_worker.bulk_sync")
def bulk_sync(request: dict,current_user_id:str) -> dict:
    """Celery task to handle bulk synchronization of data changes."""
    sync_service = get_sync_service()
    current_user_id_parsed = UUID(current_user_id)
    request_parsed = SyncBulkRequest.model_validate(request)

    return asyncio.run(sync_service.handle_bulk_sync(request_parsed, current_user_id_parsed))

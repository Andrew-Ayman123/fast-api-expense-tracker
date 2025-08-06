"""Celery worker for handling bulk synchronization tasks."""

import asyncio

from app.config.celery_config import celery_app
from app.dependencies.services_dependencies import get_sync_service


@celery_app.task(name="app.workers.sync_worker.bulk_sync")
def bulk_sync(request : dict ) -> dict:
    """Celery task to handle bulk synchronization of data changes."""  # noqa: D202

    sync_service = get_sync_service()

    return asyncio.run(sync_service.handle_bulk_sync(request))

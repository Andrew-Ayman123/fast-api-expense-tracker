"""Sync Controller for handling bulk synchronization requests."""

from fastapi import APIRouter

from app.schemas.sync_schema import SyncBulkRequest, SyncBulkResponse
from app.worker.sync_worker import bulk_sync

router = APIRouter(prefix="/sync", tags=["sync"])

@router.post("/bulk" , response_model=SyncBulkResponse)  # noqa: FAST001
async def run_bulk_sync(  # noqa: D103
    request: SyncBulkRequest,
) -> SyncBulkResponse:
    task = bulk_sync.delay(request.dict())
    result_dict = task.get()
    return SyncBulkResponse(**result_dict)

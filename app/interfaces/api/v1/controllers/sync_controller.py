"""Sync controller for the expense tracker application."""

from fastapi import APIRouter

from app.worker.sync_worker import test_add

router = APIRouter(prefix="/sync", tags=["sync"])

@router.get("/hello")
async def run_test_task() -> dict:
    """Endpoint to run a test task."""
    task = test_add.delay(10, 20)
    return {"task_id": task.id}

"""Sync Module Controller."""

import logging

from celery.result import AsyncResult
from fastapi import APIRouter

from app.celery_worker import celery, say_hello

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["sync"])

@router.get("/hello")
def run_task(*, wait: bool = False) -> dict:
    """Queue a hello task and optionally wait for the result."""
    task = say_hello.delay()
    logger.info(f"Task queued: {task.id}")  # noqa: G004
    if wait:
        logger.info(f"Waiting for task {task.id}...")  # noqa: G004
        result = task.get(timeout=10)
        logger.info(f"Task {task.id} result: {result}")  # noqa: G004
        return {"message": "Task completed", "task_id": task.id, "result": result}
    return {"message": "Task queued", "task_id": task.id}

@router.get("/result/{task_id}")
def get_task_result(task_id: str) -> dict:
    """Retrieve the result of a task by its ID."""
    task = AsyncResult(task_id, app=celery)
    logger.info(f"Checking task {task_id} status: {task.state}")  # noqa: G004
    if not task.ready():
        return {"message": "Task not completed", "task_id": task_id, "status": task.state}
    if not task.successful():
        return {"message": "Task failed", "task_id": task_id, "error": str(task.result)}
    return {"message": "Task completed", "task_id": task_id, "result": task.result}

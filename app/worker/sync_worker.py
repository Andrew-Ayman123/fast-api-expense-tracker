"""Celery worker for the expense tracker application."""

from app.config.celery_config import celery_app


@celery_app.task(name="app.workers.sync_worker.test_add")
def test_add(a: int, b: int):  # noqa: ANN201
    """Test task to add two numbers."""
    return a + b

"""Celery configuration for the expense tracker application."""
import os

from celery import Celery  #type: ignore  # noqa: PGH003

celery_app = Celery(
    "expense_tracker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

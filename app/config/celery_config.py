"""Celery configuration for the expense tracker application."""

from celery import Celery  #type: ignore  # noqa: PGH003

celery_app = Celery(
    "expense_tracker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

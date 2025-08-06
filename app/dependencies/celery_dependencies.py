"""Celery dependencies for the expense tracker application."""

from functools import lru_cache

from celery import Celery  #type: ignore[import-untyped]

from app.dependencies.settings_dependencies import get_env_settings


@lru_cache
def get_celery() -> Celery:
    """Create and configure the Celery application."""
    celery = Celery(
        "expense_tracker",
        broker=get_env_settings().celery_broker_url,
        backend=get_env_settings().celery_result_backend,
    )

    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],  # Only allow json content
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )

    return celery

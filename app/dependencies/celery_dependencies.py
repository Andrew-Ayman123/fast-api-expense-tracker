"""Celery dependencies for the expense tracker application."""

from functools import lru_cache

from celery import Celery  # type: ignore[import-untyped]
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.dependencies.repos_dependencies import (
    get_expense_participant_repository,
    get_expense_repository,
    get_group_member_repository,
    get_group_repository,
    get_user_repository,
)
from app.dependencies.services_dependencies import get_expense_service, get_group_service
from app.dependencies.settings_dependencies import get_env_settings
from app.services.expense_service import ExpenseService
from app.services.group_service import GroupService
from app.services.sync_service.sync_service import SyncService
from app.utils.conditional_cache_util import conditional_lru_cache


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


@conditional_lru_cache()
def _get_session_maker_for_celery() -> async_sessionmaker[AsyncSession]:
    """Get the session maker instance for Celery tasks."""
    engine = create_async_engine(
        get_env_settings().database_url,
        echo=get_env_settings().database_logging,
        poolclass=NullPool,
        future=True,
    )
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def get_sync_service() -> SyncService:
    """Get the Sync service instance for Celery tasks."""

    async def _get_services() -> tuple[GroupService, ExpenseService]:
        session_maker = _get_session_maker_for_celery()
        async with session_maker() as session:
            group_service = get_group_service(
                user_repository=get_user_repository(session),
                group_repository=get_group_repository(session),
                group_member_repository=get_group_member_repository(session),
            )
            expense_service = get_expense_service(
                expense_repository=get_expense_repository(session),
                expense_participant_repository=get_expense_participant_repository(session),
                group_service=group_service,
                user_repository=get_user_repository(session),
            )
            return group_service, expense_service

    return SyncService(_get_services)

# mypy: disable-error-code=arg-type

"""Dependency for repositories, providing access to the User repository."""
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.dependencies.database_dependencies import get_database_session, get_session_maker
from app.dependencies.repos_dependencies import (
    get_expense_participant_repository,
    get_expense_repository,
    get_group_member_repository,
    get_group_repository,
    get_user_repository,
)
from app.dependencies.settings_dependencies import get_env_settings
from app.repositories.interfaces.expense_participants_interface import ExpenseParticipantRepositoryInterface
from app.repositories.interfaces.expense_repository_interface import ExpenseRepositoryInterface
from app.repositories.interfaces.groups_members_interface import GroupMemberRepositoryInterface
from app.repositories.interfaces.groups_repository_interface import GroupRepositoryInterface
from app.repositories.interfaces.user_repository_interface import UserRepositoryInterface
from app.services.expense_service import ExpenseService
from app.services.group_service import GroupService
from app.services.jwt_service import JWTService
from app.services.sync_service.sync_service import SyncService
from app.services.user_service import UserService


def get_group_service(
    user_repository: Annotated[UserRepositoryInterface, Depends(get_user_repository)],
    group_repository: Annotated[GroupRepositoryInterface, Depends(get_group_repository)],
    group_member_repository: Annotated[GroupMemberRepositoryInterface, Depends(get_group_member_repository)],
    ) -> GroupService:
    """Get the Group service instance.

    Note: This is a placeholder implementation. In a complete implementation,
    you would inject the required repository interfaces.

    Returns:
        GroupService: The Group service instance.

    """
    return GroupService(
        group_repository=group_repository,
        group_member_repository=group_member_repository,
        user_repository=user_repository,
    )


def get_expense_service(
    expense_repository: Annotated[ExpenseRepositoryInterface, Depends(get_expense_repository)],
    expense_participant_repository: Annotated[
        ExpenseParticipantRepositoryInterface, Depends(get_expense_participant_repository),
    ],
    group_service: Annotated[GroupService, Depends(get_group_service)],
    user_repository: Annotated[UserRepositoryInterface, Depends(get_user_repository)],
) -> ExpenseService:
    """Get the Expense service instance.

    Args:
        expense_repository (ExpenseRepositoryInterface): The Expense repository instance.
        expense_participant_repository (ExpenseParticipantRepositoryInterface): The ExpenseParticipant repository
            instance.
        group_service (GroupService): The Group service instance.
        user_repository (UserRepositoryInterface): The User repository instance.

    Returns:
        ExpenseService: The Expense service instance.

    """
    return ExpenseService(
        expense_repository=expense_repository,
        expense_participant_repository=expense_participant_repository,
        group_service=group_service,
        user_repository=user_repository,
    )


# It's ok to cache JWTService because it is stateless and does not hold any mutable state
@lru_cache
def get_jwt_service() -> JWTService:
    """Get the JWT service instance.

    Returns:
        JWTService: The JWT service instance.

    """
    settings = get_env_settings()
    return JWTService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expiration_minutes=settings.jwt_expiration_minutes,
    )


def get_user_service(
    user_repository: Annotated[UserRepositoryInterface, Depends(get_user_repository)],
) -> UserService:
    """Get the User service instance.

    Args:
        user_repository (UserRepositoryInterface): The User repository instance.

    Returns:
        UserService: The User service instance.

    """
    return UserService(
        user_repository=user_repository,
    )
def get_sync_service(
) -> SyncService:
    """Get the Sync service instance.

    Args:
        expense_service (ExpenseService): The Expense service instance.
        group_service (GroupService): The Group service instance.

    Returns:
        SyncService: The Sync service instance.

    """
    session_maker= get_session_maker()
    session = get_database_session(session_maker)
    group_service= get_group_service(
        user_repository=get_user_repository(session),
        group_repository=get_group_repository(session),
        group_member_repository=get_group_member_repository(session),
    )
    expense_service= get_expense_service(
        expense_repository=get_expense_repository(session),
        expense_participant_repository=get_expense_participant_repository(session),
        group_service=group_service,
        user_repository=get_user_repository(session),

    )
    return SyncService(
        expense_service=expense_service,
        group_service=group_service,
    )

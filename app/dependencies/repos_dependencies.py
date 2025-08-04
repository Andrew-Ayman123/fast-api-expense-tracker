"""Dependency for repositories, providing access to the User repository."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database_dependencies import get_database_session
from app.repositories.expense_participants_pg_repository_impl import ExpenseParticipantsPGRepository
from app.repositories.expense_pg_repository_impl import ExpensePGRepository
from app.repositories.groups_members_pg_repository_impl import GroupMemberPGRepository
from app.repositories.groups_pg_repository_impl import GroupPGRepository
from app.repositories.interfaces.expense_participants_interface import ExpenseParticipantRepositoryInterface
from app.repositories.interfaces.expense_repository_interface import ExpenseRepositoryInterface
from app.repositories.interfaces.groups_members_interface import GroupMemberRepositoryInterface
from app.repositories.interfaces.groups_repository_interface import GroupRepositoryInterface
from app.repositories.interfaces.user_repository_interface import UserRepositoryInterface
from app.repositories.user_pg_repository_impl import UserPGRepository


def get_user_repository(session: Annotated[AsyncSession, Depends(get_database_session)]) -> UserRepositoryInterface:
    """Get the User repository instance.

    Args:
        session (AsyncSession, optional): An optional AsyncSession instance.
            If not provided, a new one will be created. Defaults to Depends(get_database_session).


    Returns:
        UserPGRepository: The User repository instance.

    """
    return UserPGRepository(session=session)


def get_group_member_repository(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> GroupMemberRepositoryInterface:
    """Get the GroupMember repository instance.

    Args:
        session (AsyncSession, optional): An optional AsyncSession instance.
            If not provided, a new one will be created. Defaults to Depends(get_database_session).

    Returns:
        GroupMemberPGRepository: The GroupMember repository instance.

    """
    return GroupMemberPGRepository(db_session=session)


def get_group_repository(session: Annotated[AsyncSession, Depends(get_database_session)]) -> GroupRepositoryInterface:
    """Get the Group repository instance.

    Args:
        session (AsyncSession, optional): An optional AsyncSession instance.
            If not provided, a new one will be created. Defaults to Depends(get_database_session).

    Returns:
        GroupPGRepository: The Group repository instance.

    """
    return GroupPGRepository(session=session)


def get_expense_repository(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> ExpenseRepositoryInterface:
    """Get the Expense repository instance.

    Args:
        session (AsyncSession, optional): An optional AsyncSession instance.
            If not provided, a new one will be created. Defaults to Depends(get_database_session).

    Returns:
        ExpensePGRepository: The Expense repository instance.

    """
    return ExpensePGRepository(session=session)


def get_expense_participant_repository(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> ExpenseParticipantRepositoryInterface:
    """Get the ExpenseParticipant repository instance.

    Args:
        session (AsyncSession, optional): An optional AsyncSession instance.
            If not provided, a new one will be created. Defaults to Depends(get_database_session).

    Returns:
        ExpenseParticipantPGRepository: The ExpenseParticipant repository instance.

    """
    return ExpenseParticipantsPGRepository(session=session)

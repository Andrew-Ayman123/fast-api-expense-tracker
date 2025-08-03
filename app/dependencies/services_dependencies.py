# mypy: disable-error-code=arg-type

"""Dependency for repositories, providing access to the User repository."""
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.dependencies.repos_dependencies import get_user_repository
from app.dependencies.settings_dependencies import get_env_settings
from app.repositories.interfaces.user_repository_interface import UserRepositoryInterface
from app.services.expense_service import ExpenseService
from app.services.group_service import GroupService
from app.services.jwt_service import JWTService
from app.services.user_service import UserService


def get_group_service() -> GroupService:
    """Get the Group service instance.

    Note: This is a placeholder implementation. In a complete implementation,
    you would inject the required repository interfaces.

    Returns:
        GroupService: The Group service instance.

    """
    return GroupService(
        group_repository=None,
        group_member_repository=None,
        user_repository=None,
    )


def get_expense_service() -> ExpenseService:
    """Get the Expense service instance.

    Note: This is a placeholder implementation. In a complete implementation,
    you would inject the required repository interfaces.

    Returns:
        ExpenseService: The Expense service instance.

    """
    # Placeholder - in real implementation, inject repositories
    return ExpenseService(
        expense_repository=None,
        group_service=None,
        user_repository=None,
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

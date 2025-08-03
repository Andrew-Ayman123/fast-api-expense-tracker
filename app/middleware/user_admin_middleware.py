"""User Admin Middleware for FastAPI.

This middleware checks if the authenticated user has admin role in a specific group.
"""
import uuid
from typing import Annotated

from fastapi import Depends, Request

from app.dependencies.services_dependencies import get_group_service
from app.exceptions.user_exception import UserNotAuthorizedError
from app.middleware.jwt_auth_middleware import get_current_user_id
from app.services.group_service import GroupService
from app.utils.create_exception_util import create_http_exception
from app.utils.get_path_id_util import get_id_from_path


async def verify_user_admin_role(
    request: Request,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    group_service: Annotated[GroupService, Depends(get_group_service)],
) -> None:
    """Verify that the current user has admin role in the specified group.

    Args:
        request: The FastAPI request object
        current_user_id: The authenticated user's ID from JWT token
        group_service: The group service for checking user roles

    Raises:
        HTTPException: If user is not admin of the group or group doesn't exist

    """
    group_id = await get_id_from_path(request, "group_id")

    # Check if user has admin role in the group
    try:
        # Get user role in group instead of using private method
        is_user_admin_of_group = await group_service.is_user_admin_of_group(current_user_id, group_id)
        if not is_user_admin_of_group:
            raise UserNotAuthorizedError(current_user_id)  # noqa: TRY301
    except Exception as e:
        raise create_http_exception(
            message="User is not an admin of this group",
            status_code=403,
            details={"error": str(e)},
        ) from e

"""User Admin Middleware for FastAPI.

This middleware checks if the authenticated user has admin role in a specific group.
"""

import uuid
from typing import Annotated

from fastapi import Depends

from app.dependencies.services_dependencies import get_group_service
from app.exceptions.application_exception import ApplicationError
from app.middleware.middleware_dependencies import get_current_user_id
from app.services.group_service import GroupService
from app.utils.create_exception_util import create_http_exception


async def verify_user_admin_role(
    group_id: uuid.UUID,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    group_service: Annotated[GroupService, Depends(get_group_service)],
) -> None:
    """Verify that the current user has admin role in the specified group.

    Args:
        group_id: The ID of the group
        current_user_id: The authenticated user's ID from JWT token
        group_service: The group service for checking user roles

    Raises:
        HTTPException: If user is not admin of the group or group doesn't exist

    """
    # Get group and check if it exists
    try:
        group = await group_service.get_group_by_id(group_id, current_user_id)
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        raise create_http_exception(
            message="An error occurred while verifying user admin role",
            status_code=500,
            details={"error": str(e)},
        ) from e

    if not group:
        raise create_http_exception(
            message="Group not found",
            status_code=404,
            details={"group_id": str(group_id)},
        )

    # Check if user has admin role in the group
    try:
        is_user_admin_of_group = await group_service.is_user_admin_of_group(current_user_id, group_id)
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        raise create_http_exception(
            message="An error occurred while verifying user admin role",
            status_code=500,
            details={"error": str(e)},
        ) from e

    if not is_user_admin_of_group:
        raise create_http_exception(
            message="User is not an admin of this group",
            status_code=403,
            details={"user_id": str(current_user_id), "group_id": str(group_id)},
        )

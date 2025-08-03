"""FastAPI Group API Controller."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.dependencies.services_dependencies import get_group_service
from app.exceptions.group_exception import (
    GroupMemberAlreadyExistsError,
    GroupMemberNotFoundError,
    GroupNotFoundError,
)
from app.exceptions.user_exception import UserIDNotFoundError, UserNotAuthorizedError
from app.middleware.jwt_auth_middleware import get_current_user_id
from app.middleware.user_admin_middleware import verify_user_admin_role
from app.models.group_model import GroupModel
from app.schemas.group_schema import (
    GroupCreateData,
    GroupCreateRequest,
    GroupCreateResponse,
    GroupData,
    GroupDetailData,
    GroupDetailResponse,
    GroupListData,
    GroupListResponse,
    GroupMemberAddData,
    GroupMemberAddRequest,
    GroupMemberAddResponse,
    GroupMemberData,
    GroupMemberRoleUpdateRequest,
    GroupMembersListData,
    GroupMembersListResponse,
    GroupUpdateRequest,
    GroupUpdateResponse,
    PaginationData,
)
from app.services.group_service import GroupService
from app.utils.create_exception_util import create_http_exception
from app.utils.get_path_id_util import get_id_from_path
from app.utils.logger_util import get_logger

# versioning is handled in the main file
router = APIRouter(prefix="/groups", tags=["groups"])


def _convert_group_to_data(group: GroupModel) -> GroupData:
    """Convert GroupModel to GroupData schema using from_attributes."""
    return GroupData.model_validate(group, from_attributes=True)


@router.post("")
async def create_group(
    group_data: GroupCreateRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    group_service: Annotated[GroupService, Depends(get_group_service)],
) -> GroupCreateResponse:
    """Create a new expense group.

    Args:
        group_data (GroupCreateRequest): The data for creating a new group.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        group_service (GroupService): The group service instance.

    Returns:
        GroupCreateResponse: The group response wrapped in data field.

    Raises:
        400 Bad Request: If there is an error during group creation.
        401 Unauthorized: If the JWT token is invalid or expired.

    """
    try:
        group, member_count, user_role = await group_service.create_group(group_data, current_user_id)

        group_dict = group.__dict__.copy()
        group_dict["user_role"] = user_role
        group_dict["member_count"] = member_count
        group_data_obj = GroupData.model_validate(group_dict, from_attributes=True)
        create_data = GroupCreateData(group=group_data_obj)
        return GroupCreateResponse(data=create_data)
    except Exception as e:
        get_logger().error("Error creating group: %s", str(e))
        raise create_http_exception(
            message="Failed to create group",
            status_code=400,
            details={"error": str(e)},
        ) from e


@router.get("")
async def list_groups(
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    group_service: Annotated[GroupService, Depends(get_group_service)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> GroupListResponse:
    """List all groups for the authenticated user.

    Args:
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        group_service (GroupService): The group service instance.
        page (int): Page number for pagination.
        limit (int): Items per page for pagination.

    Returns:
        GroupListResponse: The list of groups with pagination wrapped in data field.

    Raises:
        400 Bad Request: If there is an error retrieving groups.
        401 Unauthorized: If the JWT token is invalid or expired.

    """
    try:
        groups, total = await group_service.get_user_groups(current_user_id, page, limit)

        # Convert groups to schema objects with user roles
        groups_data = []
        for group, member_count, user_role in groups:
            group_dict = group.__dict__.copy()
            group_dict["user_role"] = user_role
            group_dict["member_count"] = member_count
            group_data = GroupData.model_validate(group_dict, from_attributes=True)
            groups_data.append(group_data)

        # Calculate pagination
        total_pages = (total + limit - 1) // limit
        pagination = PaginationData(page=page, limit=limit, total=total, pages=total_pages)

        list_data = GroupListData(groups=groups_data, pagination=pagination)
        return GroupListResponse(data=list_data)
    except Exception as e:
        get_logger().error("Error retrieving groups: %s", str(e))
        raise create_http_exception(
            message="Failed to retrieve groups",
            status_code=400,
            details={"error": str(e)},
        ) from e


@router.get("/{group_id}")
async def get_group(
    request: Request,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    group_service: Annotated[GroupService, Depends(get_group_service)],
) -> GroupDetailResponse:
    """Get detailed information about a specific group.

    Args:
        request (Request): The FastAPI request object.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        group_service (GroupService): The group service instance.

    Returns:
        GroupDetailResponse: The group detail response wrapped in data field.

    Raises:
        400 Bad Request: If there is an error retrieving the group.
        401 Unauthorized: If the JWT token is invalid or expired.
        403 Forbidden: If the user is not a member of this group.
        404 Not Found: If the group is not found.

    """
    try:
        group_id = await get_id_from_path(request, "group_id")
        group, member_count, user_role = await group_service.get_group_by_id(group_id, current_user_id)

        # Convert to schema with user role
        group_dict = group.__dict__.copy()
        group_dict["user_role"] = user_role
        group_dict["member_count"] = member_count
        group_data = GroupData.model_validate(group_dict, from_attributes=True)

        detail_data = GroupDetailData(group=group_data)
        return GroupDetailResponse(data=detail_data)
    except GroupNotFoundError as e:
        raise create_http_exception(
            message="Group not found",
            status_code=404,
            details={"group_id": str(group_id)},
        ) from e
    except UserNotAuthorizedError as e:
        raise create_http_exception(
            message="User is not a member of this group",
            status_code=403,
            details={"error": str(e)},
        ) from e
    except Exception as e:
        get_logger().error("Error retrieving group: %s", str(e))
        raise create_http_exception(
            message="Failed to retrieve group",
            status_code=400,
            details={"error": str(e)},
        ) from e


@router.put("/{group_id}")
async def update_group(
    request: Request,
    group_data: GroupUpdateRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    group_service: Annotated[GroupService, Depends(get_group_service)],
    _: Annotated[None, Depends(verify_user_admin_role)],
) -> GroupUpdateResponse:
    """Update group information.

    Args:
        request (Request): The FastAPI request object.
        group_data (GroupUpdateRequest): The data for updating the group.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        group_service (GroupService): The group service instance.
        _ : User admin role verification dependency.

    Returns:
        GroupUpdateResponse: The updated group response wrapped in data field.

    Raises:
        400 Bad Request: If there is an error during group update.
        401 Unauthorized: If the JWT token is invalid or expired.
        403 Forbidden: If the user is not an admin of this group.
        404 Not Found: If the group is not found.

    """
    try:
        group_id = await get_id_from_path(request, "group_id")
        group, member_count, user_role = await group_service.update_group(group_id, group_data, current_user_id)

        group_dict = group.__dict__.copy()
        group_dict["user_role"] = user_role
        group_dict["member_count"] = member_count
        updated_group_data = GroupData.model_validate(group_dict, from_attributes=True)

        update_data = GroupCreateData(group=updated_group_data)

        return GroupUpdateResponse(data=update_data)
    except GroupNotFoundError as e:
        raise create_http_exception(
            message="Group not found",
            status_code=404,
            details={"group_id": str(group_id)},
        ) from e
    except UserNotAuthorizedError as e:
        raise create_http_exception(
            message="Only group admin can update group",
            status_code=403,
            details={"error": str(e)},
        ) from e
    except Exception as e:
        get_logger().error("Error updating group: %s", str(e))
        raise create_http_exception(
            message="Failed to update group",
            status_code=400,
            details={"error": str(e)},
        ) from e


@router.get("/{group_id}/members")
async def list_group_members(
    request: Request,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    group_service: Annotated[GroupService, Depends(get_group_service)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> GroupMembersListResponse:
    """Get paginated list of group members.

    Args:
        request (Request): The FastAPI request object.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        group_service (GroupService): The group service instance.
        page (int): Page number for pagination.
        limit (int): Items per page for pagination.

    Returns:
        GroupMembersListResponse: The list of group members with pagination wrapped in data field.

    Raises:
        400 Bad Request: If there is an error retrieving group members.
        401 Unauthorized: If the JWT token is invalid or expired.
        403 Forbidden: If the user is not a member of this group.
        404 Not Found: If the group is not found.

    """
    try:
        group_id = await get_id_from_path(request, "group_id")
        members_user_roles, members_roles, total = await group_service.get_group_members(
            group_id,
            current_user_id,
            page,
            limit,
        )

        members_data = []
        # Convert members to schema objects
        for user_role, role in zip(members_user_roles, members_roles, strict=True):
            member_dict = user_role.__dict__.copy()
            member_dict["role"] = role
            members_data.append(GroupMemberData.model_validate(member_dict, from_attributes=True))

        # Calculate pagination
        total_pages = (total + limit - 1) // limit
        pagination = PaginationData(page=page, limit=limit, total=total, pages=total_pages)

        list_data = GroupMembersListData(members=members_data, pagination=pagination)
        return GroupMembersListResponse(data=list_data)
    except GroupNotFoundError as e:
        raise create_http_exception(
            message="Group not found",
            status_code=404,
            details={"group_id": str(group_id)},
        ) from e
    except UserNotAuthorizedError as e:
        raise create_http_exception(
            message="User is not a member of this group",
            status_code=403,
            details={"error": str(e)},
        ) from e
    except Exception as e:
        get_logger().error("Error retrieving group members: %s", str(e))
        raise create_http_exception(
            message="Failed to retrieve group members",
            status_code=400,
            details={"error": str(e)},
        ) from e


@router.post("/{group_id}/members")
async def add_group_member(
    request: Request,
    member_data: GroupMemberAddRequest,
    group_service: Annotated[GroupService, Depends(get_group_service)],
    _: Annotated[None, Depends(verify_user_admin_role)],
) -> GroupMemberAddResponse:
    """Add a new member to the group.

    Args:
        request (Request): The FastAPI request object.
        member_data (GroupMemberAddRequest): The data for adding a new member.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        group_service (GroupService): The group service instance.
        _ : User admin role verification dependency.

    Returns:
        GroupMemberAddResponse: The added member response wrapped in data field.

    Raises:
        400 Bad Request: If the email is invalid or user already in group.
        401 Unauthorized: If the JWT token is invalid or expired.
        403 Forbidden: If the user is not an admin of this group.
        404 Not Found: If the group or user is not found.

    """
    try:
        group_id = await get_id_from_path(request, "group_id")
        member, role = await group_service.add_member(group_id, member_data)
        member_dict = member.__dict__.copy()
        member_dict["role"] = role
        member_data_obj = GroupMemberData.model_validate(member_dict, from_attributes=True)
        add_data = GroupMemberAddData(member=member_data_obj)

        return GroupMemberAddResponse(data=add_data)
    except GroupNotFoundError as e:
        raise create_http_exception(
            message="Group not found",
            status_code=404,
            details={"group_id": str(group_id)},
        ) from e
    except UserIDNotFoundError as e:
        raise create_http_exception(
            message="User not found",
            status_code=404,
            details={"error": str(e)},
        ) from e
    except GroupMemberAlreadyExistsError as e:
        raise create_http_exception(
            message="User already in group",
            status_code=400,
            details={"error": str(e)},
        ) from e
    except UserNotAuthorizedError as e:
        raise create_http_exception(
            message="Only group admin can add members",
            status_code=403,
            details={"error": str(e)},
        ) from e
    except Exception as e:
        get_logger().error("Error adding group member: %s", str(e))
        raise create_http_exception(
            message="Failed to add group member",
            status_code=400,
            details={"error": str(e)},
        ) from e


@router.put("/{group_id}/members/{user_id}/role")
async def update_member_role(
    request: Request,
    role_data: GroupMemberRoleUpdateRequest,
    group_service: Annotated[GroupService, Depends(get_group_service)],
    _: Annotated[None, Depends(verify_user_admin_role)],
) -> dict:
    """Update a member's role in a group.

    Args:
        request (Request): The FastAPI request object.
        role_data (GroupMemberRoleUpdateRequest): The new role data.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        group_service (GroupService): The group service instance.
        _ : User admin role verification dependency.

    Returns:
        dict: Success message.

    Raises:
        400 Bad Request: If there is an error during role update.
        401 Unauthorized: If the JWT token is invalid or expired.
        403 Forbidden: If the user is not an admin of this group.
        404 Not Found: If the group or member is not found.

    """
    try:
        group_id = await get_id_from_path(request, "group_id")
        member_user_id = await get_id_from_path(request, "user_id")

        await group_service.update_member_role(group_id, member_user_id, role_data.role)
    except GroupNotFoundError as e:
        raise create_http_exception(
            message="Group not found",
            status_code=404,
            details={"group_id": str(group_id)},
        ) from e
    except GroupMemberNotFoundError as e:
        raise create_http_exception(
            message="Member not found in group",
            status_code=404,
            details={"error": str(e)},
        ) from e
    except UserNotAuthorizedError as e:
        raise create_http_exception(
            message="Only group admin can update member roles",
            status_code=403,
            details={"error": str(e)},
        ) from e
    except Exception as e:
        get_logger().error("Error updating member role: %s", str(e))
        raise create_http_exception(
            message="Failed to update member role",
            status_code=400,
            details={"error": str(e)},
        ) from e
    else:
        return {"message": "Member role updated successfully"}


@router.delete("/{group_id}/members/{user_id}")
async def remove_group_member(
    request: Request,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    group_service: Annotated[GroupService, Depends(get_group_service)],
    _: Annotated[None, Depends(verify_user_admin_role)],
) -> dict:
    """Remove a member from a group.

    Args:
        request (Request): The FastAPI request object.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        group_service (GroupService): The group service instance.
        _ : User admin role verification dependency.

    Returns:
        dict: Success message.

    Raises:
        400 Bad Request: If there is an error during member removal.
        401 Unauthorized: If the JWT token is invalid or expired.
        403 Forbidden: If the user is not an admin of this group.
        404 Not Found: If the group or member is not found.

    """
    try:
        group_id = await get_id_from_path(request, "group_id")
        member_user_id = await get_id_from_path(request, "user_id")

        await group_service.remove_member(group_id, member_user_id, current_user_id)
    except GroupNotFoundError as e:
        raise create_http_exception(
            message="Group not found",
            status_code=404,
            details={"group_id": str(group_id)},
        ) from e
    except GroupMemberNotFoundError as e:
        raise create_http_exception(
            message="Member not found in group",
            status_code=404,
            details={"error": str(e)},
        ) from e
    except UserNotAuthorizedError as e:
        raise create_http_exception(
            message="Only group admin can remove members",
            status_code=403,
            details={"error": str(e)},
        ) from e
    except Exception as e:
        get_logger().error("Error removing group member: %s", str(e))
        raise create_http_exception(
            message="Failed to remove group member",
            status_code=400,
            details={"error": str(e)},
        ) from e
    else:
        return {"message": "Member removed successfully"}


@router.delete("/{group_id}")
async def delete_group(
    request: Request,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    group_service: Annotated[GroupService, Depends(get_group_service)],
    _: Annotated[None, Depends(verify_user_admin_role)],
) -> dict:
    """Delete a group (only allowed by admin).

    Args:
        request (Request): The FastAPI request object.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        group_service (GroupService): The group service instance.
        _ : User admin role verification dependency.

    Returns:
        dict: Success message.

    Raises:
        400 Bad Request: If there is an error during group deletion.
        401 Unauthorized: If the JWT token is invalid or expired.
        403 Forbidden: If the user is not an admin of this group.
        404 Not Found: If the group is not found.

    """
    try:
        group_id = await get_id_from_path(request, "group_id")
        await group_service.delete_group(group_id, current_user_id)
    except GroupNotFoundError as e:
        raise create_http_exception(
            message="Group not found",
            status_code=404,
            details={"group_id": str(group_id)},
        ) from e
    except UserNotAuthorizedError as e:
        raise create_http_exception(
            message="Only group admin can delete group",
            status_code=403,
            details={"error": str(e)},
        ) from e
    except Exception as e:
        get_logger().error("Error deleting group: %s", str(e))
        raise create_http_exception(
            message="Failed to delete group",
            status_code=400,
            details={"error": str(e)},
        ) from e
    else:
        return {"message": "Group deleted successfully"}

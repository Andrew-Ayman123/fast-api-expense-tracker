"""FastAPI Expense API Controller."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.services_dependencies import get_expense_service
from app.exceptions.application_exception import ApplicationError
from app.middleware.jwt_auth_middleware import get_current_user_id
from app.middleware.user_admin_middleware import verify_user_admin_role
from app.schemas.expense_schema import (
    ExpenseCreateData,
    ExpenseCreateRequest,
    ExpenseCreateResponse,
    ExpenseCreateResponseData,
    ExpenseDetailData,
    ExpenseDetailResponse,
    ExpenseDetailResponseData,
    ExpenseListData,
    ExpenseListItemData,
    ExpenseListResponse,
    ExpenseParticipantData,
    ExpensePayerData,
    ExpenseUpdateData,
    ExpenseUpdateRequest,
    ExpenseUpdateResponse,
    PaginationData,
)
from app.services.expense_service import ExpenseService
from app.utils.create_exception_util import create_http_exception
from app.utils.logger_util import get_logger

# versioning is handled in the main file
router = APIRouter(prefix="/groups/{group_id}/expenses", tags=["expenses"])


@router.post("")
async def create_expense(
    group_id: uuid.UUID,
    expense_data: ExpenseCreateRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    expense_service: Annotated[ExpenseService, Depends(get_expense_service)],
    _: Annotated[None, Depends(verify_user_admin_role)],
) -> ExpenseCreateResponse:
    """Create a new expense in a group.

    Args:
        group_id (uuid.UUID): The ID of the group where the expense is created.
        expense_data (ExpenseCreateRequest): The data for creating a new expense.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        expense_service (ExpenseService): The expense service instance.

    Returns:
        ExpenseCreateResponse: The expense response wrapped in data field.

    Raises:
        400 Bad Request: If there is an error during expense creation.
        401 Unauthorized: If the JWT token is invalid or expired.
        403 Forbidden: If the user is not a member of this group.

    """
    try:
        expense, payer, participants = await expense_service.create_expense(group_id, expense_data, current_user_id)

        # Convert expense to schema
        expense_dict = expense.__dict__.copy()
        expense_dict["participants"] = participants
        expense_dict["payer"] = payer
        expense_create_data = ExpenseCreateData.model_validate(expense_dict, from_attributes=True)

        create_response_data = ExpenseCreateResponseData(expense=expense_create_data)
        return ExpenseCreateResponse(data=create_response_data)
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        get_logger().error("Error creating expense: %s", str(e))
        raise create_http_exception(
            message="Failed to create expense",
            status_code=500,
            details={"error": str(e)},
        ) from e


@router.get("")
async def list_expenses(
    group_id: uuid.UUID,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    expense_service: Annotated[ExpenseService, Depends(get_expense_service)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
) -> ExpenseListResponse:
    """List expenses in a group with filtering options.

    Args:
        group_id (uuid.UUID): The ID of the group to list expenses for.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        expense_service (ExpenseService): The expense service instance.
        page (int): Page number for pagination.
        limit (int): Items per page for pagination.

    Returns:
        ExpenseListResponse: The list of expenses with pagination wrapped in data field.

    Raises:
        400 Bad Request: If there is an error retrieving expenses.
        401 Unauthorized: If the JWT token is invalid or expired.
        403 Forbidden: If the user is not a member of this group.

    """
    try:
        expenses_with_data, total = await expense_service.get_expenses_by_group(group_id, current_user_id, page, limit)

        # Convert expenses to schema objects
        expenses_data = []
        for expense,payer, participants in expenses_with_data:
            expense_dict = expense.__dict__.copy()
            expense_dict["participants"] = participants
            expense_dict["payer"] = payer
            expense_item = ExpenseListItemData.model_validate(expense_dict, from_attributes=True)
            expenses_data.append(expense_item)

        # Calculate pagination
        total_pages = (total + limit - 1) // limit
        pagination = PaginationData(page=page, limit=limit, total=total, pages=total_pages)

        list_data = ExpenseListData(expenses=expenses_data, pagination=pagination)
        return ExpenseListResponse(data=list_data)
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        get_logger().error("Error retrieving expenses: %s", str(e))
        raise create_http_exception(
            message="Failed to retrieve expenses",
            status_code=500,
            details={"error": str(e)},
        ) from e


@router.get("/{expense_id}")
async def get_expense(
    group_id: uuid.UUID,  # noqa: ARG001
    expense_id: uuid.UUID,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    expense_service: Annotated[ExpenseService, Depends(get_expense_service)],
) -> ExpenseDetailResponse:
    """Get detailed information about a specific expense.

    Args:
        group_id (uuid.UUID): The ID of the group where the expense belongs.
        expense_id (uuid.UUID): The ID of the expense to retrieve.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        expense_service (ExpenseService): The expense service instance.

    Returns:
        ExpenseDetailResponse: The expense detail response wrapped in data field.

    Raises:
        400 Bad Request: If there is an error retrieving the expense.
        401 Unauthorized: If the JWT token is invalid or expired.
        403 Forbidden: If the user is not a member of this group.
        404 Not Found: If the expense is not found.

    """
    try:
        expense, participants, payer, group_name = await expense_service.get_expense_by_id(expense_id, current_user_id)

        # Convert participants and payer to schema
        participants_data = [
            ExpenseParticipantData.model_validate(participant, from_attributes=True) for participant in participants
        ]
        payer_data = ExpensePayerData.model_validate(payer, from_attributes=True)

        # Convert expense to schema
        expense_dict = expense.__dict__.copy()
        expense_dict["participants"] = participants_data
        expense_dict["payer"] = payer_data
        expense_dict["group_name"] = group_name
        expense_detail = ExpenseDetailData.model_validate(expense_dict, from_attributes=True)

        detail_response_data = ExpenseDetailResponseData(expense=expense_detail)
        return ExpenseDetailResponse(data=detail_response_data)
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        get_logger().error("Error retrieving expense: %s", str(e))
        raise create_http_exception(
            message="Failed to retrieve expense",
            status_code=500,
            details={"error": str(e)},
        ) from e


@router.put("/{expense_id}")
async def update_expense(
    group_id: uuid.UUID,  # noqa: ARG001
    expense_id: uuid.UUID,
    expense_data: ExpenseUpdateRequest,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    expense_service: Annotated[ExpenseService, Depends(get_expense_service)],
    _: Annotated[None, Depends(verify_user_admin_role)],
) -> ExpenseUpdateResponse:
    """Update an existing expense.

    Args:
        group_id (uuid.UUID): The ID of the group where the expense belongs.
        expense_id (uuid.UUID): The ID of the expense to update.
        expense_data (ExpenseUpdateRequest): The data for updating the expense.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        expense_service (ExpenseService): The expense service instance.

    Returns:
        ExpenseUpdateResponse: The updated expense response wrapped in data field.

    Raises:
        400 Bad Request: If there is an error during expense update.
        401 Unauthorized: If the JWT token is invalid or expired.
        403 Forbidden: If the user is not a member of this group.
        404 Not Found: If the expense is not found.

    """
    try:
        expense, payer, participants = await expense_service.update_expense(expense_id, expense_data, current_user_id)

        # Convert expense to schema
        expense_dict = expense.__dict__.copy()
        expense_dict["participants"] = participants
        expense_dict["payer"] = payer
        updated_expense_data = ExpenseCreateData.model_validate(expense_dict, from_attributes=True)

        update_data = ExpenseUpdateData(expense=updated_expense_data)
        return ExpenseUpdateResponse(data=update_data)
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        get_logger().error("Error updating expense: %s", str(e))
        raise create_http_exception(
            message="Failed to update expense",
            status_code=500,
            details={"error": str(e)},
        ) from e


@router.delete("/{expense_id}", status_code=204)
async def delete_expense(
    group_id: uuid.UUID,  # noqa: ARG001
    expense_id: uuid.UUID,
    expense_service: Annotated[ExpenseService, Depends(get_expense_service)],
    _: Annotated[None, Depends(verify_user_admin_role)],
) -> None:
    """Delete an expense.

    Args:
        group_id (uuid.UUID): The ID of the group where the expense belongs.
        expense_id (uuid.UUID): The ID of the expense to delete.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        expense_service (ExpenseService): The expense service instance.

    Raises:
        400 Bad Request: If there is an error during expense deletion.
        401 Unauthorized: If the JWT token is invalid or expired.
        403 Forbidden: If the user is not a member of this group.
        404 Not Found: If the expense is not found.

    """
    try:
        await expense_service.delete_expense(expense_id)
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        get_logger().error("Error deleting expense: %s", str(e))
        raise create_http_exception(
            message="Failed to delete expense",
            status_code=500,
            details={"error": str(e)},
        ) from e

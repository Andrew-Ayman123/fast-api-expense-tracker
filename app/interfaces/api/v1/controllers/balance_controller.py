"""Controller for handling user balance in group expenses."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.dependencies.services_dependencies import get_expense_service
from app.exceptions.application_exception import ApplicationError
from app.middleware.jwt_auth_middleware import get_current_user_id
from app.schemas.expense_schema import (
    UserBalanceResponse,
)
from app.services.expense_service import ExpenseService
from app.utils.create_exception_util import create_http_exception
from app.utils.get_path_id_util import get_id_from_path
from app.utils.logger_util import get_logger

# versioning is handled in the main file
router = APIRouter(prefix="/groups/{group_id}/members/{user_id}", tags=["Group Expenses Balance"])

@router.get("/balance")
async def get_user_balance(
    request: Request,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    expense_service: Annotated[ExpenseService, Depends(get_expense_service)],
) -> UserBalanceResponse:
    """Get a user's balance in a group.

    Args:
        request (Request): The FastAPI request object.
        current_user_id (uuid.UUID): The authenticated user's ID from JWT token.
        expense_service (ExpenseService): The expense service instance.

    Returns:
        UserBalanceResponse: The user balance response wrapped in data field.

    Raises:
        400 Bad Request: If there is an error retrieving the balance.
        401 Unauthorized: If the JWT token is invalid or expired.
        403 Forbidden: If the user is not a member of this group.
        404 Not Found: If the group or user is not found.

    """
    try:
        group_id = await get_id_from_path(request, "group_id")
        target_user_id = await get_id_from_path(request, "user_id")

        balance_data = await expense_service.get_user_balance(group_id, target_user_id, current_user_id)
        return UserBalanceResponse(data=balance_data)
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        get_logger().error("Error retrieving user balance: %s", str(e))
        raise create_http_exception(
            message="Failed to retrieve user balance",
            status_code=500,
            details={"error": str(e)},
        ) from e

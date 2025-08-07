"""Sync service for the expense tracker application."""

from collections.abc import Awaitable, Callable
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.schemas.expense_schema import ExpenseCreateRequest, ExpenseUpdateRequest
from app.schemas.group_schema import GroupCreateRequest, GroupUpdateRequest
from app.schemas.sync_schema import (
    SyncBulkRequest,
    SyncChangeData,
    SyncExpenseCreateData,
    SyncExpenseUpdateData,
    SyncGroupCreateData,
    SyncGroupUpdateData,
)
from app.services.expense_service import ExpenseService
from app.services.group_service import GroupService


class SyncService:
    """Service for handling synchronization operations."""

    def __init__(self, services_generator: Callable[[], Awaitable[tuple[GroupService, ExpenseService]]]) -> None:
        """Initialize the SyncService with a callable to get Group and Expense services."""
        self.services_generator = services_generator
        self.group_service: GroupService
        self.expense_service: ExpenseService

    async def _handle_create_expense(
        self,
        change: SyncChangeData,
        current_user_id: UUID,
    ) -> str:
        """Handle creation of an expense."""
        if change.data is None:
            return "Failed: create expense: missing data"
        entity_data = SyncExpenseCreateData.model_validate(change.data.model_dump())

        # Check if the group exists before creating expense
        try:
            await self.group_service.get_group_by_id(entity_data.group_id, current_user_id)
        except Exception:  # noqa: BLE001
            return f"Failed: create expense: group {entity_data.group_id} not found or not accessible"

        try:
            expense = await self.expense_service.create_expense(
                group_id=entity_data.group_id,
                expense_data=ExpenseCreateRequest.model_validate(entity_data.model_dump()),
                current_user_id=current_user_id,
                expense_id=change.entity_id,
                created_at=change.timestamp,  # Use change timestamp as creation time
            )
            return f"Success: Expense {expense[0].id} created successfully"
        except IntegrityError:
            return "Failed: create expense: Already Exists"
        except Exception as e:  # noqa: BLE001
            return f"Failed: create expense: {e!s}"

    async def _handle_create_group(
        self,
        change: SyncChangeData,
        current_user_id: UUID,
    ) -> str:
        """Handle creation of a group."""
        if change.data is None:
            return "Failed: create group: missing data"
        entity_data = SyncGroupCreateData.model_validate(change.data.model_dump())

        try:
            group = await self.group_service.create_group(
                group_data=GroupCreateRequest.model_validate(entity_data.model_dump()),
                created_by_id=current_user_id,
                group_id=change.entity_id,
                created_at=change.timestamp,  # Use change timestamp as creation time
            )
            return f"Success: Group {group[0].id} created successfully"
        except IntegrityError:
            return "Failed: create group: Already Exists"
        except Exception as e:  # noqa: BLE001
            return f"Failed: create group: {e!s}"

    async def _handle_update_expense(
        self,
        change: SyncChangeData,
        current_user_id: UUID,
    ) -> str:
        """Handle update of an expense."""
        entity_id = change.entity_id
        if change.data is None:
            return "Failed: update expense: missing data"
        entity_data = SyncExpenseUpdateData.model_validate(change.data.model_dump())
        change_timestamp = change.timestamp

        try:
            # Get current expense to compare timestamps
            current_expense = await self.expense_service.get_expense_by_id(entity_id, current_user_id)

            # Compare timestamps - discard if the change is older than current data
            if current_expense[0].updated_at >= change_timestamp:
                return f"Failed: Expense {entity_id} update discarded (older timestamp)"

            updated_expense = await self.expense_service.update_expense(
                expense_id=entity_id,
                expense_data=ExpenseUpdateRequest.model_validate(entity_data.model_dump()),
                user_id=current_user_id,
                updated_at=change_timestamp,  # Use change timestamp as update time
            )
            return f"Success: Expense {updated_expense[0].id} updated successfully"
        except Exception as e:  # noqa: BLE001
            return f"Failed: update expense {entity_id}: {e!s}"

    async def _handle_update_group(
        self,
        change: SyncChangeData,
        current_user_id: UUID,
    ) -> str:
        """Handle update of a group."""
        entity_id = change.entity_id
        if change.data is None:
            return "Failed: update group: missing data"
        entity_data = SyncGroupUpdateData.model_validate(change.data.model_dump())
        change_timestamp = change.timestamp

        try:
            # Get current group to compare timestamps
            current_group = await self.group_service.get_group_by_id(entity_id, current_user_id)

            # Compare timestamps - discard if the change is older than current data
            if current_group[0].updated_at >= change_timestamp:
                return f"Failed: Group {entity_id} update discarded (older timestamp)"

            updated_group = await self.group_service.update_group(
                group_id=entity_id,
                group_data=GroupUpdateRequest.model_validate(entity_data.model_dump()),
                user_id=current_user_id,
                updated_at=change_timestamp,  # Use change timestamp as update time
            )
            return f"Success: Group {updated_group[0].id} updated successfully"
        except Exception as e:  # noqa: BLE001
            return f"Failed: update group {entity_id}: {e!s}"

    async def _handle_delete_expense(
        self,
        change: SyncChangeData,
        current_user_id: UUID,
    ) -> str:
        """Handle deletion of an expense."""
        entity_id = change.entity_id

        try:
            # Check if expense exists before deletion
            await self.expense_service.get_expense_by_id(entity_id, current_user_id)
            await self.expense_service.delete_expense(entity_id)
        except Exception:  # noqa: BLE001
            return f"Failed: Expense {entity_id} could not be found or might be deleted before"
        else:
            return f"Success: Expense {entity_id} deleted successfully"

    async def _handle_delete_group(
        self,
        change: SyncChangeData,
        current_user_id: UUID,
    ) -> str:
        """Handle deletion of a group."""
        entity_id = change.entity_id

        try:
            # Check if group exists before deletion
            await self.group_service.get_group_by_id(entity_id, current_user_id)
            await self.group_service.delete_group(entity_id, current_user_id)
        except Exception:  # noqa: BLE001
            return f"Failed: Group {entity_id} could not be found or might be deleted before"
        else:
            return f"Success: Group {entity_id} deleted successfully"

    async def handle_bulk_sync(
        self,
        request: SyncBulkRequest,
        current_user_id: UUID,
    ) -> dict:
        """Handle bulk synchronization of data changes."""
        notification_list = []

        for change in request.changes:
            self.group_service, self.expense_service = await self.services_generator()
            if change.type == "create" and change.entity == "expense":
                notification = await self._handle_create_expense(change, current_user_id)
            elif change.type == "create" and change.entity == "group":
                notification = await self._handle_create_group(change, current_user_id)
            elif change.type == "update" and change.entity == "expense":
                notification = await self._handle_update_expense(change, current_user_id)
            elif change.type == "update" and change.entity == "group":
                notification = await self._handle_update_group(change, current_user_id)
            elif change.type == "delete" and change.entity == "expense":
                notification = await self._handle_delete_expense(change, current_user_id)
            elif change.type == "delete" and change.entity == "group":
                notification = await self._handle_delete_group(change, current_user_id)
            else:
                notification = f"Unknown operation type or entity: {change.type} for {change.entity}"

            notification_list.append(notification)

        return {"notifications": notification_list}

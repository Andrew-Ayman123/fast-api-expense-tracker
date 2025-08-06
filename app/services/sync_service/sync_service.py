"""Sync service for the expense tracker application."""

import asyncio
from uuid import UUID

from app.schemas.sync_schema import SyncBulkRequest
from app.services.expense_service import ExpenseService
from app.services.group_service import GroupService


class SyncService:
    """Service for handling synchronization operations."""

    def __init__(
        self,
        expense_service: ExpenseService,
        group_service: GroupService,
    ) -> None:
        """Initialize the SyncService with necessary dependencies."""
        self.expense_service = expense_service
        self.group_service = group_service

    async def handle_bulk_sync(
        self,
        request: SyncBulkRequest,
        current_user_id: UUID,  # noqa: ARG002
    ) -> dict:
        """Handle bulk synchronization of data changes."""
        # simulate delay to see pending, please remove ya MAGDYYYYYYY
        await asyncio.sleep(30)
        notification_list = []

        for change in request.changes:
            change_type = change.type
            entity = change.entity

            if change_type == "create":
                notification_list.append(f"{entity} created")
            elif change_type == "update":
                notification_list.append(f"{entity} updated")
            elif change_type == "delete":
                notification_list.append(f"{entity} deleted")

        return {"notifications": notification_list}

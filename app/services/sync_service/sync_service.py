"""Sync service for the expense tracker application."""

from datetime import UTC, datetime

from app.schemas.sync_schema import SyncBulkResponse
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

    async def handle_bulk_sync(self, request: dict) -> dict:  # noqa: C901
        """Handle bulk synchronization of data changes."""
        operation_id = str(datetime.now(UTC).timestamp())
        nlist = []

        for change in request.get("changes", []):
            if change.get("type") == "create":
                if change.get("entity") == "expense":
                    nlist.append("expense created")
                elif change.get("entity") == "group":
                    nlist.append("group created")
            elif change.get("type") == "update":
                if change.get("entity") == "expense":
                    nlist.append("expense updated")
                elif change.get("entity") == "group":
                    nlist.append("group updated")

            elif change.get("type") == "delete":
                if change.get("entity") == "expense":
                    nlist.append("expense deleted")

                elif change.get("entity") == "group":
                    nlist.append("group deleted")

        return SyncBulkResponse(
            operation_id=operation_id,
            notifications=nlist,
        ).dict()

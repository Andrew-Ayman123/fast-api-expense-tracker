"""Exceptions for group-related operations.

This module defines custom exceptions for group operations such as creation, management, and member operations.
These exceptions can be raised by the GroupService to handle specific error cases.
"""

import uuid


class GroupCreationError(Exception):
    """Exception raised when group creation fails."""

    def __init__(self, message: str = "Failed to create group") -> None:
        """Initialize with a custom message."""
        super().__init__(message)


class GroupNotFoundError(Exception):
    """Exception raised when a group is not found."""

    def __init__(self, group_id: uuid.UUID) -> None:
        """Initialize with the group ID that was not found."""
        self.group_id = group_id
        super().__init__(f"Group with ID {self.group_id} not found.")


class GroupAccessDeniedError(Exception):
    """Exception raised when a user is not authorized to access a group."""

    def __init__(self, user_id: uuid.UUID, group_id: uuid.UUID, action: str = "access") -> None:
        """Initialize with user ID, group ID, and action."""
        self.user_id = user_id
        self.group_id = group_id
        self.action = action
        super().__init__(f"User {self.user_id} is not authorized to {self.action} group {self.group_id}.")


class GroupMemberAlreadyExistsError(Exception):
    """Exception raised when trying to add a user who is already a member."""

    def __init__(self, user_id: uuid.UUID, group_id: uuid.UUID) -> None:
        """Initialize with user ID and group ID."""
        self.user_id = user_id
        self.group_id = group_id
        super().__init__(f"User {self.user_id} is already a member of group {self.group_id}.")


class GroupMemberNotFoundError(Exception):
    """Exception raised when a group member is not found."""

    def __init__(self, user_id: uuid.UUID, group_id: uuid.UUID) -> None:
        """Initialize with user ID and group ID."""
        self.user_id = user_id
        self.group_id = group_id
        super().__init__(f"User {self.user_id} is not a member of group {self.group_id}.")


class GroupAdminRequiredError(Exception):
    """Exception raised when an action requires admin privileges."""

    def __init__(self, user_id: uuid.UUID, group_id: uuid.UUID, action: str) -> None:
        """Initialize with user ID, group ID, and action."""
        self.user_id = user_id
        self.group_id = group_id
        self.action = action
        message = f"Admin privileges required for user {self.user_id} to {self.action} in group {self.group_id}."
        super().__init__(message)


class GroupOwnerCannotLeaveError(Exception):
    """Exception raised when group owner tries to leave the group."""

    def __init__(self, user_id: uuid.UUID, group_id: uuid.UUID) -> None:
        """Initialize with user ID and group ID."""
        self.user_id = user_id
        self.group_id = group_id
        super().__init__(f"Group owner {self.user_id} cannot leave group {self.group_id}. Transfer ownership first.")


class GroupUpdateError(Exception):
    """Exception raised when group update fails."""

    def __init__(self, group_id: uuid.UUID, message: str = "Failed to update group") -> None:
        """Initialize with group ID and custom message."""
        self.group_id = group_id
        super().__init__(f"{message} (Group ID: {self.group_id})")


class GroupDeletionError(Exception):
    """Exception raised when group deletion fails."""

    def __init__(self, group_id: uuid.UUID, message: str = "Failed to delete group") -> None:
        """Initialize with group ID and custom message."""
        self.group_id = group_id
        super().__init__(f"{message} (Group ID: {self.group_id})")

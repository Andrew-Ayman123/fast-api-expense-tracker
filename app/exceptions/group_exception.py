"""Exceptions for group-related operations.

This module defines custom exceptions for group operations such as creation, management, and member operations.
These exceptions can be raised by the GroupService to handle specific error cases.
"""

import uuid

from fastapi import status

from app.exceptions.application_exception import ApplicationError


class GroupCreationError(ApplicationError):
    """Exception raised when group creation fails."""

    def __init__(self, message: str = "Failed to create group") -> None:
        """Initialize with a custom message."""
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class GroupNotFoundError(ApplicationError):
    """Exception raised when a group is not found."""

    def __init__(self, group_id: uuid.UUID) -> None:
        """Initialize with the group ID that was not found."""
        self.group_id = group_id
        message = f"Group with ID {self.group_id} not found."
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)

class GroupMemberNotFoundError(ApplicationError):
    """Exception raised when a group member is not found."""

    def __init__(self, user_id: uuid.UUID, group_id: uuid.UUID) -> None:
        """Initialize with user ID and group ID."""
        self.user_id = user_id
        self.group_id = group_id
        message = f"User {self.user_id} is not a member of group {self.group_id}."
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)

class GroupOwnerCannotLeaveError(ApplicationError):
    """Exception raised when group owner tries to leave the group."""

    def __init__(self, user_id: uuid.UUID, group_id: uuid.UUID) -> None:
        """Initialize with user ID and group ID."""
        self.user_id = user_id
        self.group_id = group_id
        message = f"Group owner {self.user_id} cannot leave group {self.group_id}. Transfer ownership first."
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)

class GroupMemberAddError(ApplicationError):
    """Exception raised when adding a member to a group fails."""

    def __init__(self, email: str, group_id: uuid.UUID, message: str = "Failed to add member") -> None:
        """Initialize with email, group ID and custom message."""
        self.email = email
        self.group_id = group_id
        formatted_message = f"{message} {email} to group {group_id}"
        super().__init__(formatted_message, status_code=status.HTTP_400_BAD_REQUEST)


class GroupMemberRemoveError(ApplicationError):
    """Exception raised when removing a member from a group fails."""

    def __init__(self, user_id: uuid.UUID, group_id: uuid.UUID, message: str = "Failed to remove member") -> None:
        """Initialize with user ID, group ID and custom message."""
        self.user_id = user_id
        self.group_id = group_id
        formatted_message = f"{message} {user_id} from group {group_id}"
        super().__init__(formatted_message, status_code=status.HTTP_400_BAD_REQUEST)


class GroupMemberRoleUpdateError(ApplicationError):
    """Exception raised when updating a member's role fails."""

    def __init__(self, user_id: uuid.UUID, group_id: uuid.UUID, message: str = "Failed to update member role") -> None:
        """Initialize with user ID, group ID and custom message."""
        self.user_id = user_id
        self.group_id = group_id
        formatted_message = f"{message} for user {user_id} in group {group_id}"
        super().__init__(formatted_message, status_code=status.HTTP_400_BAD_REQUEST)

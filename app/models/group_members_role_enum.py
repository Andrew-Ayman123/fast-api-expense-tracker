"""Group members role Enumeration Module."""
import enum


class GroupMembersRoleEnum(enum.Enum):
    """Enumeration for group members roles."""

    ADMIN = "Admin"
    MEMBER = "Member"

    def __str__(self):  # noqa: ANN204, D105
        return self.value

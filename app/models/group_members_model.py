"""Group memebers Module.

Defines the GroupMemberModel for representing group membership in the application.
"""
import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.group_members_role_enum import GroupMembersRoleEnum
from app.models.shared_base_model import Base


class GroupMemberModel(Base):
    """SQLAlchemy Group Member model - represents the group_members table."""

    __tablename__ = "group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user_membership"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )

    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[GroupMembersRoleEnum] = mapped_column(
        Enum(GroupMembersRoleEnum),
        nullable=False,
    )

    user = relationship("UserModel", back_populates="group_membership", passive_deletes=True)
    group = relationship("GroupModel", back_populates="members", passive_deletes=True)


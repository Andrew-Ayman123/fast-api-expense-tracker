"""Group memebers Module.

Defines the GroupMemberModel for representing group membership in the application.
"""
import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.shared_base_model import Base


class ExpenseParticipantModel(Base):
    """Represents a participant in an expense group."""

    __tablename__ = "expense_participants"
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_user_group_participation"),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    group_id: Mapped[UUID] = mapped_column(ForeignKey("groups.id"), nullable=False)


    user = relationship("UserModel", back_populates="expense_participation")
    group = relationship("GroupModel", back_populates="expense_participants")

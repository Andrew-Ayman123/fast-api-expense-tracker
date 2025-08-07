"""Expense Model Module.

Defines the ExpenseModel for managing expense-related data.
"""

import uuid
from datetime import datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.expense_category_enum import ExpenseCategoryEnum as ExpenseCategory
from app.models.shared_base_model import Base


class ExpenseModel(Base):
    """SQLAlchemy Expense model - represents the expenses table."""

    __tablename__ = "expenses"

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

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(Float, nullable=False)

    payer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    category: Mapped[ExpenseCategory] = mapped_column(
        Enum(ExpenseCategory),
        nullable=False,
    )

    date: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    payer = relationship("UserModel", back_populates="expenses_paid")
    group = relationship("GroupModel", back_populates="expenses")
    participants = relationship(
        "ExpenseParticipantModel",
        back_populates="expense",
        passive_deletes=True,
    )

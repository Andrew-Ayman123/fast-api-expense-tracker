"""Expense Category Enumeration Module."""
import enum


class ExpenseCategoryEnum(enum.Enum):
    """Enumeration for expense categories."""

    FOOD = "Food"
    TRANSPORT = "Transport"
    ENTERTAINMENT = "Entertainment"
    UTILITIES = "Utilities"
    HEALTHCARE = "Healthcare"
    OTHER = "Other"

    def __str__(self):  # noqa: ANN204, D105
        return self.value

"""Expense Service Module.

This module defines the ExpenseService class, which provides methods for managing expenses.
It interacts with the ExpenseRepositoryInterface, ExpenseParticipantRepositoryInterface,
and UserRepositoryInterface to perform CRUD operations on expenses and their participants.
"""

import uuid

from sqlalchemy.exc import IntegrityError

from app.exceptions.expense_exception import (
    ExpenseAccessDeniedError,
    ExpenseCreationError,
    ExpenseNotFoundError,
    ExpenseParticipantNotInGroupError,
    ExpenseParticipantRetrievalError,
    ExpenseParticipantsEmptyError,
    ExpensePayerNotInGroupError,
    ExpenseUpdateError,
)
from app.exceptions.group_exception import GroupMemberNotFoundError, GroupNotAuthorizedError
from app.models import ExpenseCategoryEnum, ExpenseModel, UserModel
from app.repositories.interfaces.expense_participants_interface import ExpenseParticipantRepositoryInterface
from app.repositories.interfaces.expense_repository_interface import ExpenseRepositoryInterface
from app.repositories.interfaces.user_repository_interface import UserRepositoryInterface
from app.schemas.expense_schema import (
    ExpenseCreateRequest,
    ExpenseUpdateRequest,
    UserBalanceResponseData,
)
from app.services.group_service import GroupService


class ExpenseService:
    """Service class for managing expenses and their participants."""

    def __init__(
        self,
        expense_repository: ExpenseRepositoryInterface,
        expense_participant_repository: ExpenseParticipantRepositoryInterface,
        group_service: GroupService,
        user_repository: UserRepositoryInterface,
    ) -> None:
        """Initialize the ExpenseService with repository instances."""
        self.expense_repository = expense_repository
        self.expense_participant_repository = expense_participant_repository
        self.group_service = group_service
        self.user_repository = user_repository

    async def _validate_user_group_access(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
        action: str,
    ) -> None:
        """Validate that a user has access to a group for a specific action."""
        if not await self.group_service.is_user_member_of_group(user_id, group_id):
            raise ExpenseAccessDeniedError(user_id, group_id, action)

    async def _validate_payer_in_group(self, payer_id: uuid.UUID, group_id: uuid.UUID) -> None:
        """Validate that the payer is a member of the group."""
        if not await self.group_service.is_user_member_of_group(payer_id, group_id):
            raise ExpensePayerNotInGroupError(payer_id, group_id)

    async def _validate_participants_in_group(
        self,
        participant_ids: list[uuid.UUID],
        group_id: uuid.UUID,
    ) -> None:
        """Validate that all participants are members of the group."""
        for participant_id in participant_ids:
            if not await self.group_service.is_user_member_of_group(participant_id, group_id):
                raise ExpenseParticipantNotInGroupError(participant_id, group_id)

    def _manage_participant_list(
        self,
        participants_id: list[uuid.UUID],
        payer_id: uuid.UUID,
        *,
        is_payer_included: bool,
    ) -> list[uuid.UUID]:
        """Manage the participant list based on payer inclusion preference."""
        participants = participants_id.copy()

        if is_payer_included:
            if payer_id not in participants:
                participants.append(payer_id)
        else:
            if payer_id in participants:
                participants.remove(payer_id)
            if not participants:
                raise ExpenseParticipantsEmptyError

        return participants

    async def _get_payer_and_participants_models(
        self,
        payer_id: uuid.UUID,
        participant_ids: list[uuid.UUID],
        group_id: uuid.UUID,
    ) -> tuple[UserModel, list[UserModel]]:
        """Get payer and participant user models."""
        # Get payer user model
        payer_user_model = await self.user_repository.get_user_by_id(payer_id)
        if not payer_user_model:
            raise ExpensePayerNotInGroupError(payer_id, group_id)

        # Get participant user models
        participant_users = await self.user_repository.get_many_users_by_ids(participant_ids)
        if not participant_users:
            raise ExpenseParticipantRetrievalError

        return payer_user_model, participant_users

    async def _get_expense_or_raise(self, expense_id: uuid.UUID) -> ExpenseModel:
        """Get an expense by ID or raise ExpenseNotFoundError if not found."""
        expense = await self.expense_repository.get_expense_by_id(expense_id)
        if not expense:
            raise ExpenseNotFoundError(expense_id)
        return expense

    async def _add_participants_to_expense(
        self,
        participant_ids: list[uuid.UUID],
        expense_id: uuid.UUID,
    ) -> None:
        """Add participants to an expense."""
        for participant_id in participant_ids:
            await self.expense_participant_repository.add_participant(
                user_id=participant_id,
                expense_id=expense_id,
            )

    async def _remove_all_participants_from_expense(self, expense_id: uuid.UUID) -> None:
        """Remove all participants from an expense."""
        old_participants = await self.expense_participant_repository.list_participants(expense_id)
        for participant in old_participants:
            await self.expense_participant_repository.remove_participant(
                user_id=participant.id,
                expense_id=expense_id,
            )

    def _calculate_user_expense_balance(
        self,
        expense: ExpenseModel,
        target_user_id: uuid.UUID,
        participants: list[UserModel],
        participant_count: int,
    ) -> float:
        """Calculate a user's balance for a specific expense."""
        # Calculate per-person share
        per_person_share = expense.amount / participant_count

        # Check if user is the payer
        is_payer = expense.payer_id == target_user_id

        # Check if user is a participant
        is_participant = any(participant.id == target_user_id for participant in participants)

        if is_payer and is_participant:
            # User paid for the expense and is also a participant
            # They should receive (total - their share) from others
            return expense.amount - per_person_share

        if is_payer and not is_participant:
            # User paid but is not a participant
            # They should receive the full amount back
            return expense.amount

        if not is_payer and is_participant:
            # User is a participant but didn't pay
            # They owe their share (negative balance)
            return -per_person_share

        # User is neither payer nor participant (shouldn't happen given our query)
        return 0.0

    async def create_expense(
        self,
        group_id: uuid.UUID,
        expense_data: ExpenseCreateRequest,
        current_user_id: uuid.UUID,
    ) -> tuple[ExpenseModel, UserModel, list[UserModel]]:
        """Create a new expense if the user is a member of the group."""
        # Check if current user is member of the group
        await self._validate_user_group_access(current_user_id, group_id, "create expenses in")

        # Validate that payer is a member of the group
        await self._validate_payer_in_group(expense_data.payer_id, group_id)

        # Manage participant list based on payer inclusion preference
        participants = self._manage_participant_list(
            expense_data.participants_id,
            expense_data.payer_id,
            is_payer_included=expense_data.is_payer_included,
        )

        # Validate that all participants are members of the group
        await self._validate_participants_in_group(participants, group_id)

        try:
            expense = await self.expense_repository.create_expense(
                title=expense_data.title,
                amount=expense_data.amount,
                group_id=group_id,
                payer_id=expense_data.payer_id,
                category=ExpenseCategoryEnum(expense_data.category),
                expense_date=expense_data.date,
            )

            if not expense:
                raise ExpenseCreationError

            # Add participants to the expense
            await self._add_participants_to_expense(participants, expense.id)

            # Get participant and payer user models
            payer_user_model, participant_users = await self._get_payer_and_participants_models(
                expense_data.payer_id, participants, group_id,
            )

        except IntegrityError as e:
            msg = f"Failed to create expense: {e!s}"
            raise ExpenseCreationError(msg) from e
        else:
            return (expense, payer_user_model, participant_users)

    async def get_expenses_by_group(
        self,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[tuple[ExpenseModel, UserModel, list[UserModel]]], int]:
        """Get all expenses in a group if the user is a member."""
        await self._validate_user_group_access(user_id, group_id, "access expenses in")

        offset = (page - 1) * limit
        expenses = await self.expense_repository.get_expenses_by_group(group_id, offset, limit)
        total_expenses = await self.expense_repository.count_expenses_in_group(group_id)

        # Convert to tuple format similar to group service
        expenses_with_data = []
        for expense in expenses:
            participants = await self.get_expense_participants(expense.id)

            # Get payer name
            payer = await self.user_repository.get_user_by_id(expense.payer_id)
            if not payer:
                raise ExpensePayerNotInGroupError(expense.payer_id, group_id)

            expenses_with_data.append((expense, payer, participants))

        return (expenses_with_data, total_expenses)

    async def get_expense_by_id(
        self,
        expense_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[ExpenseModel, list[UserModel], UserModel, str]:
        """Get an expense by ID if the user is a member of the expense's group."""
        expense = await self._get_expense_or_raise(expense_id)

        # Check if user is member of the expense's group
        await self._validate_user_group_access(user_id, expense.group_id, "access")

        # Get expense participants user models
        participants = await self.expense_participant_repository.list_participants(
            expense_id,
        )

        # Get payer information
        payer = await self.user_repository.get_user_by_id(expense.payer_id)
        if not payer:
            raise ExpensePayerNotInGroupError(expense.payer_id, expense.group_id)

        # Get group name
        group, _, _ = await self.group_service.get_group_by_id(expense.group_id, user_id)
        group_name = group.name if group else "Unknown"

        return (expense, participants, payer, group_name)

    async def update_expense(
        self,
        expense_id: uuid.UUID,
        expense_data: ExpenseUpdateRequest,
        user_id: uuid.UUID,
    ) -> tuple[ExpenseModel, UserModel, list[UserModel]]:
        """Update an expense if the user is a member of the group."""
        expense = await self._get_expense_or_raise(expense_id)

        # Check if user is member of the expense's group
        await self._validate_user_group_access(user_id, expense.group_id, "update")

        # Validate that all participants are members of the group
        await self._validate_participants_in_group(expense_data.participants_id, expense.group_id)

        # Update the expense details
        updated_expense = await self.expense_repository.update_expense(
            expense_id=expense_id,
            title=expense_data.title,
            amount=expense_data.amount,
            category=ExpenseCategoryEnum(expense_data.category),
            expense_date=expense_data.date,
        )

        if not updated_expense:
            raise ExpenseUpdateError(expense_id)

        # Manage participant list based on payer inclusion preference
        final_participants = self._manage_participant_list(
            expense_data.participants_id,
            expense_data.payer_id,
            is_payer_included=expense_data.is_payer_included,
        )

        # Update participants by removing old ones and adding new ones
        await self._remove_all_participants_from_expense(expense_id)
        await self._add_participants_to_expense(final_participants, updated_expense.id)

        # Get updated participant and payer user models
        payer_user_model, participant_users = await self._get_payer_and_participants_models(
            expense_data.payer_id, final_participants, expense.group_id,
        )

        return (updated_expense, payer_user_model, participant_users)

    async def delete_expense(self, expense_id: uuid.UUID) -> None:
        """Delete an expense if the user is a member of the group."""
        # Delete the expense
        is_removed = await self.expense_repository.delete_expense(expense_id)
        if not is_removed:
            raise ExpenseNotFoundError(expense_id)

    async def get_user_balance(
        self,
        group_id: uuid.UUID,
        target_user_id: uuid.UUID,
        requesting_user_id: uuid.UUID,
    ) -> UserBalanceResponseData:
        """Get a user's balance in a group if the requesting user is a member."""
        if not await self.group_service.is_user_member_of_group(requesting_user_id, group_id):
            raise GroupNotAuthorizedError(requesting_user_id, group_id, "access balance in")

        # Check if target user is also a member of the group
        if not await self.group_service.is_user_member_of_group(target_user_id, group_id):
            raise GroupMemberNotFoundError(target_user_id, group_id)

        # Get all expenses where the user is involved (as payer or participant)
        user_expenses = await self.expense_repository.get_expenses_for_user_in_group(target_user_id, group_id)

        net_balance = 0.0
        expense_balances: dict[uuid.UUID, float] = {}

        for expense in user_expenses:
            # Get participants for this expense
            participants = await self.expense_participant_repository.list_participants(expense.id)
            participant_count = len(participants)

            # Skip if no participants (shouldn't happen but safety check)
            if participant_count == 0:
                expense_balances[expense.id] = 0.0
                continue

            # Calculate expense balance for this user
            expense_balance = self._calculate_user_expense_balance(
                expense, target_user_id, participants, participant_count,
            )

            expense_balances[expense.id] = expense_balance
            net_balance += expense_balance

        return UserBalanceResponseData(
            user_id=target_user_id,
            net_balance=net_balance,
            expenses=expense_balances,
        )

    async def get_expense_participants(self, expense_id: uuid.UUID) -> list[UserModel]:
        """Get all participants of an expense."""
        return await self.expense_participant_repository.list_participants(expense_id)

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

    async def create_expense(  # noqa: C901
        self,
        group_id: uuid.UUID,
        expense_data: ExpenseCreateRequest,
        current_user_id: uuid.UUID,
    ) -> tuple[ExpenseModel, UserModel, list[UserModel]]:
        """Create a new expense if the user is a member of the group."""
        # Check if current user is member of the group
        if not await self.group_service.is_user_member_of_group(current_user_id, group_id):
            raise ExpenseAccessDeniedError(current_user_id, group_id, "create expenses in")

        # Validate that payer is a member of the group
        if not await self.group_service.is_user_member_of_group(expense_data.payer_id, group_id):
            raise ExpensePayerNotInGroupError(expense_data.payer_id, group_id)

        # Validate that all participants are members of the group
        participants = expense_data.participants_id.copy()
        if expense_data.is_payer_included and expense_data.payer_id not in participants:
            participants.append(expense_data.payer_id)

        for participant_id in participants:
            if not await self.group_service.is_user_member_of_group(participant_id, group_id):
                raise ExpenseParticipantNotInGroupError(participant_id, group_id)

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

            # Create expense participants
            for participant_id in participants:
                # Calculate equal share for now (can be enhanced later for custom shares)
                await self.expense_participant_repository.add_participant(
                    user_id=participant_id,
                    expense_id=expense.id,
                )

            # Get participant user models
            participant_users = await self.user_repository.get_many_users_by_ids(participants)
            if not participant_users:
                raise ExpenseParticipantRetrievalError

            payer_user_model = await self.user_repository.get_user_by_id(expense_data.payer_id)
            if not payer_user_model:
                raise ExpensePayerNotInGroupError(expense_data.payer_id, group_id)
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
        if not await self.group_service.is_user_member_of_group(user_id, group_id):
            raise ExpenseAccessDeniedError(user_id, group_id, "access expenses in")

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
        expense = await self.expense_repository.get_expense_by_id(expense_id)
        if not expense:
            raise ExpenseNotFoundError(expense_id)

        # Check if user is member of the expense's group
        if not await self.group_service.is_user_member_of_group(user_id, expense.group_id):
            raise ExpenseAccessDeniedError(user_id, expense_id, "access")

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
        expense = await self.expense_repository.get_expense_by_id(expense_id)
        if not expense:
            raise ExpenseNotFoundError(expense_id)

        # Check if user is member of the expense's group
        if not await self.group_service.is_user_member_of_group(user_id, expense.group_id):
            raise ExpenseAccessDeniedError(user_id, expense_id, "update")

        # Validate that all participants are members of the group
        for user_participant_id in expense_data.participants_id:
            if not await self.group_service.is_user_member_of_group(user_participant_id, expense.group_id):
                raise ExpenseParticipantNotInGroupError(user_participant_id, expense.group_id)

        updated_expense = await self.expense_repository.update_expense(
            expense_id=expense_id,
            title=expense_data.title,
            amount=expense_data.amount,
            category=ExpenseCategoryEnum(expense_data.category),
            expense_date=expense_data.date,
        )

        if not updated_expense:
            raise ExpenseUpdateError(expense_id)

        # Update participants - for now, we'll remove old participants and add new ones
        # This could be optimized to only update changed participants
        old_participants = await self.expense_participant_repository.list_participants(expense_id)
        for participant in old_participants:
            await self.expense_participant_repository.remove_participant(
                user_id=participant.id,
                expense_id=expense_id,
            )

        # Add new participants with their share amounts
        for user_participant_id in expense_data.participants_id:
            await self.expense_participant_repository.add_participant(
                user_id=user_participant_id,
                expense_id=updated_expense.id,
            )

        # Get updated participant user models
        participant_users = await self.user_repository.get_many_users_by_ids(expense_data.participants_id)
        if not participant_users:
            raise ExpenseParticipantRetrievalError

        # Get payer user model
        payer_user_model = await self.user_repository.get_user_by_id(expense_data.payer_id)
        if not payer_user_model:
            raise ExpensePayerNotInGroupError(expense_data.payer_id, expense.group_id)
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

            # Calculate per-person share
            per_person_share = expense.amount / participant_count

            # Check if user is the payer
            is_payer = expense.payer_id == target_user_id

            # Check if user is a participant
            is_participant = any(participant.id == target_user_id for participant in participants)

            if is_payer and is_participant:
                # User paid for the expense and is also a participant
                # They should receive (total - their share) from others
                expense_balance = expense.amount - per_person_share
            elif is_payer and not is_participant:
                # User paid but is not a participant
                # They should receive the full amount back
                expense_balance = expense.amount
            elif not is_payer and is_participant:
                # User is a participant but didn't pay
                # They owe their share (negative balance)
                expense_balance = -per_person_share
            else:
                # User is neither payer nor participant (shouldn't happen given our query)
                expense_balance = 0.0

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

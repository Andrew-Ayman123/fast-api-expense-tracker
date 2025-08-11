"""FastAPI User API Controller."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.services_dependencies import get_auth_service, get_user_service
from app.exceptions.application_exception import ApplicationError
from app.middleware.middleware_dependencies import get_current_user_id
from app.models import UserModel
from app.schemas.user_schema import (
    RefreshTokenRequest,
    TokenRefreshData,
    TokenRefreshResponse,
    UserCreateRequest,
    UserData,
    UserLoginRequest,
    UserLoginResponse,
    UserProfileData,
    UserProfileResponse,
    UserRegisterResponse,
    UserWithTokensData,
)
from app.services.abstraction.auth_service_abstraction import AuthService
from app.services.user_service import UserService
from app.utils.create_exception_util import create_http_exception
from app.utils.logger_util import get_logger

# versioning is handled in the main file
router = APIRouter(prefix="/users", tags=["users"])


def _convert_user_to_data(user: UserModel) -> UserData:
    """Convert UserModel to UserData schema using from_attributes."""
    return UserData.model_validate(user, from_attributes=True)


@router.post("/register")
async def register_user(
    user_data: UserCreateRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserRegisterResponse:
    """Register a new user and return user data with JWT tokens.

    Args:
        user_data (UserCreateRequest): The data for creating a new user.
        user_service (UserService): The user service instance.
        auth_service (auth_service): The auth service instance.

    Returns:
        UserRegisterResponse: The user response with JWT tokens wrapped in data field.

    Raises:
        409 Conflict: If the user already exists.
        400 Bad Request: If there is an error during user creation.

    """
    try:
        user = await user_service.create_user(user_data)
        token = auth_service.generate_token(user.id)
        refresh_token = auth_service.generate_refresh_token(user.id)

        user_data_obj = _convert_user_to_data(user)
        user_with_tokens = UserWithTokensData(user=user_data_obj, token=token, refresh_token=refresh_token)

        return UserRegisterResponse(data=user_with_tokens)
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        get_logger().error("Error creating user: %s", str(e))
        raise create_http_exception(
            message="Failed to create user",
            status_code=500,
            details={"error": str(e)},
        ) from e


@router.post("/login")
async def login_user(
    login_data: UserLoginRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserLoginResponse:
    """Login a user and return user data with JWT tokens.

    Args:
        login_data (UserLoginRequest): The login data containing email and password.
        user_service (UserService): The user service instance.
        auth_service (auth_service): The auth service instance.

    Returns:
        UserLoginResponse: The user response with JWT tokens wrapped in data field.

    Raises:
        401 Unauthorized: If the email or password is incorrect.
        400 Bad Request: If there is an error during user verification.

    """
    try:
        user = await user_service.verify_user_exists(login_data)
        token = auth_service.generate_token(user.id)
        refresh_token = auth_service.generate_refresh_token(user.id)

        user_data_obj = _convert_user_to_data(user)
        user_with_tokens = UserWithTokensData(user=user_data_obj, token=token, refresh_token=refresh_token)

        return UserLoginResponse(data=user_with_tokens)
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        raise create_http_exception(
            message="Login failed",
            status_code=500,
            details={"error": str(e)},
        ) from e


@router.get("/me")
async def get_user_by_id(
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> UserProfileResponse:
    """Get user profile by ID from JWT token.

    Args:
        user_service (UserService): The user service instance.
        current_user_id (uuid.UUID): The user ID extracted from the JWT token.

    Returns:
        UserProfileResponse: The user profile data wrapped in data field.

    Raises:
        400 Bad Request: If there is an error retrieving the user profile.
        403 Forbidden: If the JWT token is invalid or expired.
        404 Not Found: If the user ID from the token is not found.

    """
    try:
        user = await user_service.get_user_by_id(current_user_id)

        user_data_obj = _convert_user_to_data(user)
        user_profile_data = UserProfileData(user=user_data_obj)

        return UserProfileResponse(data=user_profile_data)
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        raise create_http_exception(
            message="Failed to retrieve user profile",
            status_code=500,
            details={"error": str(e)},
        ) from e


@router.post("/refresh")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenRefreshResponse:
    """Refresh tokens using a valid refresh token.

    Args:
        refresh_data (RefreshTokenRequest): The refresh token data.
        user_service (UserService): The user service instance.
        auth_service (auth_service): The auth service instance.

    Returns:
        TokenRefreshResponse: New JWT tokens wrapped in data field.

    Raises:
        401 Unauthorized: If the refresh token is invalid or expired.
        404 Not Found: If the user ID from the token is not found.
        400 Bad Request: If there is an error during token refresh.

    """
    try:
        # Decode the refresh token to get user ID
        user_id = auth_service.decode_refresh_token_user_id(refresh_data.refresh_token)

        # Verify user still exists
        user = await user_service.get_user_by_id(user_id)

        # Generate new tokens
        new_token = auth_service.generate_token(user.id)
        new_refresh_token = auth_service.generate_refresh_token(user.id)

        token_data = TokenRefreshData(token=new_token, refresh_token=new_refresh_token)

        return TokenRefreshResponse(data=token_data)
    except ApplicationError as e:
        raise e.to_http_exception() from e
    except Exception as e:
        raise create_http_exception(
            message="Token refresh failed",
            status_code=500,
            details={"error": str(e)},
        ) from e

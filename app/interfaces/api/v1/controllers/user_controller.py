"""FastAPI User API Controller."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import get_jwt_service, get_user_service
from app.exceptions.user_exception import (
    UserAlreadyExistsError,
    UserIDNotFoundError,
    WrongEmailOrPasswordError,
)
from app.middleware.jwt_middleware import JWTBearer
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
from app.services.jwt_service import JWTService
from app.services.user_service import UserService
from app.utils.create_error_data_util import create_error_data
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
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> UserRegisterResponse:
    """Register a new user and return user data with JWT tokens.

    Args:
        user_data (UserCreateRequest): The data for creating a new user.
        user_service (UserService): The user service instance.
        jwt_service (JWTService): The JWT service instance.

    Returns:
        UserRegisterResponse: The user response with JWT tokens wrapped in data field.

    Raises:
        409 Conflict: If the user already exists.
        400 Bad Request: If there is an error during user creation.

    """
    try:
        user = await user_service.create_user(user_data)
        token = jwt_service.generate_token(user.id)
        refresh_token = jwt_service.generate_refresh_token(user.id)

        user_data_obj = _convert_user_to_data(user)
        user_with_tokens = UserWithTokensData(user=user_data_obj, token=token, refresh_token=refresh_token)

        return UserRegisterResponse(data=user_with_tokens)
    except UserAlreadyExistsError as e:
        error_data = create_error_data(message="User already exists", details={"email": user_data.email})
        raise HTTPException(status_code=409, detail=error_data.model_dump()) from e
    except Exception as e:
        get_logger().error("Error creating user: %s", str(e))
        error_data = create_error_data(message="Failed to create user", details={"error": str(e)})
        raise HTTPException(status_code=400, detail=error_data.model_dump()) from e


@router.post("/login")
async def login_user(
    login_data: UserLoginRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> UserLoginResponse:
    """Login a user and return user data with JWT tokens.

    Args:
        login_data (UserLoginRequest): The login data containing email and password.
        user_service (UserService): The user service instance.
        jwt_service (JWTService): The JWT service instance.

    Returns:
        UserLoginResponse: The user response with JWT tokens wrapped in data field.

    Raises:
        401 Unauthorized: If the email or password is incorrect.
        400 Bad Request: If there is an error during user verification.

    """
    try:
        user = await user_service.verify_user_exists(login_data)
        token = jwt_service.generate_token(user.id)
        refresh_token = jwt_service.generate_refresh_token(user.id)

        user_data_obj = _convert_user_to_data(user)
        user_with_tokens = UserWithTokensData(user=user_data_obj, token=token, refresh_token=refresh_token)

        return UserLoginResponse(data=user_with_tokens)
    except WrongEmailOrPasswordError as e:
        error_data = create_error_data(message="Invalid credentials", details={"email": login_data.email})
        raise HTTPException(status_code=401, detail=error_data.model_dump()) from e
    except Exception as e:
        error_data = create_error_data(message="Login failed", details={"error": str(e)})
        raise HTTPException(status_code=400, detail=error_data.model_dump()) from e


@router.get("/me", dependencies=[Depends(JWTBearer())])
async def get_user_by_id(
    user_service: Annotated[UserService, Depends(get_user_service)],
    request: Request,
) -> UserProfileResponse:
    """Get user profile by ID from JWT token.

    Args:
        user_service (UserService): The user service instance.
        request (Request): The FastAPI request object containing the JWT token.

    Returns:
        UserProfileResponse: The user profile data wrapped in data field.

    Raises:
        400 Bad Request: If there is an error retrieving the user profile.
        403 Forbidden: If the JWT token is invalid or expired.
        404 Not Found: If the user ID from the token is not found.

    """
    try:
        user_id = request.state.user_id
        user = await user_service.get_user_by_id(user_id)

        user_data_obj = _convert_user_to_data(user)
        user_profile_data = UserProfileData(user=user_data_obj)

        return UserProfileResponse(data=user_profile_data)
    except UserIDNotFoundError as e:
        error_data = create_error_data(
            message="User not found",
            details={"user_id": str(request.state.user_id)},
        )
        raise HTTPException(status_code=404, detail=error_data.model_dump()) from e
    except Exception as e:
        error_data = create_error_data(message="Failed to retrieve user profile", details={"error": str(e)})
        raise HTTPException(status_code=400, detail=error_data.model_dump()) from e


@router.post("/refresh")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> TokenRefreshResponse:
    """Refresh JWT tokens using a valid refresh token.

    Args:
        refresh_data (RefreshTokenRequest): The refresh token data.
        user_service (UserService): The user service instance.
        jwt_service (JWTService): The JWT service instance.

    Returns:
        TokenRefreshResponse: New JWT tokens wrapped in data field.

    Raises:
        401 Unauthorized: If the refresh token is invalid or expired.
        404 Not Found: If the user ID from the token is not found.
        400 Bad Request: If there is an error during token refresh.

    """
    try:
        # Decode the refresh token to get user ID
        user_id = jwt_service.decode_refresh_token_user_id(refresh_data.refresh_token)

        # Verify user still exists
        user = await user_service.get_user_by_id(user_id)

        # Generate new tokens
        new_token = jwt_service.generate_token(user.id)
        new_refresh_token = jwt_service.generate_refresh_token(user.id)

        token_data = TokenRefreshData(token=new_token, refresh_token=new_refresh_token)

        return TokenRefreshResponse(data=token_data)
    except ValueError as e:
        # JWT decode errors (expired, invalid)
        error_data = create_error_data(
            message="Invalid or expired refresh token",
            details={"token_error": str(e)},
        )
        raise HTTPException(status_code=401, detail=error_data.model_dump()) from e
    except UserIDNotFoundError as e:
        error_data = create_error_data(message="User not found", details={"error": str(e)})
        raise HTTPException(status_code=404, detail=error_data.model_dump()) from e
    except Exception as e:
        get_logger().error("Error refreshing token: %s", str(e))
        error_data = create_error_data(message="Token refresh failed", details={"error": str(e)})
        raise HTTPException(status_code=400, detail=error_data.model_dump()) from e

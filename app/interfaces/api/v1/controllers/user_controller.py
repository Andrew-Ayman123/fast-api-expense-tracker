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
from app.models.user_model import UserModel
from app.schemas.user_schema import UserCreateRequest, UserLoginRequest, UserResponse, UserResponseWithToken
from app.services.jwt_service import JWTService
from app.services.user_service import UserService
from app.utils.logger_util import get_logger

# versioning is handled in the main file
router = APIRouter(prefix="/user", tags=["user"])


def _convert_user_to_response(user: UserModel) -> UserResponse:
    """Convert UserModel to UserResponse schema using from_attributes."""
    return UserResponse.model_validate(user, from_attributes=True)


@router.post("/register")
async def register_user(
    user_data: UserCreateRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> UserResponseWithToken:
    """Register a new user and return user data with JWT token.

    Args:
        user_data (UserCreateRequest): The data for creating a new user.
        user_service (UserService): The user service instance.
        jwt_service (JWTService): The JWT service instance.

    Returns:
        UserResponseWithToken: The user response with JWT token.

    Raises:
        409 Conflict: If the user already exists.
        400 Bad Request: If there is an error during user creation.

    """
    try:
        user = await user_service.create_user(user_data)
        token = jwt_service.generate_token(user.id)
        return UserResponseWithToken(**_convert_user_to_response(user).model_dump(), token=token)
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except Exception as e:
        get_logger().error("Error creating user: %s", str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/login")
async def login_user(
    login_data: UserLoginRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> UserResponseWithToken:
    """Login a user and return user data with JWT token.

    Args:
        login_data (UserLoginRequest): The login data containing email and password.
        user_service (UserService): The user service instance.
        jwt_service (JWTService): The JWT service instance.

    Returns:
        UserResponseWithToken: The user response with JWT token.

    Raises:
        401 Unauthorized: If the email or password is incorrect.
        400 Bad Request: If there is an error during user verification.

    """
    try:
        user = await user_service.verify_user_exists(login_data)
        token = jwt_service.generate_token(user.id)

        return UserResponseWithToken(**_convert_user_to_response(user).model_dump(), token=token)
    except WrongEmailOrPasswordError as e:
        raise HTTPException(status_code=401, detail="Wrong email or password") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/profile", dependencies=[Depends(JWTBearer())])
async def get_user_by_id(
    user_service: Annotated[UserService, Depends(get_user_service)],
    request: Request,
) -> UserResponse:
    """Get user profile by ID from JWT token.

    Args:
        user_service (UserService): The user service instance.
        request (Request): The FastAPI request object containing the JWT token.

    Returns:
        UserResponse: The user profile data.

    Raises:
        400 Bad Request: If there is an error retrieving the user profile.
        403 Forbidden: If the JWT token is invalid or expired.
        404 Not Found: If the user ID from the token is not found.

    """
    try:
        user_id = request.state.user_id
        user = await user_service.get_user_by_id(user_id)

        return _convert_user_to_response(user)
    except UserIDNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

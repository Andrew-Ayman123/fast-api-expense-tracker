"""JWT Authentication Middleware for FastAPI."""
import uuid
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.dependencies.services_dependencies import get_jwt_service
from app.services.jwt_service import JWTService
from app.utils.create_exception_util import create_http_exception


@lru_cache
def get_http_bearer() -> HTTPBearer:
    """Return a cached instance of HTTPBearer security scheme."""
    return HTTPBearer(auto_error=True)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(get_http_bearer)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> uuid.UUID:
    """Extract and verify JWT token, return user_id."""
    if credentials.scheme != "Bearer":
        raise create_http_exception(
            message="Invalid authentication scheme.",
            status_code=403,
            details={"error": "Authentication scheme must be Bearer."},
        )
    try:
        return jwt_service.decode_token_user_id(credentials.credentials)
    except Exception as e:
        raise create_http_exception(
            message="Invalid or expired token.",
            status_code=403,
            details={"error": str(e)},
        ) from e

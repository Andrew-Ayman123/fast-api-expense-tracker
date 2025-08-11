"""Dependency to get the current user ID from the authentication middleware."""
import uuid
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.middleware.abstraction.auth_middleware_abstraction import AuthMiddlewareAbstraction
from app.middleware.factory import AuthMiddlewareFactory


@lru_cache
def get_auth_middleware() -> AuthMiddlewareAbstraction:
    """Get the authentication middleware instance."""
    factory = AuthMiddlewareFactory()
    return factory.get_auth_middleware()


async def get_current_user_id(
    auth_middleware: Annotated[AuthMiddlewareAbstraction, Depends(get_auth_middleware)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer(auto_error=True))],
) -> uuid.UUID:
    """Get the current user ID from the authentication middleware."""
    return await auth_middleware.get_current_user_id(credentials)

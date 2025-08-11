"""Auth middleware that uses the AuthService factory (provider-agnostic)."""

import uuid
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.exceptions.application_exception import ApplicationError
from app.middleware.abstraction.auth_middleware_abstraction import AuthMiddlewareAbstraction
from app.services.abstraction.auth_service_abstraction import AuthService
from app.utils.create_exception_util import create_http_exception


class JWTAuthMiddleware(AuthMiddlewareAbstraction):
    """JWT-based authentication middleware implementation."""

    def __init__(self, auth_service: AuthService) -> None:
        """Initialize the JWTAuthMiddleware with an AuthService instance."""
        self.auth_service = auth_service

    @staticmethod
    @lru_cache
    def get_http_bearer() -> HTTPBearer:
        """Return a cached HTTPBearer security instance."""
        return HTTPBearer(auto_error=True)

    async def get_current_user_id(
        self,
        credentials: Annotated[HTTPAuthorizationCredentials, Depends(get_http_bearer.__func__)],
    ) -> uuid.UUID:
        """Extract and verify a JWT token and return user_id."""
        if credentials.scheme != "Bearer":
            raise create_http_exception(
                message="Invalid authentication scheme.",
                status_code=403,
                details={"error": f"{credentials.scheme} Authentication scheme must be Bearer."},
            )

        try:
            return self.auth_service.decode_token_user_id(credentials.credentials)
        except ApplicationError as e:
            raise e.to_http_exception() from e
        except Exception as e:
            raise create_http_exception(
                message="Invalid or expired token.",
                status_code=500,
                details={"error": str(e)},
            ) from e

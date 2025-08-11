"""Abstract middleware contract for authentication."""
import uuid
from abc import ABC, abstractmethod

from fastapi.security import HTTPAuthorizationCredentials


class AuthMiddlewareAbstraction(ABC):
    """Abstract middleware contract for authentication."""

    @abstractmethod
    async def get_current_user_id(self, credentials: HTTPAuthorizationCredentials) -> uuid.UUID:
        """Extract and validate the current user ID from request context."""
        raise NotImplementedError

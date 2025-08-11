"""Auth service abstraction for managing user authentication and authorization."""

import uuid
from abc import ABC, abstractmethod


class AuthService(ABC):
    """Abstract base class for authentication services."""

    @abstractmethod
    def decode_token_user_id(self, token: str) -> uuid.UUID:
        """Decode an access token and return the user id as UUID."""
        raise NotImplementedError

    @abstractmethod
    def decode_refresh_token_user_id(self, refresh_token: str) -> uuid.UUID:
        """Decode a refresh token and return the user id as UUID."""
        raise NotImplementedError

    def generate_token(self, user_id: uuid.UUID) -> str:
        """Generate an access token for a user."""
        raise NotImplementedError

    def generate_refresh_token(self, user_id: uuid.UUID) -> str:
        """Generate a refresh token for a user."""
        raise NotImplementedError

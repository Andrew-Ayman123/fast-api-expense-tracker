"""JWT Service for handling JSON Web Tokens (JWT) in a FastAPI application."""

import uuid
from datetime import UTC, datetime, timedelta

from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError


class JWTService:
    """Service for handling JWT token generation and decoding."""

    def __init__(self, secret_key: str, algorithm: str = "HS256", expiration_minutes: int = 60) -> None:
        """Initialize the JWTService with secret key and algorithm.

        Args:
            secret_key (str): The secret key used for signing the JWT.
            algorithm (str): The algorithm used for signing the JWT. Default is 'HS256'.
            expiration_minutes (int): The expiration time for the JWT in minutes. Default is 60

        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_minutes = expiration_minutes

    def generate_token(self, user_id: uuid.UUID) -> str:
        """Generate a JWT token for user authentication."""
        expiration = datetime.now(tz=UTC) + timedelta(minutes=self.expiration_minutes)
        payload = {
            "user_id": str(user_id),
            "exp": int(
                expiration.timestamp(),
            ),  # Use standard JWT 'exp' claim with int(timestamp) for automatic validation
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> dict:
        """Decode a JWT token and return the payload.

        Args:
            token (str): The JWT token to decode.

        Returns:
            dict: The decoded payload containing user information.

        """
        try:
            # The jose library automatically handles exp claim validation
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except ExpiredSignatureError as e:
            msg = "Token has expired"
            raise ValueError(msg) from e
        except JWTError as e:
            msg = "Invalid token"
            raise ValueError(msg) from e

    def decode_token_user_id(self, token: str) -> uuid.UUID:
        """Decode a JWT token and return the user ID."""
        payload = self.decode_token(token)
        return uuid.UUID(payload["user_id"])

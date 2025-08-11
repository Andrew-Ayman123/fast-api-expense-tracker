"""Middleware factory to select authentication provider dynamically."""



from app.dependencies.services_dependencies import get_auth_service
from app.dependencies.settings_dependencies import get_env_settings
from app.middleware.abstraction.auth_middleware_abstraction import AuthMiddlewareAbstraction
from app.middleware.jwt_middleware import JWTAuthMiddleware


class AuthMiddlewareFactory:
    """Factory class to create authentication middleware instances."""

    @staticmethod
    def get_auth_middleware() -> AuthMiddlewareAbstraction:
        """Return the authentication middleware based on AUTH_MODE in environment."""
        settings = get_env_settings()
        auth_mode = settings.AUTH_MODE

        if auth_mode == "JWT":
            auth_service = get_auth_service()
            return JWTAuthMiddleware(auth_service=auth_service)

        msg = f"Unsupported AUTH_PROVIDER: {auth_mode}"
        raise ValueError(msg)

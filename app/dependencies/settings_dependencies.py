"""Dependency for application settings."""

from functools import lru_cache

from app.config.environment import Settings


@lru_cache
def get_env_settings() -> Settings:
    """Get the application settings instance.

    Returns:
        Settings: The application settings instance with environment variables loaded.

    """
    return Settings()

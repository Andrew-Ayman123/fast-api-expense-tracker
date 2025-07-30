"""Environment configuration settings for the FastAPI application.

This module defines the application settings using Pydantic's BaseSettings.
It includes database connection settings and API metadata.
"""

from pydantic_settings import BaseSettings

from app.utils.env_util import get_env, get_env_bool, get_env_int


class Settings(BaseSettings):
    """Application settings: database and API configuration."""

    database_url: str = get_env("DATABASE_URL")
    database_host: str = get_env("DATABASE_HOST")
    database_port: int = get_env_int("DATABASE_PORT")
    database_name: str = get_env("DATABASE_NAME")
    database_user: str = get_env("DATABASE_USER")
    database_password: str = get_env("DATABASE_PASSWORD")

    database_logging: bool = get_env_bool("DATABASE_LOGGING")

    app_name: str = get_env("APP_NAME")
    app_description: str = get_env("APP_DESCRIPTION")
    app_version: str = get_env("APP_VERSION")

    server_host: str = get_env("SERVER_HOST")
    server_port: int = get_env_int("SERVER_PORT")
    server_reload: bool = get_env_bool("SERVER_RELOAD")
    server_log_level: str = get_env("SERVER_LOG_LEVEL")

    jwt_secret_key: str = get_env("JWT_SECRET_KEY")
    jwt_algorithm: str = get_env("JWT_ALGORITHM")
    jwt_expiration_minutes: int = get_env_int("JWT_EXPIRATION_MINUTES")

    testing: bool = get_env_bool("TESTING")

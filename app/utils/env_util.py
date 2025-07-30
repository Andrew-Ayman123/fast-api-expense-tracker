"""Environment variable utility functions for the App.

These functions help in retrieving environment variables with optional default values.
They handle different data types such as string, integer, and boolean.
"""

import os

from app.exceptions.env_missing_exception import MissingEnvironmentVariableError
from app.exceptions.env_wrong_format import EnvironmentVariableFormatError


def get_env(var_name: str) -> str:
    """Get an environment variable or return a default value if not set.

    Args:
        var_name: The name of the environment variable to retrieve

    Returns:
        The value of the environment variable or the default value if not set

    """
    value = os.getenv(var_name)
    if value is None:
        raise MissingEnvironmentVariableError(var_name)

    return value


def get_env_int(var_name: str) -> int:
    """Get an environment variable as an integer or return a default value if not set.

    Args:
        var_name: The name of the environment variable to retrieve

    Returns:
        The value of the environment variable as an integer or the default value if not set

    """
    value = get_env(var_name)

    if not value.isdigit():
        raise EnvironmentVariableFormatError(var_name, value, "integer")
    return int(value)


def get_env_bool(var_name: str) -> bool:
    """Retrieve an environment variable and interpret it as a boolean.

    Args:
        var_name: Name of the environment variable to fetch.

    Returns:
        Boolean value of the environment variable, or None if not set and no default is provided.

    """
    value = get_env(var_name).lower()  # Normalize to lowercase for comparison
    if value not in ("true", "false", "1", "0", "yes", "no"):
        raise EnvironmentVariableFormatError(var_name, value, "boolean")

    return value in ("true", "1", "yes")

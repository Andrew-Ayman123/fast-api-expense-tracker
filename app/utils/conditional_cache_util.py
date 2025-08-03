"""Utility for applying LRU caching conditionally based on the environment."""
from collections.abc import Callable
from functools import lru_cache

from app.dependencies.settings_dependencies import get_env_settings


def conditional_lru_cache() -> Callable:
    """Apply LRU cache conditionally based on the environment."""

    def decorator(func: Callable) -> Callable:
        # No caching in testing mode because shared loopback in engine cause errors
        if get_env_settings().testing:
            return func
        return lru_cache()(func)

    return decorator

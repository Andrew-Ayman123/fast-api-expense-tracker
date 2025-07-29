"""logging utility module for the FastAPI application."""

import logging
from functools import lru_cache


@lru_cache
def get_logger() -> logging.Logger:
    """Get the application logger instance.

    Returns:
        logging.Logger: The logger instance configured for the application.

    """
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

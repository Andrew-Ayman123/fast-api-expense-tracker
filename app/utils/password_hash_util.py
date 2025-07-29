"""Hashing and verifying utils passwords using the Passlib library."""

import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password (str): The plaintext password to hash.

    Returns:
        str: The hashed password.

    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_pass: str) -> bool:
    """Verify a password against a hashed password.

    Args:
        password (str): The plaintext password to verify.
        hashed_pass (str): The hashed password to compare against.

    Returns:
        bool: True if the password matches the hashed password, False otherwise.

    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed_pass.encode("utf-8"))

"""Shared base model for all SQLAlchemy models in the application.

It uses SQLAlchemy's DeclarativeBase to create a base class that all models can inherit from.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all models using SQLAlchemy's declarative system."""

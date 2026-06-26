"""
SQLAlchemy ORM models will be defined in subsequent milestones.

This file re-exports the Base from core.database for convenience.
"""

from backend.core.database import Base

__all__ = ["Base"]

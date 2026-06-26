"""
Centralized model exports.

Importing models here ensures Alembic and SQLAlchemy detect them
via Base.metadata BEFORE any relationship resolution occurs.
"""

from backend.core.database import Base
from backend.models.department import Department
from backend.models.role import Role
from backend.models.user import User

__all__ = ["Base", "Role", "Department", "User"]

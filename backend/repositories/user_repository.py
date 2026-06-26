"""
User-specific repository operations.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.role import Role
from backend.models.user import User
from backend.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity."""

    def __init__(self, db: Session) -> None:
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return self.db.scalars(stmt).first()

    def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username.lower())
        return self.db.scalars(stmt).first()

    def email_exists(self, email: str) -> bool:
        return self.get_by_email(email) is not None

    def username_exists(self, username: str) -> bool:
        return self.get_by_username(username) is not None

    def get_role_by_name(self, name: str) -> Role | None:
        stmt = select(Role).where(Role.name == name.lower())
        return self.db.scalars(stmt).first()

    def update_last_login(self, user: User) -> None:
        user.last_login_at = datetime.utcnow()
        self.db.flush()

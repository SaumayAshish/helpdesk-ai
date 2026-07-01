"""
User management business logic.

Scope for this step: listing users (with role/department/status filters)
and activating/deactivating accounts. Role assignment, registration, and
password management already live in AuthService — this service does not
duplicate them.

RBAC for these endpoints is enforced at the route layer via `require_roles`
(same pattern as backend/api/v1/endpoints/dashboard.py), not inside this
service. That's a deliberate distinction from TicketService: ticket RBAC
depends on *which* ticket (e.g. "your own"), so it has to live in the
service where the ticket is loaded. User listing/activation is a blanket
role gate with no per-resource ownership check, so the dependency alone
is sufficient — duplicating it here would just be dead code.
"""

import math

from loguru import logger
from sqlalchemy.orm import Session

from backend.core.exceptions import ForbiddenException, NotFoundException
from backend.models.user import User
from backend.repositories.user_repository import UserRepository


class UserService:
    """Encapsulates user management workflows."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    def _get_user_or_404(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} not found")
        return user

    # =====================================================
    # List — paginated, filterable
    # =====================================================

    def get_users(
        self,
        page: int = 1,
        page_size: int = 20,
        role: str | None = None,
        department_id: int | None = None,
        is_active: bool | None = None,
    ) -> dict:
        """
        Return a paginated list of users.

        Used for two purposes:
        - Admin dashboard: manage the full roster
        - Ticket assignment picker: engineers/admins fetch role="engineer"
          to populate the "assign to" dropdown
        """
        users = self.user_repo.get_paginated(
            page=page,
            page_size=page_size,
            role_name=role,
            department_id=department_id,
            is_active=is_active,
        )
        total = self.user_repo.count(
            role_name=role,
            department_id=department_id,
            is_active=is_active,
        )

        return {
            "items": users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 1,
        }

    # =====================================================
    # Deactivate — soft-disable an account
    # =====================================================

    def deactivate_user(self, user_id: int, acting_user: User) -> User:
        """
        Disable a user account. Deactivated users can no longer log in
        (see AuthService.authenticate — checks is_active).

        Guards against an admin locking themselves out, which would leave
        the system with no way to reactivate anyone.
        """
        if user_id == acting_user.id:
            raise ForbiddenException("You cannot deactivate your own account")

        user = self._get_user_or_404(user_id)
        user.is_active = False
        self.user_repo.commit()
        self.db.refresh(user)

        logger.info(f"User deactivated: id={user.id} by admin_id={acting_user.id}")
        return user

    # =====================================================
    # Activate — re-enable a disabled account
    # =====================================================

    def activate_user(self, user_id: int, acting_user: User) -> User:
        """Re-enable a previously deactivated account."""
        user = self._get_user_or_404(user_id)
        user.is_active = True
        self.user_repo.commit()
        self.db.refresh(user)

        logger.info(f"User activated: id={user.id} by admin_id={acting_user.id}")
        return user

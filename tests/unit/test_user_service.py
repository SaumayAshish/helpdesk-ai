"""
Unit tests for UserService business logic.

These mock the repository and DB session, so they run without a real
database connection — same convention as test_ticket_service.py.
"""

from unittest.mock import MagicMock

import pytest

from backend.core.exceptions import ForbiddenException, NotFoundException
from backend.services.user_service import UserService


def make_service():
    """Return a UserService with a mocked DB session and repository."""
    db = MagicMock()
    service = UserService(db)
    service.user_repo = MagicMock()
    return service


# =====================================================
# Tests — get_users (listing + pagination math)
# =====================================================


class TestGetUsers:

    def test_returns_paginated_shape(self):
        service = make_service()
        service.user_repo.get_paginated.return_value = [MagicMock(), MagicMock()]
        service.user_repo.count.return_value = 2

        result = service.get_users(page=1, page_size=20)

        assert result["total"] == 2
        assert result["page"] == 1
        assert result["total_pages"] == 1
        assert len(result["items"]) == 2

    def test_total_pages_rounds_up(self):
        service = make_service()
        service.user_repo.get_paginated.return_value = []
        service.user_repo.count.return_value = 25  # 25 users, page_size=20 -> 2 pages

        result = service.get_users(page=1, page_size=20)

        assert result["total_pages"] == 2

    def test_empty_result_has_one_total_page(self):
        service = make_service()
        service.user_repo.get_paginated.return_value = []
        service.user_repo.count.return_value = 0

        result = service.get_users(page=1, page_size=20)

        assert result["total_pages"] == 1

    def test_forwards_filters_to_repository(self):
        service = make_service()
        service.user_repo.get_paginated.return_value = []
        service.user_repo.count.return_value = 0

        service.get_users(page=2, page_size=10, role="engineer", department_id=3, is_active=True)

        service.user_repo.get_paginated.assert_called_once_with(
            page=2, page_size=10, role_name="engineer", department_id=3, is_active=True
        )
        service.user_repo.count.assert_called_once_with(
            role_name="engineer", department_id=3, is_active=True
        )


# =====================================================
# Tests — deactivate_user
# =====================================================


class TestDeactivateUser:

    def test_admin_can_deactivate_another_user(self, admin_user):
        service = make_service()
        target = MagicMock(id=99, is_active=True)
        service.user_repo.get_by_id.return_value = target

        result = service.deactivate_user(99, admin_user)

        assert result.is_active is False
        service.user_repo.commit.assert_called_once()

    def test_admin_cannot_deactivate_self(self, admin_user):
        service = make_service()

        with pytest.raises(ForbiddenException, match="cannot deactivate your own account"):
            service.deactivate_user(admin_user.id, admin_user)

        service.user_repo.get_by_id.assert_not_called()

    def test_raises_404_for_missing_user(self, admin_user):
        service = make_service()
        service.user_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            service.deactivate_user(999, admin_user)


# =====================================================
# Tests — activate_user
# =====================================================


class TestActivateUser:

    def test_admin_can_activate_user(self, admin_user):
        service = make_service()
        target = MagicMock(id=99, is_active=False)
        service.user_repo.get_by_id.return_value = target

        result = service.activate_user(99, admin_user)

        assert result.is_active is True
        service.user_repo.commit.assert_called_once()

    def test_raises_404_for_missing_user(self, admin_user):
        service = make_service()
        service.user_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            service.activate_user(999, admin_user)

"""
Unit tests for TicketService business logic.

These tests mock the repository and database session,
so they run without any database connection.
"""

from unittest.mock import MagicMock, patch

import pytest

from backend.core.exceptions import ForbiddenException, NotFoundException
from backend.models.ticket import TicketStatus
from backend.services.ticket_service import TicketService

# =====================================================
# Helpers — build a service with mocked dependencies
# =====================================================


def make_service():
    """Return a TicketService with a mocked DB session."""
    db = MagicMock()
    service = TicketService(db)
    service.ticket_repo = MagicMock()
    return service


# =====================================================
# Tests — get_ticket (read access RBAC)
# =====================================================


class TestGetTicket:

    def test_employee_can_view_own_ticket(self, employee_user, open_ticket):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = open_ticket

        result = service.get_ticket(1, employee_user)

        assert result == open_ticket

    def test_employee_cannot_view_others_ticket(self, employee_user, open_ticket):
        # Ticket belongs to user_id=999, not employee (id=10)
        open_ticket.created_by_id = 999
        service = make_service()
        service.ticket_repo.get_by_id.return_value = open_ticket

        with pytest.raises(ForbiddenException):
            service.get_ticket(1, employee_user)

    def test_engineer_can_view_any_ticket(self, engineer_user, open_ticket):
        open_ticket.created_by_id = 999  # belongs to someone else
        service = make_service()
        service.ticket_repo.get_by_id.return_value = open_ticket

        result = service.get_ticket(1, engineer_user)

        assert result == open_ticket

    def test_raises_404_when_ticket_not_found(self, employee_user):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            service.get_ticket(999, employee_user)


# =====================================================
# Tests — assign_ticket (RBAC + state transition)
# =====================================================


class TestAssignTicket:

    def test_employee_cannot_assign(self, employee_user, open_ticket):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = open_ticket

        with pytest.raises(ForbiddenException, match="Only engineers and admins"):
            service.assign_ticket(1, employee_user, assignee_id=20)

    def test_engineer_can_assign(self, engineer_user, open_ticket):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = open_ticket

        # Mock db.get to return a valid assignee
        assignee = MagicMock()
        assignee.is_active = True
        service.db.get.return_value = assignee

        service.assign_ticket(1, engineer_user, assignee_id=20)

        assert open_ticket.assigned_to_id == 20

    def test_assign_transitions_open_to_in_progress(self, engineer_user, open_ticket):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = open_ticket

        assignee = MagicMock()
        assignee.is_active = True
        service.db.get.return_value = assignee

        service.assign_ticket(1, engineer_user, assignee_id=20)

        assert open_ticket.status == TicketStatus.IN_PROGRESS

    def test_assign_raises_404_for_inactive_assignee(self, engineer_user, open_ticket):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = open_ticket

        inactive_user = MagicMock()
        inactive_user.is_active = False
        service.db.get.return_value = inactive_user

        with pytest.raises(NotFoundException):
            service.assign_ticket(1, engineer_user, assignee_id=99)


# =====================================================
# Tests — resolve_ticket (state machine)
# =====================================================


class TestResolveTicket:

    def test_engineer_can_resolve_in_progress_ticket(self, engineer_user, in_progress_ticket):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = in_progress_ticket

        service.resolve_ticket(1, engineer_user)

        assert in_progress_ticket.status == TicketStatus.RESOLVED

    def test_cannot_resolve_open_ticket(self, engineer_user, open_ticket):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = open_ticket

        with pytest.raises(ForbiddenException, match="IN_PROGRESS or REOPENED"):
            service.resolve_ticket(1, engineer_user)

    def test_employee_cannot_resolve(self, employee_user, in_progress_ticket):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = in_progress_ticket

        with pytest.raises(ForbiddenException, match="Only engineers and admins"):
            service.resolve_ticket(1, employee_user)

    def test_resolving_after_due_date_sets_sla_breached(self, engineer_user, in_progress_ticket):
        from datetime import datetime, timedelta, timezone

        service = make_service()
        in_progress_ticket.sla_due_at = datetime.now(timezone.utc) - timedelta(hours=1)
        service.ticket_repo.get_by_id.return_value = in_progress_ticket

        service.resolve_ticket(1, engineer_user)

        assert in_progress_ticket.sla_breached is True

    def test_resolving_before_due_date_does_not_breach(self, engineer_user, in_progress_ticket):
        from datetime import datetime, timedelta, timezone

        service = make_service()
        in_progress_ticket.sla_due_at = datetime.now(timezone.utc) + timedelta(hours=1)
        service.ticket_repo.get_by_id.return_value = in_progress_ticket

        service.resolve_ticket(1, engineer_user)

        assert in_progress_ticket.sla_breached is False

    def test_resolving_with_no_due_date_does_not_breach(self, engineer_user, in_progress_ticket):
        service = make_service()
        in_progress_ticket.sla_due_at = None  # no matching SlaPolicy at creation time
        service.ticket_repo.get_by_id.return_value = in_progress_ticket

        service.resolve_ticket(1, engineer_user)

        assert in_progress_ticket.sla_breached is False


# =====================================================
# Tests — close_ticket (state machine)
# =====================================================


class TestCloseTicket:

    def test_engineer_can_close_resolved_ticket(self, engineer_user, resolved_ticket):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = resolved_ticket

        service.close_ticket(1, engineer_user)

        assert resolved_ticket.status == TicketStatus.CLOSED

    def test_cannot_close_in_progress_ticket(self, engineer_user, in_progress_ticket):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = in_progress_ticket

        with pytest.raises(ForbiddenException, match="RESOLVED first"):
            service.close_ticket(1, engineer_user)

    def test_employee_cannot_close(self, employee_user, resolved_ticket):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = resolved_ticket

        with pytest.raises(ForbiddenException, match="Only engineers and admins"):
            service.close_ticket(1, employee_user)


# =====================================================
# Tests — reopen_ticket
# =====================================================


class TestReopenTicket:

    def test_reporter_can_reopen_own_closed_ticket(self, employee_user, closed_ticket):
        closed_ticket.created_by_id = employee_user.id
        service = make_service()
        service.ticket_repo.get_by_id.return_value = closed_ticket

        service.reopen_ticket(1, employee_user)

        assert closed_ticket.status == TicketStatus.REOPENED

    def test_reopen_clears_timestamps(self, engineer_user, closed_ticket):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = closed_ticket

        service.reopen_ticket(1, engineer_user)

        assert closed_ticket.closed_at is None
        assert closed_ticket.resolved_at is None

    def test_cannot_reopen_in_progress_ticket(self, engineer_user, in_progress_ticket):
        service = make_service()
        service.ticket_repo.get_by_id.return_value = in_progress_ticket

        with pytest.raises(ForbiddenException, match="CLOSED or RESOLVED"):
            service.reopen_ticket(1, engineer_user)

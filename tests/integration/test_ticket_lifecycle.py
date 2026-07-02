"""
Ticket lifecycle end-to-end: create -> assign -> resolve -> close -> reopen,
plus RBAC denials, through real HTTP requests against a real Postgres.

There's no public "create an engineer/admin account" endpoint (by design —
see backend/api/v1/endpoints/users.py, which only exposes list/activate/
deactivate). Real deployments provision those via database/seeds/*.sql or
an admin using a future user-management UI. Here, _create_active_user()
does the same thing directly against the test database session, then logs
in through the real /auth/login endpoint to get a real JWT — the RBAC
checks under test all happen through that real token, not a shortcut.
"""

from backend.core.security import hash_password
from backend.models.role import Role
from backend.models.user import User

TEST_PASSWORD = "TestPass123!"


# =====================================================
# Helpers
# =====================================================


def _create_active_user(db_session, role_name: str, email: str, username: str) -> User:
    role = db_session.query(Role).filter(Role.name == role_name).one()
    user = User(
        email=email,
        username=username,
        password_hash=hash_password(TEST_PASSWORD),
        full_name=username.replace("_", " ").title(),
        role_id=role.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _login(client, email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_ticket(client, token: str, title: str = "VPN not connecting") -> dict:
    response = client.post(
        "/api/v1/tickets",
        headers=_auth_headers(token),
        json={
            "title": title,
            "description": "Detailed description of the issue, at least 20 characters.",
            "priority": "medium",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


# =====================================================
# Full happy-path lifecycle
# =====================================================


class TestTicketLifecycle:
    def test_full_lifecycle_create_assign_resolve_close_reopen(self, client, db_session):
        # Employee registers and creates a ticket
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "lifecycle.employee@example.com",
                "username": "lifecycle_employee",
                "password": TEST_PASSWORD,
                "full_name": "Lifecycle Employee",
            },
        )
        employee_token = _login(client, "lifecycle.employee@example.com")

        ticket = _create_ticket(client, employee_token)
        assert ticket["status"] == "open"
        assert ticket["assignee"] is None
        ticket_id = ticket["id"]

        # Engineer (provisioned directly, no self-service path) assigns it
        engineer = _create_active_user(
            db_session, "engineer", "lifecycle.engineer@example.com", "lifecycle_engineer"
        )
        db_session.flush()
        engineer_token = _login(client, "lifecycle.engineer@example.com")

        assign_response = client.post(
            f"/api/v1/tickets/{ticket_id}/assign",
            headers=_auth_headers(engineer_token),
            json={"assignee_id": engineer.id},
        )
        assert assign_response.status_code == 200, assign_response.text
        assigned = assign_response.json()
        assert assigned["status"] == "in_progress"
        assert assigned["assignee"]["id"] == engineer.id

        # Engineer resolves it
        resolve_response = client.post(
            f"/api/v1/tickets/{ticket_id}/resolve", headers=_auth_headers(engineer_token)
        )
        assert resolve_response.status_code == 200, resolve_response.text
        resolved = resolve_response.json()
        assert resolved["status"] == "resolved"
        assert resolved["resolved_at"] is not None

        # Engineer closes it
        close_response = client.post(
            f"/api/v1/tickets/{ticket_id}/close", headers=_auth_headers(engineer_token)
        )
        assert close_response.status_code == 200, close_response.text
        closed = close_response.json()
        assert closed["status"] == "closed"
        assert closed["closed_at"] is not None

        # Reporter reopens it — closed_at/resolved_at should clear
        reopen_response = client.post(
            f"/api/v1/tickets/{ticket_id}/reopen", headers=_auth_headers(employee_token)
        )
        assert reopen_response.status_code == 200, reopen_response.text
        reopened = reopen_response.json()
        assert reopened["status"] == "reopened"
        assert reopened["closed_at"] is None
        assert reopened["resolved_at"] is None


# =====================================================
# RBAC denials
# =====================================================


class TestTicketRBAC:
    def test_employee_cannot_assign_ticket(self, client, db_session):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "rbac.assign@example.com",
                "username": "rbac_assign",
                "password": TEST_PASSWORD,
                "full_name": "RBAC Assign",
            },
        )
        token = _login(client, "rbac.assign@example.com")
        ticket = _create_ticket(client, token)

        response = client.post(
            f"/api/v1/tickets/{ticket['id']}/assign",
            headers=_auth_headers(token),
            json={"assignee_id": 1},
        )

        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"

    def test_employee_cannot_resolve_ticket(self, client):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "rbac.resolve@example.com",
                "username": "rbac_resolve",
                "password": TEST_PASSWORD,
                "full_name": "RBAC Resolve",
            },
        )
        token = _login(client, "rbac.resolve@example.com")
        ticket = _create_ticket(client, token)

        response = client.post(
            f"/api/v1/tickets/{ticket['id']}/resolve", headers=_auth_headers(token)
        )

        assert response.status_code == 403

    def test_employee_cannot_close_ticket(self, client):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "rbac.close@example.com",
                "username": "rbac_close",
                "password": TEST_PASSWORD,
                "full_name": "RBAC Close",
            },
        )
        token = _login(client, "rbac.close@example.com")
        ticket = _create_ticket(client, token)

        response = client.post(
            f"/api/v1/tickets/{ticket['id']}/close", headers=_auth_headers(token)
        )

        assert response.status_code == 403

    def test_employee_cannot_view_others_ticket(self, client):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "rbac.owner@example.com",
                "username": "rbac_owner",
                "password": TEST_PASSWORD,
                "full_name": "RBAC Owner",
            },
        )
        owner_token = _login(client, "rbac.owner@example.com")
        ticket = _create_ticket(client, owner_token)

        client.post(
            "/api/v1/auth/register",
            json={
                "email": "rbac.other@example.com",
                "username": "rbac_other",
                "password": TEST_PASSWORD,
                "full_name": "RBAC Other",
            },
        )
        other_token = _login(client, "rbac.other@example.com")

        response = client.get(
            f"/api/v1/tickets/{ticket['id']}", headers=_auth_headers(other_token)
        )

        assert response.status_code == 403


# =====================================================
# State-machine rules (not just role checks)
# =====================================================


class TestTicketStateTransitions:
    def test_cannot_resolve_a_ticket_that_is_still_open(self, client, db_session):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "state.reporter@example.com",
                "username": "state_reporter",
                "password": TEST_PASSWORD,
                "full_name": "State Reporter",
            },
        )
        reporter_token = _login(client, "state.reporter@example.com")
        ticket = _create_ticket(client, reporter_token)

        _create_active_user(
            db_session, "engineer", "state.engineer@example.com", "state_engineer"
        )
        db_session.flush()
        engineer_token = _login(client, "state.engineer@example.com")

        # Ticket is still "open" (never assigned) — resolve should be rejected
        response = client.post(
            f"/api/v1/tickets/{ticket['id']}/resolve", headers=_auth_headers(engineer_token)
        )

        assert response.status_code == 403
        assert "IN_PROGRESS or REOPENED" in response.json()["detail"]

    def test_cannot_close_a_ticket_that_is_not_resolved(self, client, db_session):
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "state2.reporter@example.com",
                "username": "state2_reporter",
                "password": TEST_PASSWORD,
                "full_name": "State2 Reporter",
            },
        )
        reporter_token = _login(client, "state2.reporter@example.com")
        ticket = _create_ticket(client, reporter_token)

        engineer = _create_active_user(
            db_session, "engineer", "state2.engineer@example.com", "state2_engineer"
        )
        db_session.flush()
        engineer_token = _login(client, "state2.engineer@example.com")

        client.post(
            f"/api/v1/tickets/{ticket['id']}/assign",
            headers=_auth_headers(engineer_token),
            json={"assignee_id": engineer.id},
        )

        # Ticket is now "in_progress" (assigned, not resolved) — close should be rejected
        response = client.post(
            f"/api/v1/tickets/{ticket['id']}/close", headers=_auth_headers(engineer_token)
        )

        assert response.status_code == 403
        assert "RESOLVED" in response.json()["detail"]

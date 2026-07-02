"""
API client for helpdesk-ai FastAPI backend.

All HTTP communication lives here — Streamlit pages never
import 'requests' directly. This makes it easy to:
- Change the base URL (dev → staging → prod) in one place
- Add logging or retry logic centrally
- Mock in tests
"""

from __future__ import annotations  # enables "dict | list" syntax on Python 3.9

from typing import Any

import requests

# =====================================================
# Configuration
# =====================================================

BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 10  # seconds


# =====================================================
# Internal helpers
# =====================================================


def _headers(token: str) -> dict:
    """Build Authorization header from JWT token."""
    return {"Authorization": f"Bearer {token}"}


def _handle(response: requests.Response) -> Any:
    """
    Raise a readable error on non-2xx responses.
    Returns parsed JSON on success.
    """
    try:
        response.raise_for_status()
        return response.json()
    except requests.HTTPError:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise ValueError(f"[{response.status_code}] {detail}")


def _handle_binary(response: requests.Response) -> bytes:
    """
    Same error handling as _handle(), but for endpoints that return a raw
    file (report exports) instead of JSON. Calling response.json() on a
    PDF/xlsx body would crash, so this is a separate path rather than a
    branch inside _handle().
    """
    try:
        response.raise_for_status()
        return response.content
    except requests.HTTPError:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise ValueError(f"[{response.status_code}] {detail}")


# =====================================================
# Auth
# =====================================================


def login(email: str, password: str) -> dict:
    """
    POST /auth/login — returns access_token and refresh_token.
    Uses form encoding (OAuth2 requirement).
    """
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": email, "password": password},
        timeout=TIMEOUT,
    )
    return _handle(response)


def get_current_user(token: str) -> dict:
    """GET /auth/me — returns current user profile."""
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


# =====================================================
# Tickets
# =====================================================


def list_tickets(
    token: str,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    priority: str | None = None,
) -> dict:
    """GET /tickets — paginated list with optional filters."""
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority

    response = requests.get(
        f"{BASE_URL}/tickets",
        headers=_headers(token),
        params=params,
        timeout=TIMEOUT,
    )
    return _handle(response)


def get_ticket(token: str, ticket_id: int) -> dict:
    """GET /tickets/{ticket_id} — single ticket detail."""
    response = requests.get(
        f"{BASE_URL}/tickets/{ticket_id}",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


def create_ticket(token: str, payload: dict) -> dict:
    """POST /tickets — create a new ticket."""
    response = requests.post(
        f"{BASE_URL}/tickets",
        headers=_headers(token),
        json=payload,
        timeout=TIMEOUT,
    )
    return _handle(response)


def assign_ticket(token: str, ticket_id: int, assignee_id: int) -> dict:
    """POST /tickets/{ticket_id}/assign."""
    response = requests.post(
        f"{BASE_URL}/tickets/{ticket_id}/assign",
        headers=_headers(token),
        json={"assignee_id": assignee_id},
        timeout=TIMEOUT,
    )
    return _handle(response)


def resolve_ticket(token: str, ticket_id: int) -> dict:
    """POST /tickets/{ticket_id}/resolve."""
    response = requests.post(
        f"{BASE_URL}/tickets/{ticket_id}/resolve",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


def close_ticket(token: str, ticket_id: int) -> dict:
    """POST /tickets/{ticket_id}/close."""
    response = requests.post(
        f"{BASE_URL}/tickets/{ticket_id}/close",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


def reopen_ticket(token: str, ticket_id: int) -> dict:
    """POST /tickets/{ticket_id}/reopen."""
    response = requests.post(
        f"{BASE_URL}/tickets/{ticket_id}/reopen",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


def add_comment(token: str, ticket_id: int, body: str, is_internal: bool = False) -> dict:
    """POST /tickets/{ticket_id}/comments."""
    response = requests.post(
        f"{BASE_URL}/tickets/{ticket_id}/comments",
        headers=_headers(token),
        json={"body": body, "is_internal": is_internal},
        timeout=TIMEOUT,
    )
    return _handle(response)


def get_comments(token: str, ticket_id: int) -> list:
    """GET /tickets/{ticket_id}/comments."""
    response = requests.get(
        f"{BASE_URL}/tickets/{ticket_id}/comments",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


# =====================================================
# Dashboard
# =====================================================


def get_dashboard_summary(token: str) -> dict:
    """GET /dashboard/summary."""
    response = requests.get(
        f"{BASE_URL}/dashboard/summary",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


def get_dashboard_trends(token: str) -> list:
    """GET /dashboard/trends."""
    response = requests.get(
        f"{BASE_URL}/dashboard/trends",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


def get_sla_stats(token: str) -> list:
    """GET /dashboard/sla."""
    response = requests.get(
        f"{BASE_URL}/dashboard/sla",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


def get_engineer_stats(token: str) -> list:
    """GET /dashboard/engineers."""
    response = requests.get(
        f"{BASE_URL}/dashboard/engineers",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


def get_heatmap_data(token: str) -> list:
    """GET /dashboard/heatmap — ticket counts by day-of-week x hour."""
    response = requests.get(
        f"{BASE_URL}/dashboard/heatmap",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


# =====================================================
# Users
# =====================================================


def list_users(
    token: str,
    page: int = 1,
    page_size: int = 20,
    role: str | None = None,
    department_id: int | None = None,
    is_active: bool | None = None,
) -> dict:
    """GET /users — paginated, filterable roster. Engineer/admin only."""
    params: dict[str, Any] = {"page": page, "page_size": page_size}
    if role:
        params["role"] = role
    if department_id:
        params["department_id"] = department_id
    if is_active is not None:
        params["is_active"] = is_active

    response = requests.get(
        f"{BASE_URL}/users",
        headers=_headers(token),
        params=params,
        timeout=TIMEOUT,
    )
    return _handle(response)


def deactivate_user(token: str, user_id: int) -> dict:
    """POST /users/{user_id}/deactivate. Admin only."""
    response = requests.post(
        f"{BASE_URL}/users/{user_id}/deactivate",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


def activate_user(token: str, user_id: int) -> dict:
    """POST /users/{user_id}/activate. Admin only."""
    response = requests.post(
        f"{BASE_URL}/users/{user_id}/activate",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


# =====================================================
# SLA Policies
# =====================================================


def get_sla_policies(token: str) -> list:
    """GET /sla-policies. Engineer/admin only."""
    response = requests.get(
        f"{BASE_URL}/sla-policies",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(response)


def update_sla_policy(token: str, policy_id: int, payload: dict) -> dict:
    """PATCH /sla-policies/{policy_id}. Admin only."""
    response = requests.patch(
        f"{BASE_URL}/sla-policies/{policy_id}",
        headers=_headers(token),
        json=payload,
        timeout=TIMEOUT,
    )
    return _handle(response)


# =====================================================
# Reports
# =====================================================

_REPORT_ENDPOINTS = {
    "csv": "csv",
    "excel": "excel",
    "pdf": "pdf",
}


def export_tickets_report(
    token: str,
    fmt: str,
    status: str | None = None,
    priority: str | None = None,
    department_id: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> bytes:
    """
    GET /reports/tickets/{csv,excel,pdf} — returns raw file bytes.

    fmt must be one of "csv", "excel", "pdf". date_from/date_to are
    ISO date strings ("YYYY-MM-DD") — Streamlit's st.date_input gives
    a date object, so callers should str() it first.
    """
    if fmt not in _REPORT_ENDPOINTS:
        raise ValueError(f"Unknown report format: {fmt!r}. Expected one of {list(_REPORT_ENDPOINTS)}.")

    params: dict[str, Any] = {}
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    if department_id:
        params["department_id"] = department_id
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    response = requests.get(
        f"{BASE_URL}/reports/tickets/{_REPORT_ENDPOINTS[fmt]}",
        headers=_headers(token),
        params=params,
        timeout=TIMEOUT,
    )
    return _handle_binary(response)

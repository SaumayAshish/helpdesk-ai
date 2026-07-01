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

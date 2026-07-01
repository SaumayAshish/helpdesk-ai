"""
Admin Users page — view the full user roster and activate/deactivate accounts.

Admin-only. Engineers can call GET /users too (they need it for the ticket
assignee picker — see pages/4_Ticket_Detail.py), but account management
(deactivate/activate) is restricted to admins at the API layer, so this
page is gated the same way here rather than showing controls that would
just 403 for an engineer.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st

from frontend.components.auth import get_role, get_user, logout, require_login
from frontend import api_client

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Users | Helpdesk AI", page_icon="👥", layout="wide")

# ── Auth gate ─────────────────────────────────────────────────────────────────
token = require_login()
user = get_user()
role = get_role()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 👤 {user.get('full_name', 'User')}")
    st.markdown(f"**Role:** {role.title()}")
    st.divider()
    if st.button("🚪 Sign Out", use_container_width=True):
        logout()

# ── Role guard: admin only ────────────────────────────────────────────────────
if role != "admin":
    st.error("⛔ Access denied. This page is for admins only.")
    st.stop()

# ── Page header ───────────────────────────────────────────────────────────────
st.title("👥 User Management")
st.caption("View the roster and manage account access.")

# ── Filters row ───────────────────────────────────────────────────────────────
col_role, col_status, col_page = st.columns([2, 2, 1])

with col_role:
    role_options = ["All", "employee", "engineer", "admin"]
    selected_role = st.selectbox("Role", role_options)

with col_status:
    status_options = ["All", "Active", "Inactive"]
    selected_status = st.selectbox("Status", status_options)

with col_page:
    page = st.number_input("Page", min_value=1, value=1, step=1)

role_filter = None if selected_role == "All" else selected_role
is_active_filter = {"All": None, "Active": True, "Inactive": False}[selected_status]

# ── Fetch users ────────────────────────────────────────────────────────────────
try:
    result = api_client.list_users(
        token,
        page=page,
        page_size=20,
        role=role_filter,
        is_active=is_active_filter,
    )
    users = result.get("items", [])
    total = result.get("total", 0)
except ValueError as e:
    st.error(str(e))
    st.stop()
except Exception:
    st.error("⚠️ Could not load users. Is the backend running?")
    st.stop()

st.caption(f"Showing {len(users)} of {total} user(s)  |  Page {page}")

if not users:
    st.info("No users match the selected filters.")
    st.stop()

st.divider()

# ── Roster table ───────────────────────────────────────────────────────────────
# One row per user: identity, role/department, status, and a toggle action.
# The toggle button always shows the action available given the CURRENT
# status (Deactivate for active users, Activate for inactive ones) rather
# than a static label, so there is only ever one valid next action visible.
header_cols = st.columns([3, 2, 2, 2, 2])
for col, label in zip(header_cols, ["Name", "Role", "Department", "Status", "Action"]):
    col.markdown(f"**{label}**")

for u in users:
    row = st.columns([3, 2, 2, 2, 2])
    row[0].write(f"{u['full_name']}  \n:gray[{u['email']}]")
    row[1].write(u["role"].title())
    row[2].write(u.get("department") or "—")
    row[3].write("🟢 Active" if u["is_active"] else "⚫ Inactive")

    is_self = u["id"] == user.get("id")
    with row[4]:
        if is_self:
            st.caption("This is you")
        elif u["is_active"]:
            if st.button("Deactivate", key=f"deactivate_{u['id']}", use_container_width=True):
                try:
                    api_client.deactivate_user(token, u["id"])
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
        else:
            if st.button("Activate", key=f"activate_{u['id']}", use_container_width=True):
                try:
                    api_client.activate_user(token, u["id"])
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

st.divider()

if total > page * 20:
    st.info("There are more users. Increase the page number above to see them.")

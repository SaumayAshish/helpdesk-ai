"""
Authentication helpers shared across all pages.
"""

import streamlit as st

from .. import api_client  # relative import: frontend/api_client.py


def require_login() -> str:
    """
    Enforce authentication on any page.

    - On the home page (app.py): renders the login form inline.
    - On all other pages: redirects to app.py using st.switch_page().

    Returns the JWT token if already authenticated.

    Usage (add to top of every page):
        token = require_login()
    """
    if "token" not in st.session_state:
        # Detect whether we're on the main app page or a sub-page.
        # __file__ for pages lives in frontend/pages/; app.py lives in frontend/.
        import inspect
        caller_file = inspect.stack()[1].filename
        is_home = caller_file.endswith("app.py")

        if is_home:
            # Login form belongs here — render it and halt.
            _render_login_form()
        else:
            # On any other page, redirect to the home/login page.
            st.warning("Please sign in to continue.")
            st.switch_page("app.py")

        st.stop()

    return st.session_state["token"]


def get_user() -> dict:
    """Return the current user dict from session state."""
    return st.session_state.get("user", {})


def get_role() -> str:
    """Return the current user's role name."""
    return get_user().get("role", "employee")


def logout() -> None:
    """Clear session state and rerun to show login page."""
    st.session_state.clear()
    st.rerun()


def _render_login_form() -> None:
    """Render the login form and handle submission."""
    st.title("🎫 Helpdesk AI")
    st.subheader("Sign in to your account")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@company.com")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In", use_container_width=True)

    if submit:
        if not email or not password:
            st.error("Please enter both email and password.")
            return

        with st.spinner("Signing in..."):
            try:
                tokens = api_client.login(email, password)
                user = api_client.get_current_user(tokens["access_token"])

                # Store in session
                st.session_state["token"] = tokens["access_token"]
                st.session_state["user"] = user

                st.success(f"Welcome, {user['full_name']}!")
                st.rerun()  # reload page now that token exists

            except ValueError as e:
                st.error(str(e))
            except Exception:
                st.error("⚠️ Cannot connect to the backend. Make sure the FastAPI server is running on port 8000.")

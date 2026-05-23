import streamlit as st

LOGIN_SESSION_KEYS = (
    "login_is_superadmin",
    "login_username_input",
    "login_password_input",
    "superadmin_portal_choice",
    "login_username_applied",
    "login_username_confirmed",
)


def init_session_state() -> None:
    st.session_state.setdefault("current_user", None)
    st.session_state.setdefault("active_page", "Login")


def clear_login_form_state() -> None:
    for key in LOGIN_SESSION_KEYS:
        st.session_state.pop(key, None)


def login_user(user_payload: dict, *, portal: str | None = None) -> None:
    if portal is not None:
        user_payload = {**user_payload, "portal": portal}
    st.session_state["current_user"] = user_payload
    if user_payload.get("role") == "superadmin" and user_payload.get("portal") == "users":
        st.session_state["active_page"] = "Dashboard"
        st.session_state["nav_page"] = "Dashboard"
    else:
        st.session_state["active_page"] = "Dashboard"
        st.session_state["nav_page"] = "Dashboard"


def switch_superadmin_portal(portal: str) -> None:
    """Switch superadmin between Admin UI (admin) and User Management (users)."""
    user = get_current_user()
    if not user or user.get("role") != "superadmin" or user.get("portal") == portal:
        return

    from src.db.database import get_db_session
    from src.db import models as _db_models  # noqa: F401
    from src.db.models import User
    from src.services.user_service import build_user_payload, enrich_staff_user_payload

    with get_db_session() as session:
        db_user = session.get(User, user["id"])
        if not db_user or not db_user.is_active:
            return
        payload = enrich_staff_user_payload(
            session,
            build_user_payload(db_user, portal=portal),
            portal=portal,
        )

    from ui.components.sidebar_nav import SIDEBAR_NAV_RADIO_KEY

    st.session_state.pop(SIDEBAR_NAV_RADIO_KEY, None)
    login_user(payload, portal=portal)


def logout_user() -> None:
    st.session_state["current_user"] = None
    st.session_state["active_page"] = "Login"
    clear_login_form_state()


def get_current_user() -> dict | None:
    return st.session_state.get("current_user")


def require_role(allowed_roles: set[str]) -> bool:
    user = get_current_user()
    return bool(user and user["role"] in allowed_roles)

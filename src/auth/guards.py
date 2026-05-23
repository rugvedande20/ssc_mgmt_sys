import streamlit as st


def init_session_state() -> None:
    st.session_state.setdefault("current_user", None)
    st.session_state.setdefault("active_page", "Login")


def login_user(user_payload: dict, *, portal: str | None = None) -> None:
    if portal is not None:
        user_payload = {**user_payload, "portal": portal}
    st.session_state["current_user"] = user_payload
    if user_payload.get("role") == "superadmin" and user_payload.get("portal") == "users":
        st.session_state["active_page"] = "User Management"
        st.session_state["nav_page"] = "User Management"
    else:
        st.session_state["active_page"] = "Dashboard"
        st.session_state["nav_page"] = "Dashboard"


def logout_user() -> None:
    st.session_state["current_user"] = None
    st.session_state["active_page"] = "Login"


def get_current_user() -> dict | None:
    return st.session_state.get("current_user")


def require_role(allowed_roles: set[str]) -> bool:
    user = get_current_user()
    return bool(user and user["role"] in allowed_roles)

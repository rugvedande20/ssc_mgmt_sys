import streamlit as st


def init_session_state() -> None:
    st.session_state.setdefault("current_user", None)
    st.session_state.setdefault("active_page", "Login")


def login_user(user_payload: dict) -> None:
    st.session_state["current_user"] = user_payload
    st.session_state["active_page"] = "Dashboard"


def logout_user() -> None:
    st.session_state["current_user"] = None
    st.session_state["active_page"] = "Login"


def get_current_user() -> dict | None:
    return st.session_state.get("current_user")


def require_role(allowed_roles: set[str]) -> bool:
    user = get_current_user()
    return bool(user and user["role"] in allowed_roles)

import streamlit as st

from src.auth.guards import login_user
from src.auth.service import authenticate_user
from src.db.database import get_db_session
from src.services.user_service import build_user_payload


def render() -> None:
    st.title("Login")
    st.caption("Role-based access for students and admins.")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        with get_db_session() as session:
            user = authenticate_user(session, username=username.strip(), password=password)
        if not user:
            st.error("Invalid credentials. Please try again.")
            return

        login_user(build_user_payload(user))
        st.success("Login successful.")
        st.rerun()

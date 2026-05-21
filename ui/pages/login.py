import streamlit as st

from src.auth.guards import login_user
from src.auth.service import authenticate_user
from src.db.database import get_db_session
from src.services.user_service import build_user_payload


def render() -> None:
    st.title("Login")
    st.caption("Sign in as a school teacher/admin or as a student (Class 6–10).")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        with get_db_session() as session:
            user = authenticate_user(session, username=username.strip(), password=password)
            user_payload = build_user_payload(user) if user else None
        if not user_payload:
            st.error("Invalid credentials. Please try again.")
            return

        login_user(user_payload)
        st.success("Login successful.")
        st.rerun()

    with st.expander("Demo credentials"):
        st.markdown(
            """
            - **Admin:** `admin` / `Admin@123`
            - **Students:** accounts created by your admin under Student Management
            """
        )

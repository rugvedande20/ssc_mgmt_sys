from __future__ import annotations

import streamlit as st

from src.db.database import get_db_session
from src.services.password_change_service import admin_reset_student_password
from src.services.student_credentials import build_login_password
from src.utils.admin_context import student_scope_for_user


def render_admin_reset_password_panel(
    current_user: dict,
    *,
    student_id: int,
    student_username: str,
    student_name: str,
    key_prefix: str,
) -> None:
    st.markdown("### Reset student password")
    st.caption(
        f"Set a new password for **{student_name}** when they cannot sign in. "
        "The old password is not required."
    )

    default_password = build_login_password(student_username)

    col_custom, col_default = st.columns(2)
    with col_default:
        if st.button(
            "Reset to default password",
            use_container_width=True,
            key=f"{key_prefix}_default_btn",
        ):
            try:
                with get_db_session() as session:
                    admin_reset_student_password(
                        session,
                        student_id,
                        default_password,
                        **student_scope_for_user(current_user),
                    )
                st.success(f"Password reset. Share this with the student: `{default_password}`")
            except ValueError as exc:
                st.error(str(exc))

    with col_custom:
        st.caption(f"Default format: `{default_password}`")

    with st.form(f"{key_prefix}_custom_form", clear_on_submit=True):
        new_password = st.text_input("Custom new password", type="password")
        confirm_password = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Set custom password", use_container_width=True, type="primary")

    if submitted:
        if new_password != confirm_password:
            st.error("Passwords do not match.")
        else:
            try:
                with get_db_session() as session:
                    applied = admin_reset_student_password(
                        session,
                        student_id,
                        new_password,
                        **student_scope_for_user(current_user),
                    )
                st.success(f"Password updated. Share this with the student: `{applied}`")
            except ValueError as exc:
                st.error(str(exc))

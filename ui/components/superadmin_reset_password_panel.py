from __future__ import annotations

import streamlit as st

from src.db.database import get_db_session
from src.services.password_change_service import superadmin_reset_staff_password
from src.services.staff_credentials import default_staff_role_password


def render_superadmin_reset_password_panel(
    *,
    staff_id: int,
    staff_name: str,
    first_name: str,
    last_name: str,
    full_name: str,
    role: str,
    key_prefix: str,
) -> None:
    st.markdown("### Reset staff password")
    st.caption(
        f"Set a new password for **{staff_name}** ({role}) when they cannot sign in. "
        "The old password is not required."
    )

    default_password = default_staff_role_password(
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        role=role,
    )

    col_custom, col_default = st.columns(2)
    with col_default:
        if st.button(
            "Reset to default password",
            use_container_width=True,
            key=f"{key_prefix}_default_btn",
        ):
            try:
                with get_db_session() as session:
                    superadmin_reset_staff_password(session, staff_id, default_password)
                st.success(f"Password reset. Share this with the user: `{default_password}`")
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
                    applied = superadmin_reset_staff_password(session, staff_id, new_password)
                st.success(f"Password updated. Share this with the user: `{applied}`")
            except ValueError as exc:
                st.error(str(exc))

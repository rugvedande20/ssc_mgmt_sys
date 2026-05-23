from __future__ import annotations

import streamlit as st

from src.db.database import get_db_session
from src.services.password_change_service import change_password


def render_change_password_panel(current_user: dict, *, key_prefix: str = "change_pwd") -> None:
    st.markdown("### Change password")
    st.caption("Enter your current password, then choose a new one.")

    with st.form(f"{key_prefix}_form", clear_on_submit=True):
        old_password = st.text_input("Current password", type="password")
        new_password = st.text_input("New password", type="password")
        confirm_password = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Update password", use_container_width=True, type="primary")

    if submitted:
        if new_password != confirm_password:
            st.error("New passwords do not match.")
        else:
            try:
                with get_db_session() as session:
                    change_password(
                        session,
                        current_user["id"],
                        old_password,
                        new_password,
                    )
                st.success("Password updated successfully.")
            except ValueError as exc:
                st.error(str(exc))

import streamlit as st

from config.school_context import FUTURE_SCOPE_NOTE, PROFILE_FIELD_LABELS, format_class
from src.db.database import get_db_session
from src.services.student_service import get_student_profile_payload
from src.utils.helpers import is_student_profile_complete, profile_completeness_percent
from ui.components.common import render_profile_completeness
from ui.components.layout import section
from ui.components.page_chrome import render_page_header, render_snapshot_grid
from ui.components.change_password_panel import render_change_password_panel
from ui.components.student_profile_form import render_student_profile_form


def render(current_user: dict) -> None:
    edit_mode = st.session_state.pop("profile_edit_mode", False)

    with get_db_session() as session:
        profile = get_student_profile_payload(session, current_user["id"])

    if not is_student_profile_complete(profile):
        render_page_header(
            "My School Profile",
            "Finish setup from **Complete Profile** in the menu first.",
            badge_text="Incomplete",
            badge_variant="amber",
        )
        render_profile_completeness(profile)
        st.info("Your profile is not complete yet. Open **Complete Profile** to finish all required fields.")
        return

    render_page_header(
        "My School Profile",
        f"View and edit your details for better guidance. {FUTURE_SCOPE_NOTE}",
        badge_text="Complete",
        badge_variant="emerald",
    )

    if not edit_mode:
        with section("Your details", "Summary of what teachers and guidance tools use."):
            render_profile_completeness(profile)
            render_snapshot_grid(
                [
                    (PROFILE_FIELD_LABELS["department"], profile["department"] or "—"),
                    (PROFILE_FIELD_LABELS["semester"], format_class(profile["semester"])),
                    (PROFILE_FIELD_LABELS["family_income_band"], profile["family_income_band"] or "—"),
                    (PROFILE_FIELD_LABELS["internet_access"], profile["internet_access"] or "—"),
                ]
            )
            if st.button("Edit profile", type="primary", use_container_width=True):
                st.session_state["profile_edit_mode"] = True
                st.rerun()

    if edit_mode:
        with section("Edit profile", "Update anytime — changes save instantly."):
            if st.button("← Back to profile summary"):
                st.rerun()
            render_student_profile_form(
                current_user["id"],
                profile,
                form_key="student_profile_edit",
                submit_label="Save changes",
            )

    with section("Account security", "Update your sign-in password."):
        render_change_password_panel(current_user, key_prefix="student_profile_pwd")

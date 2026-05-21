import streamlit as st

from config.school_context import FUTURE_SCOPE_NOTE
from src.db.database import get_db_session
from src.services.student_service import get_student_profile_payload
from src.utils.helpers import is_student_profile_complete, profile_completeness_percent
from ui.components.common import render_profile_completeness
from ui.components.layout import section
from ui.components.page_chrome import render_highlight_panel, render_page_header
from ui.components.student_profile_form import render_student_profile_form


def render(current_user: dict) -> None:
    with get_db_session() as session:
        profile = get_student_profile_payload(session, current_user["id"])

    if not is_student_profile_complete(profile):
        render_page_header(
            "My School Profile",
            "Finish setup from **Complete Profile** in the menu first.",
            badge_text="Incomplete",
            badge_variant="amber",
        )
        completeness = profile_completeness_percent(profile)
        render_profile_completeness(profile)
        st.info("Your profile is not complete yet. Open **Complete Profile** to finish all required fields.")
        return

    render_page_header(
        "My School Profile",
        f"Keep your details up to date for better guidance. {FUTURE_SCOPE_NOTE}",
        badge_text="Complete",
        badge_variant="emerald",
    )

    render_highlight_panel(
        "You're all set",
        "Teachers and the guidance system use this information alongside your assessments.",
        variant="emerald",
        icon="✓",
    )

    with section("Profile completeness", "All required fields for Class 6–10 students."):
        render_profile_completeness(profile)

    with section("Edit your details", "Update anytime — changes save instantly."):
        render_student_profile_form(
            current_user["id"],
            profile,
            form_key="student_profile_edit",
            submit_label="Save changes",
        )

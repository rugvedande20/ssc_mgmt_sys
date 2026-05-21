import streamlit as st

from config.school_context import FUTURE_SCOPE_NOTE
from src.db.database import get_db_session
from src.services.student_service import get_student_profile_payload
from src.utils.helpers import get_missing_profile_fields, profile_completeness_percent
from ui.components.common import render_profile_completeness
from ui.components.layout import section
from ui.components.page_chrome import render_highlight_panel, render_page_header
from ui.components.student_profile_form import render_student_profile_form


def render(current_user: dict) -> None:
    with get_db_session() as session:
        profile = get_student_profile_payload(session, current_user["id"])

    completeness = profile_completeness_percent(profile)
    missing = get_missing_profile_fields(profile)

    render_page_header(
        "Complete your profile",
        f"Hi {current_user['full_name']} — one-time setup to unlock your student dashboard.",
        badge_text=f"{completeness}% done",
        badge_variant="violet" if completeness < 100 else "emerald",
    )

    render_highlight_panel(
        "Why we ask for this",
        f"Your school details and interests help teachers support you and power future assessments. {FUTURE_SCOPE_NOTE}",
        variant="sky",
        icon="🎓",
    )

    with section("Setup progress", "Track what is left before you can explore careers."):
        render_profile_completeness(profile, title="Setup progress")
        if missing:
            st.warning("Still needed: " + ", ".join(missing))
        else:
            st.success("All required fields are filled. Save below to unlock the full menu.")

    with section("Your school profile", "Three short sections — takes about 5 minutes."):
        render_student_profile_form(
            current_user["id"],
            profile,
            form_key="student_onboarding_profile",
            submit_label="Save & continue",
        )

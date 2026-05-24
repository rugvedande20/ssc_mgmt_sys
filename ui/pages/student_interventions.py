import streamlit as st

from config.school_context import FUTURE_SCOPE_NOTE
from src.db.database import get_db_session
from src.services.intervention_service import get_student_interventions_payload
from ui.components.intervention_display import render_student_interventions_page
from ui.components.layout import section
from ui.components.page_chrome import render_page_header


def render(current_user: dict) -> None:
    with get_db_session() as session:
        payload = get_student_interventions_payload(session, current_user["id"])

    render_page_header(
        "My Support & Interventions",
        f"Your scheduled counseling sessions and support plan from your school team. {FUTURE_SCOPE_NOTE}",
        badge_text="Student",
        badge_variant="sky",
    )

    with section(
        "Support plan",
        "Based on your school's latest review — sessions and modules your counselors maintain for you.",
    ):
        render_student_interventions_page(payload)

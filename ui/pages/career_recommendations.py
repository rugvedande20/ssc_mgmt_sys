import streamlit as st

from config.school_context import FUTURE_SCOPE_NOTE
from src.db.database import get_db_session
from src.services.student_service import get_student_dashboard_payload, get_student_profile_payload
from src.utils.helpers import is_student_profile_complete, parse_json_list
from ui.components.layout import section
from ui.components.page_chrome import render_career_card, render_highlight_panel, render_page_header


def render(current_user: dict) -> None:
    render_page_header(
        "Career Ideas & Pathways",
        f"Explore careers that may suit your interests (Class 6–10). {FUTURE_SCOPE_NOTE}",
        badge_text="Explorer",
        badge_variant="violet",
    )

    with get_db_session() as session:
        profile = get_student_profile_payload(session, current_user["id"])
        if not is_student_profile_complete(profile):
            render_highlight_panel(
                "Profile required",
                "Complete your school profile first — open **Complete Profile** from the menu.",
                variant="amber",
                icon="!",
            )
            return
        payload = get_student_dashboard_payload(session, current_user["id"])

    recommendations = payload["recommendations"]
    latest_assessment = payload["latest_assessment"]

    if not latest_assessment:
        render_highlight_panel(
            "Interest assessment needed",
            "Complete the interest assessment so future career ideas can use your profile.",
            variant="sky",
            icon="◆",
        )
    else:
        render_highlight_panel(
            "You're on track",
            "Personalized career matching is coming next — preview sample ideas below.",
            variant="emerald",
            icon="✓",
        )

    with section("Career matches (preview)", "Demo suggestions — real engine connects in the next milestone."):
        if recommendations:
            for recommendation in recommendations:
                render_career_card(
                    career_name=recommendation["career_name"],
                    match_score=recommendation["match_score"],
                    rationale=recommendation["rationale"],
                    skills=parse_json_list(recommendation["skill_gap"]),
                    activities=parse_json_list(recommendation["certifications"]),
                )
        else:
            st.info("No career ideas are stored for your account yet.")

    with section("Coming next", "What the full career module will include."):
        st.markdown(
            """
            - Career ideas matched to your interests and school marks
            - Simple learning roadmaps (subjects, clubs, projects)
            - Activities and courses to try at your age
            - Later: Class 11–12 stream guidance and market trends
            """
        )

import streamlit as st

from config.school_context import FUTURE_SCOPE_NOTE, GRADE_LABELS, PROFILE_FIELD_LABELS, format_class
from src.db.database import get_db_session
from src.services.student_service import get_student_dashboard_payload
from src.utils.helpers import parse_json_list, profile_completeness_percent
from ui.components.common import render_profile_completeness, render_student_next_steps


def render(current_user: dict) -> None:
    st.title("My Dashboard")
    st.caption(f"Your school profile, interest assessment, and early career ideas (Class 6–10). {FUTURE_SCOPE_NOTE}")

    with get_db_session() as session:
        payload = get_student_dashboard_payload(session, current_user["id"])

    profile = payload["profile"]
    latest_assessment = payload["latest_assessment"]
    recommendations = payload["recommendations"]
    completeness = profile_completeness_percent(profile)
    profile_complete = completeness >= 80
    assessment_done = latest_assessment is not None
    has_recommendations = len(recommendations) > 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Profile Completeness", f"{completeness}%")
    col2.metric("Interest Assessment", "Completed" if assessment_done else "Pending")
    col3.metric("Career Ideas", len(recommendations))

    render_student_next_steps(
        profile_complete=profile_complete,
        assessment_done=assessment_done,
        has_recommendations=has_recommendations,
    )

    st.divider()
    st.subheader("Profile Snapshot")
    if profile:
        render_profile_completeness(profile)
        st.write(
            {
                PROFILE_FIELD_LABELS["department"]: profile["department"] or "—",
                PROFILE_FIELD_LABELS["semester"]: format_class(profile["semester"]),
                PROFILE_FIELD_LABELS["family_income_band"]: profile["family_income_band"] or "—",
                PROFILE_FIELD_LABELS["internet_access"]: profile["internet_access"] or "—",
            }
        )
        if completeness < 80:
            st.caption("Complete your profile (especially interests and strengths) for better career ideas.")
    else:
        st.warning("Your profile is not set up yet. Open **Profile** from the sidebar to get started.")

    st.subheader("Latest Interest Assessment")
    if latest_assessment:
        st.write(latest_assessment["summary"])
        st.caption(f"Top interest areas: {latest_assessment['top_codes']}")
    else:
        st.info("Take the interest assessment from the sidebar when you are ready.")

    st.subheader("Career Ideas For You")
    if recommendations:
        st.caption("Demo suggestions from sample data. Personalized recommendations will come in the next milestone.")
        for recommendation in recommendations:
            st.markdown(f"**{recommendation['career_name']}** — {recommendation['match_score']:.0f}% match")
            st.write(recommendation["rationale"])
            skills = parse_json_list(recommendation["skill_gap"])
            activities = parse_json_list(recommendation["certifications"])
            if skills:
                st.caption(f"Skills to build: {', '.join(skills)}")
            if activities:
                st.caption(f"Activities & courses to try: {', '.join(activities)}")
    else:
        st.info("Career ideas will appear here after you complete your profile and interest assessment.")

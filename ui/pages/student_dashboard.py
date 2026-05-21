import streamlit as st

from config.school_context import FUTURE_SCOPE_NOTE, PROFILE_FIELD_LABELS, format_class
from src.db.database import get_db_session
from src.services.student_service import get_student_dashboard_payload
from src.utils.helpers import is_student_profile_complete, parse_json_list, profile_completeness_percent
from ui.components.common import render_profile_completeness, render_student_next_steps
from ui.components.layout import section
from ui.components.page_chrome import render_highlight_panel, render_page_header, render_snapshot_grid


def render(current_user: dict) -> None:
    with get_db_session() as session:
        payload = get_student_dashboard_payload(session, current_user["id"])

    profile = payload["profile"]
    latest_assessment = payload["latest_assessment"]
    recommendations = payload["recommendations"]
    completeness = profile_completeness_percent(profile)
    profile_complete = is_student_profile_complete(profile)
    assessment_done = latest_assessment is not None
    has_recommendations = len(recommendations) > 0

    render_page_header(
        "My Dashboard",
        f"Your journey through profile, interests, and early career ideas. {FUTURE_SCOPE_NOTE}",
        badge_text="Student",
        badge_variant="sky",
    )

    metric_cols = st.columns(3)
    metric_cols[0].metric("Profile", f"{completeness}%")
    metric_cols[1].metric("Interest assessment", "Done" if assessment_done else "Pending")
    metric_cols[2].metric("Career ideas", len(recommendations))

    with section("Your journey", "Three milestones — same flow your teachers see on their dashboard."):
        render_student_next_steps(
            profile_complete=profile_complete,
            assessment_done=assessment_done,
            has_recommendations=has_recommendations,
        )

    with section("Profile snapshot", "Quick view of your school context."):
        if profile:
            render_profile_completeness(profile)
            render_snapshot_grid(
                [
                    (PROFILE_FIELD_LABELS["department"], profile["department"] or "—"),
                    (PROFILE_FIELD_LABELS["semester"], format_class(profile["semester"])),
                    (PROFILE_FIELD_LABELS["family_income_band"], profile["family_income_band"] or "—"),
                    (PROFILE_FIELD_LABELS["internet_access"], profile["internet_access"] or "—"),
                ]
            )
            if not profile_complete:
                st.caption("Update **Profile** anytime if your interests or school details change.")
        else:
            st.warning("Your profile is not set up yet.")

    with section(
        "Latest interest assessment",
        "Summary from your most recent RIASEC-style questionnaire.",
    ):
        if latest_assessment:
            render_highlight_panel(
                "Your interest profile",
                latest_assessment["summary"],
                variant="violet",
                icon="✨",
            )
            st.caption(f"Top interest areas: {latest_assessment['top_codes']}")
        else:
            st.info("Take the **Interest Assessment** from the sidebar when you are ready.")

    with section("Career ideas for you", "Early pathways matched to your profile (demo preview)."):
        if recommendations:
            st.caption("Sample ideas for now — personalized recommendations are coming next.")
            for recommendation in recommendations:
                skills = parse_json_list(recommendation["skill_gap"])
                activities = parse_json_list(recommendation["certifications"])
                st.markdown(f"**{recommendation['career_name']}** — {recommendation['match_score']:.0f}% match")
                st.write(recommendation["rationale"])
                if skills:
                    st.caption(f"Skills to build: {', '.join(skills)}")
                if activities:
                    st.caption(f"Activities to try: {', '.join(activities)}")
                st.divider()
        else:
            st.info("Career ideas appear after you complete your profile and interest assessment.")

import streamlit as st

from config.school_context import FUTURE_SCOPE_NOTE
from src.db.database import get_db_session
from src.services.career_recommendation_service import generate_career_guidance, get_student_career_payload
from src.services.student_service import get_student_dashboard_payload, get_student_profile_payload
from src.utils.helpers import is_student_profile_complete, parse_json_list
from ui.components.activity_meta import render_activity_caption
from ui.components.layout import section
from ui.components.page_chrome import render_career_card, render_highlight_panel, render_page_header


def render(current_user: dict) -> None:
    render_page_header(
        "Career Ideas & Pathways",
        f"Your future-oriented career guidance report. {FUTURE_SCOPE_NOTE}",
        badge_text="Future-fit",
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
        dashboard = get_student_dashboard_payload(session, current_user["id"])
        career_payload = get_student_career_payload(session, current_user["id"])

    latest_assessment = dashboard.get("latest_assessment")
    snapshot = career_payload.get("snapshot")
    recommendations = career_payload.get("recommendations") or []
    has_report = snapshot is not None

    with section(
        "Generate your career guidance",
        "Uses your Interest Assessment, academic records, profile, and 5-year labour outlook.",
    ):
        if not latest_assessment:
            st.info("Complete the **Interest Assessment** first, then return here to generate your report.")
        elif not has_report:
            if st.button("Generate career guidance report", type="primary", use_container_width=True):
                try:
                    with get_db_session() as session:
                        generate_career_guidance(session, current_user["id"])
                    st.success("Report saved below.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        else:
            st.caption("Re-run when your class or marks change to refresh matches.")
            if st.button("Refresh career guidance report", type="primary", use_container_width=True):
                try:
                    with get_db_session() as session:
                        generate_career_guidance(session, current_user["id"])
                    st.success("Report updated.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    if not has_report:
        render_highlight_panel(
            "No report yet",
            "Generate your career guidance report using the button above (after Interest Assessment).",
            variant="sky",
            icon="◆",
        )
        return

    render_highlight_panel(
        "Your career guidance report",
        snapshot["summary"],
        variant="emerald",
        icon="✓",
    )
    render_activity_caption(
        at=snapshot["generated_at"],
        at_label="Generated",
        by=snapshot.get("activity_by"),
    )
    st.caption(f"Class {snapshot.get('student_class') or '—'}")

    report = snapshot.get("report") or {}
    if snapshot.get("phase") == "class_10_report" and report.get("class_10"):
        c10 = report["class_10"]
        with section("Class 10 transition report", "Concrete suggestions before choosing Class 11–12."):
            st.write(c10.get("summary", ""))
            if c10.get("top_career"):
                st.metric("Strongest future-fit pathway", c10["top_career"])
            if c10.get("stream_recommendations"):
                st.markdown("**Suggested streams**")
                for item in c10["stream_recommendations"]:
                    st.markdown(f"- **{item['stream']}** — {item['reason']}")
            if c10.get("next_steps"):
                st.markdown("**What to do next**")
                for step in c10["next_steps"]:
                    st.markdown(f"- {step}")

    rising = (report.get("meta") or {}).get("rising_sectors") or []
    if rising:
        with section("Jobs & fields rising (next 5 years)", "Labour outlook used in your match scores."):
            for sector in rising[:4]:
                pct = round(float(sector.get("growth_rate", 0)) * 100)
                st.markdown(f"**{sector['name']}** — projected demand signal ~{pct}%")
                st.progress(min(1.0, float(sector.get("growth_rate", 0))))

    with section("Your career matches", "Ranked by interest fit, academics, and future job demand."):
        if recommendations:
            for recommendation in recommendations:
                render_career_card(
                    career_name=recommendation["career_name"],
                    match_score=recommendation["match_score"],
                    rationale=recommendation["rationale"],
                    skills=parse_json_list(recommendation["skill_gap"]),
                    activities=parse_json_list(recommendation.get("certifications")),
                )
                if recommendation.get("roadmap"):
                    with st.expander(f"Roadmap — {recommendation['career_name']}"):
                        st.write(recommendation["roadmap"])
        else:
            st.info("No career matches in this report.")

    history = career_payload.get("history") or []
    if len(history) > 1:
        with section("Past reports", "Earlier guidance saved when you generated again."):
            for item in history:
                render_activity_caption(
                    at=item["generated_at"],
                    at_label="Generated",
                    by=item.get("activity_by"),
                )
                st.caption(f"Class {item.get('student_class') or '—'} · {item['phase']}")
                st.write(item["summary"])

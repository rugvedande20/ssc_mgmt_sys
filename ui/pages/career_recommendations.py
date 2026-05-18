import streamlit as st

from config.school_context import FUTURE_SCOPE_NOTE
from src.db.database import get_db_session
from src.services.student_service import get_student_dashboard_payload
from src.utils.helpers import parse_json_list


def render(current_user: dict) -> None:
    st.title("Career Ideas & Pathways")
    st.caption(f"Explore careers that may suit your interests (Class 6–10). {FUTURE_SCOPE_NOTE}")

    with get_db_session() as session:
        payload = get_student_dashboard_payload(session, current_user["id"])

    recommendations = payload["recommendations"]
    latest_assessment = payload["latest_assessment"]

    if not latest_assessment:
        st.info("Complete the interest assessment first so future career ideas can use your profile.")
    elif not payload["profile"]:
        st.info("Fill in your school profile so teachers and the system have the right context.")
    else:
        st.success("You are ready for personalized career ideas once the recommendation engine is connected.")

    st.divider()
    st.subheader("Preview (Demo Data)")
    st.caption(
        "Sample career ideas for demonstration. The real engine will suggest roles, skills, and activities matched to you."
    )

    if recommendations:
        for recommendation in recommendations:
            with st.expander(f"{recommendation['career_name']} — {recommendation['match_score']:.0f}% match"):
                st.write(recommendation["rationale"])
                skills = parse_json_list(recommendation["skill_gap"])
                activities = parse_json_list(recommendation["certifications"])
                if skills:
                    st.markdown("**Skills to build**")
                    for skill in skills:
                        st.markdown(f"- {skill}")
                if activities:
                    st.markdown("**Activities & courses to try**")
                    for item in activities:
                        st.markdown(f"- {item}")
    else:
        st.info("No career ideas are stored for your account yet.")

    st.divider()
    st.subheader("Coming Next")
    st.markdown(
        """
        - Career ideas matched to your interests and school marks
        - Simple learning roadmaps (subjects, clubs, projects)
        - Activities and courses to try at your age
        - Later: Class 11–12 stream guidance and market trends
        """
    )

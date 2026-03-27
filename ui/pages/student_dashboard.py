import streamlit as st

from src.db.database import get_db_session
from src.db.models import CareerRecommendation, PsychometricAttempt, StudentProfile
from src.utils.helpers import parse_json_list


def render(current_user: dict) -> None:
    st.title("Student Dashboard")
    st.caption("Your profile, assessment status, and career guidance snapshot.")

    with get_db_session() as session:
        profile = session.query(StudentProfile).filter(StudentProfile.user_id == current_user["id"]).first()
        latest_assessment = (
            session.query(PsychometricAttempt)
            .filter(PsychometricAttempt.student_id == current_user["id"])
            .order_by(PsychometricAttempt.submitted_at.desc())
            .first()
        )
        recommendations = (
            session.query(CareerRecommendation)
            .filter(CareerRecommendation.student_id == current_user["id"])
            .order_by(CareerRecommendation.match_score.desc())
            .limit(3)
            .all()
        )

    col1, col2, col3 = st.columns(3)
    col1.metric("Profile Status", "Complete" if profile else "Pending")
    col2.metric("Psychometric Test", "Completed" if latest_assessment else "Pending")
    col3.metric("Top Career Matches", len(recommendations))

    st.subheader("Profile Snapshot")
    if profile:
        st.write(
            {
                "Department": profile.department,
                "Semester": profile.semester,
                "Family Income Band": profile.family_income_band,
                "Internet Access": profile.internet_access,
            }
        )
    else:
        st.info("Profile details will appear here once the student profile module is implemented.")

    st.subheader("Latest Assessment")
    if latest_assessment:
        st.write(latest_assessment.summary)
        st.caption(f"Top codes: {latest_assessment.top_codes}")
    else:
        st.info("No psychometric assessment found yet.")

    st.subheader("Recommended Careers")
    if recommendations:
        for recommendation in recommendations:
            st.markdown(f"**{recommendation.career_name}** - {recommendation.match_score:.0f}% match")
            st.write(recommendation.rationale)
            skills = parse_json_list(recommendation.skill_gap)
            certifications = parse_json_list(recommendation.certifications)
            if skills:
                st.caption(f"Skill gaps: {', '.join(skills)}")
            if certifications:
                st.caption(f"Suggested certifications: {', '.join(certifications)}")
    else:
        st.info("Career recommendations will appear here after the recommendation engine is connected.")

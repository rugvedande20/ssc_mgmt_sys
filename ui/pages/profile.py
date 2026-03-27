import streamlit as st

from src.db.database import get_db_session
from src.services.student_service import get_student_profile, upsert_student_profile


def render(current_user: dict) -> None:
    st.title("Profile")
    st.caption("Keep this profile current so later modules can produce better counseling and career guidance.")

    with get_db_session() as session:
        profile = get_student_profile(session, current_user["id"])

    with st.form("student_profile_form"):
        col1, col2 = st.columns(2)
        age = col1.number_input("Age", min_value=16, max_value=40, value=profile.age if profile and profile.age else 18)
        gender = col2.selectbox(
            "Gender",
            ["", "Female", "Male", "Non-binary", "Prefer not to say"],
            index=["", "Female", "Male", "Non-binary", "Prefer not to say"].index(profile.gender)
            if profile and profile.gender in ["", "Female", "Male", "Non-binary", "Prefer not to say"]
            else 0,
        )
        department = col1.text_input("Department", value=profile.department if profile and profile.department else "")
        semester = col2.number_input(
            "Semester",
            min_value=1,
            max_value=12,
            value=profile.semester if profile and profile.semester else 1,
        )
        family_income_band = col1.selectbox(
            "Family Income Band",
            ["", "Low", "Middle", "Upper Middle", "High"],
            index=["", "Low", "Middle", "Upper Middle", "High"].index(profile.family_income_band)
            if profile and profile.family_income_band in ["", "Low", "Middle", "Upper Middle", "High"]
            else 0,
        )
        parental_education = col2.text_input(
            "Parental Education", value=profile.parental_education if profile and profile.parental_education else ""
        )
        travel_distance_km = col1.number_input(
            "Travel Distance (km)",
            min_value=0.0,
            max_value=200.0,
            value=float(profile.travel_distance_km) if profile and profile.travel_distance_km is not None else 0.0,
            step=0.5,
        )
        internet_access = col2.selectbox(
            "Internet Access",
            ["", "Yes", "No", "Limited"],
            index=["", "Yes", "No", "Limited"].index(profile.internet_access)
            if profile and profile.internet_access in ["", "Yes", "No", "Limited"]
            else 0,
        )
        interests_summary = st.text_area(
            "Interests Summary",
            value=profile.interests_summary if profile and profile.interests_summary else "",
            height=120,
        )
        strengths_summary = st.text_area(
            "Strengths Summary",
            value=profile.strengths_summary if profile and profile.strengths_summary else "",
            height=120,
        )
        submitted = st.form_submit_button("Save Profile", use_container_width=True)

    if submitted:
        with get_db_session() as session:
            upsert_student_profile(
                session,
                current_user["id"],
                {
                    "age": int(age),
                    "gender": gender,
                    "department": department,
                    "semester": int(semester),
                    "family_income_band": family_income_band,
                    "parental_education": parental_education,
                    "travel_distance_km": float(travel_distance_km),
                    "internet_access": internet_access,
                    "interests_summary": interests_summary,
                    "strengths_summary": strengths_summary,
                },
            )
        st.success("Profile updated successfully.")
        st.rerun()

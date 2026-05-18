import streamlit as st

from config.constants import TARGET_GRADE_MAX, TARGET_GRADE_MIN
from config.school_context import FUTURE_SCOPE_NOTE, GRADE_LABELS, PROFILE_FIELD_LABELS
from src.db.database import get_db_session
from src.services.student_service import get_student_profile_payload, upsert_student_profile


def render(current_user: dict) -> None:
    st.title("My School Profile")
    st.caption(
        f"Help teachers and the guidance system understand your class, school, and interests (Class 6–10). {FUTURE_SCOPE_NOTE}"
    )

    with get_db_session() as session:
        profile = get_student_profile_payload(session, current_user["id"])

    grade_options = list(range(TARGET_GRADE_MIN, TARGET_GRADE_MAX + 1))
    grade_labels = [GRADE_LABELS[g] for g in grade_options]

    with st.form("student_profile_form"):
        col1, col2 = st.columns(2)
        age = col1.number_input(
            "Age",
            min_value=10,
            max_value=17,
            value=profile["age"] if profile and profile["age"] else 13,
        )
        gender = col2.selectbox(
            "Gender",
            ["", "Female", "Male", "Non-binary", "Prefer not to say"],
            index=["", "Female", "Male", "Non-binary", "Prefer not to say"].index(profile["gender"])
            if profile and profile["gender"] in ["", "Female", "Male", "Non-binary", "Prefer not to say"]
            else 0,
        )
        school_name = col1.text_input(
            PROFILE_FIELD_LABELS["department"],
            value=profile["department"] if profile else "",
            placeholder="e.g. Ryan International School (CBSE)",
        )
        current_class = profile["semester"] if profile and profile["semester"] in grade_options else TARGET_GRADE_MIN
        class_label = col2.selectbox(
            PROFILE_FIELD_LABELS["semester"],
            grade_labels,
            index=grade_options.index(int(current_class)),
        )
        family_income_band = col1.selectbox(
            PROFILE_FIELD_LABELS["family_income_band"],
            ["", "Low", "Middle", "Upper Middle", "High"],
            index=["", "Low", "Middle", "Upper Middle", "High"].index(profile["family_income_band"])
            if profile and profile["family_income_band"] in ["", "Low", "Middle", "Upper Middle", "High"]
            else 0,
        )
        parental_education = col2.selectbox(
            PROFILE_FIELD_LABELS["parental_education"],
            ["", "Up to Class 10", "Graduate", "Postgraduate", "Other"],
            index=["", "Up to Class 10", "Graduate", "Postgraduate", "Other"].index(profile["parental_education"])
            if profile
            and profile["parental_education"] in ["", "Up to Class 10", "Graduate", "Postgraduate", "Other"]
            else 0,
        )
        travel_distance_km = col1.number_input(
            PROFILE_FIELD_LABELS["travel_distance_km"],
            min_value=0.0,
            max_value=80.0,
            value=float(profile["travel_distance_km"]) if profile and profile["travel_distance_km"] is not None else 0.0,
            step=0.5,
        )
        internet_access = col2.selectbox(
            PROFILE_FIELD_LABELS["internet_access"],
            ["", "Yes", "No", "Limited"],
            index=["", "Yes", "No", "Limited"].index(profile["internet_access"])
            if profile and profile["internet_access"] in ["", "Yes", "No", "Limited"]
            else 0,
        )
        interests_summary = st.text_area(
            PROFILE_FIELD_LABELS["interests_summary"],
            value=profile["interests_summary"] if profile else "",
            height=120,
            placeholder="Sports, subjects you enjoy, clubs, creative hobbies…",
        )
        strengths_summary = st.text_area(
            PROFILE_FIELD_LABELS["strengths_summary"],
            value=profile["strengths_summary"] if profile else "",
            height=120,
            placeholder="Subjects you do well in, awards, leadership roles…",
        )
        submitted = st.form_submit_button("Save Profile", use_container_width=True)

    if submitted:
        selected_grade = grade_options[grade_labels.index(class_label)]
        with get_db_session() as session:
            upsert_student_profile(
                session,
                current_user["id"],
                {
                    "age": int(age),
                    "gender": gender,
                    "department": school_name,
                    "semester": int(selected_grade),
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

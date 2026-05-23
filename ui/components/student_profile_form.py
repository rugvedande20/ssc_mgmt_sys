from __future__ import annotations

from typing import Any

import streamlit as st

from config.constants import TARGET_GRADE_MAX, TARGET_GRADE_MIN
from config.school_context import FAMILY_INCOME_BRACKETS, GRADE_LABELS, PROFILE_FIELD_LABELS
from ui.components.page_chrome import render_form_section_header
from src.db.database import get_db_session
from src.services.student_service import upsert_student_profile
from src.utils.helpers import validate_student_profile_data


def _index_in_options(value: str, options: list[str]) -> int:
    return options.index(value) if value in options else 0


def render_student_profile_form(
    current_user_id: int,
    profile: dict[str, Any] | None,
    *,
    form_key: str,
    submit_label: str = "Save profile",
) -> None:
    grade_options = list(range(TARGET_GRADE_MIN, TARGET_GRADE_MAX + 1))
    grade_labels = [GRADE_LABELS[g] for g in grade_options]
    gender_options = ["", "Female", "Male", "Non-binary", "Prefer not to say"]
    income_options = list(FAMILY_INCOME_BRACKETS)
    education_options = ["", "Up to Class 10", "Graduate", "Postgraduate", "Other"]
    internet_options = ["", "Yes", "No", "Limited"]

    current_class = (
        profile["semester"]
        if profile and profile.get("semester") in grade_options
        else TARGET_GRADE_MIN
    )

    with st.form(form_key):
        render_form_section_header("👤", "About you", "Basic details used across the platform")
        col1, col2 = st.columns(2)
        age = col1.number_input(
            PROFILE_FIELD_LABELS["age"],
            min_value=10,
            max_value=17,
            value=int(profile["age"]) if profile and profile.get("age") is not None else 13,
        )
        gender = col2.selectbox(
            PROFILE_FIELD_LABELS["gender"],
            gender_options,
            index=_index_in_options(profile["gender"] if profile else "", gender_options),
        )

        render_form_section_header("🏫", "School & home", "Class, school, and learning environment")
        col3, col4 = st.columns(2)
        school_name = col3.text_input(
            PROFILE_FIELD_LABELS["department"],
            value=profile["department"] if profile else "",
            placeholder="e.g. Ryan International School (CBSE)",
        )
        class_label = col4.selectbox(
            PROFILE_FIELD_LABELS["semester"],
            grade_labels,
            index=grade_options.index(int(current_class)),
        )
        family_income_band = col3.selectbox(
            PROFILE_FIELD_LABELS["family_income_band"],
            income_options,
            index=_index_in_options(profile["family_income_band"] if profile else "", income_options),
        )
        parental_education = col4.selectbox(
            PROFILE_FIELD_LABELS["parental_education"],
            education_options,
            index=_index_in_options(profile["parental_education"] if profile else "", education_options),
        )
        travel_distance_km = col3.number_input(
            PROFILE_FIELD_LABELS["travel_distance_km"],
            min_value=0.0,
            max_value=80.0,
            value=float(profile["travel_distance_km"])
            if profile and profile.get("travel_distance_km") is not None
            else 0.0,
            step=0.5,
        )
        internet_access = col4.selectbox(
            PROFILE_FIELD_LABELS["internet_access"],
            internet_options,
            index=_index_in_options(profile["internet_access"] if profile else "", internet_options),
        )

        render_form_section_header("✨", "Interests & strengths", "Helps with assessments and career ideas")
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

        submitted = st.form_submit_button(submit_label, use_container_width=True, type="primary")

    if submitted:
        selected_grade = grade_options[grade_labels.index(class_label)]
        payload = {
            "age": int(age),
            "gender": gender,
            "department": school_name.strip(),
            "semester": int(selected_grade),
            "family_income_band": family_income_band,
            "parental_education": parental_education,
            "travel_distance_km": float(travel_distance_km),
            "internet_access": internet_access,
            "interests_summary": interests_summary.strip(),
            "strengths_summary": strengths_summary.strip(),
        }
        errors = validate_student_profile_data(payload)
        if errors:
            st.error("Please complete the following: " + ", ".join(errors))
            return

        with get_db_session() as session:
            upsert_student_profile(session, current_user_id, payload, updated_by_user_id=current_user_id)
        st.success("Profile saved successfully.")
        st.rerun()


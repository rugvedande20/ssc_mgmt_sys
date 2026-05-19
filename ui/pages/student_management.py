import streamlit as st

from config.constants import TARGET_GRADE_MAX, TARGET_GRADE_MIN
from config.school_context import FUTURE_SCOPE_NOTE, GRADE_LABELS, PROFILE_FIELD_LABELS
from src.db.database import get_db_session
from src.services.student_service import create_student_user, get_student_overview, list_students
from src.utils.helpers import profile_completeness_percent
from ui.components.layout import section
from ui.components.risk_display import risk_level_badge
from ui.components.student_overview import (
    render_academic_tab,
    render_profile_tab,
    render_psychometric_tab,
    render_risk_tab,
)
from ui.components.tables import show_dataframe


def _render_student_overview(overview: dict) -> None:
    st.markdown(f"### {overview['full_name']}")
    st.caption(f"@{overview['username']} · {overview['email']}")

    col1, col2, col3 = st.columns(3)
    profile = overview["profile"]
    completeness = profile_completeness_percent(profile)
    col1.metric("Profile", f"{completeness}%")
    col2.metric("Career records", overview["recommendation_count"])
    with col3:
        st.markdown("**Latest risk**")
        prediction = overview.get("latest_prediction")
        if prediction:
            st.markdown(
                risk_level_badge(str(prediction.get("risk_level", "—"))),
                unsafe_allow_html=True,
            )
        else:
            st.write("—")

    tab_profile, tab_academic, tab_risk, tab_psych = st.tabs(
        ["Profile", "Academics", "Dropout risk", "Psychometric"]
    )

    with tab_profile:
        render_profile_tab(profile)
    with tab_academic:
        render_academic_tab(overview.get("latest_academic"))
    with tab_risk:
        render_risk_tab(overview.get("latest_prediction"))
    with tab_psych:
        render_psychometric_tab(overview.get("latest_psychometric"))


def render(current_user: dict) -> None:
    st.header("Student Management")
    st.caption(f"Create and review student accounts for Class {TARGET_GRADE_MIN}–{TARGET_GRADE_MAX}. {FUTURE_SCOPE_NOTE}")

    grade_options = list(range(TARGET_GRADE_MIN, TARGET_GRADE_MAX + 1))
    grade_labels = [GRADE_LABELS[g] for g in grade_options]

    with section("Create student", "New Class 6–10 login and profile."):
        with st.form("create_student_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            full_name = col1.text_input("Full name")
            username = col2.text_input("Username")
            email = col1.text_input("Email")
            password = col2.text_input("Temporary password", type="password")
            school_name = col1.text_input(
                PROFILE_FIELD_LABELS["department"],
                placeholder="e.g. City Public School (CBSE)",
            )
            class_label = col2.selectbox(PROFILE_FIELD_LABELS["semester"], grade_labels, index=2)
            submitted = st.form_submit_button("Create student", use_container_width=True)

        if submitted:
            if not all([full_name.strip(), username.strip(), email.strip(), password]):
                st.error("Full name, username, email, and password are required.")
            else:
                try:
                    selected_grade = grade_options[grade_labels.index(class_label)]
                    with get_db_session() as session:
                        create_student_user(
                            session,
                            username=username,
                            full_name=full_name,
                            email=email,
                            password=password,
                            profile_data={"department": school_name, "semester": int(selected_grade)},
                            created_by_admin_id=current_user["id"],
                        )
                    st.success("Student account created successfully.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    with section("Student directory", "Search and pick a student for the overview below."):
        search_term = st.text_input("Search by name, username, or email")
        with get_db_session() as session:
            students = list_students(
                session, search_term=search_term, limit=100, admin_user_id=current_user["id"]
            )

        if students:
            show_dataframe(students, columns=["full_name", "username", "email", "school", "class"])
        else:
            st.info("No students found for the current search.")
            return

    with section("Student overview", "Profile, academics, risk, and psychometric data for one student."):
        student_labels = {f"{student['full_name']} ({student['username']})": student["id"] for student in students}
        selected_label = st.selectbox("Select a student", list(student_labels.keys()))
        with get_db_session() as session:
            overview = get_student_overview(session, student_labels[selected_label])

        if overview:
            _render_student_overview(overview)

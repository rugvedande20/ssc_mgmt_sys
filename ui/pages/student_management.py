import streamlit as st

from config.constants import TARGET_GRADE_MAX, TARGET_GRADE_MIN
from config.school_context import FUTURE_SCOPE_NOTE, GRADE_LABELS, PROFILE_FIELD_LABELS, format_class
from src.db.database import get_db_session
from src.services.student_service import create_student_user, get_student_overview, list_students
from src.utils.helpers import profile_completeness_percent


def _render_student_overview(overview: dict) -> None:
    st.markdown(f"### {overview['full_name']}")
    st.caption(f"@{overview['username']} · {overview['email']}")

    col1, col2, col3 = st.columns(3)
    profile = overview["profile"]
    completeness = profile_completeness_percent(profile)
    col1.metric("Profile", f"{completeness}%")
    col2.metric("Career Records", overview["recommendation_count"])
    col3.metric(
        "Latest Risk",
        overview["latest_prediction"]["risk_level"] if overview["latest_prediction"] else "—",
    )

    tab_profile, tab_academic, tab_risk, tab_psych = st.tabs(
        ["Profile", "Academics", "Dropout Risk", "Psychometric"]
    )

    with tab_profile:
        if profile:
            st.json(
                {
                    PROFILE_FIELD_LABELS["department"]: profile["department"],
                    PROFILE_FIELD_LABELS["semester"]: format_class(profile["semester"]),
                    PROFILE_FIELD_LABELS["family_income_band"]: profile["family_income_band"],
                    PROFILE_FIELD_LABELS["internet_access"]: profile["internet_access"],
                    PROFILE_FIELD_LABELS["interests_summary"]: profile["interests_summary"],
                    PROFILE_FIELD_LABELS["strengths_summary"]: profile["strengths_summary"],
                }
            )
        else:
            st.info("No profile saved yet.")

    with tab_academic:
        academic = overview["latest_academic"]
        if academic:
            st.json(academic)
        else:
            st.info("No academic records yet. Add data under Academic Data Upload.")

    with tab_risk:
        prediction = overview["latest_prediction"]
        if prediction:
            st.metric("Risk score", f"{prediction['risk_score']}%")
            st.write(f"**Level:** {prediction['risk_level']}")
            st.caption(f"Predicted at {prediction['predicted_at']}")
            st.write(prediction["top_factors"])
        else:
            st.info("No dropout prediction yet. Train the model and run predictions on Dropout Analysis.")

    with tab_psych:
        psych = overview["latest_psychometric"]
        if psych:
            st.write(psych["summary"])
            st.caption(f"Top codes: {psych['top_codes']} · Submitted {psych['submitted_at']}")
        else:
            st.info("Student has not completed the interest assessment.")


def render(current_user: dict) -> None:
    st.title("Student Management")
    st.caption(f"Create and review student accounts for Class {TARGET_GRADE_MIN}–{TARGET_GRADE_MAX}. {FUTURE_SCOPE_NOTE}")

    grade_options = list(range(TARGET_GRADE_MIN, TARGET_GRADE_MAX + 1))
    grade_labels = [GRADE_LABELS[g] for g in grade_options]

    with st.form("create_student_form", clear_on_submit=True):
        st.subheader("Create Student Account")
        col1, col2 = st.columns(2)
        full_name = col1.text_input("Full Name")
        username = col2.text_input("Username")
        email = col1.text_input("Email")
        password = col2.text_input("Temporary Password", type="password")
        school_name = col1.text_input(
            PROFILE_FIELD_LABELS["department"],
            placeholder="e.g. City Public School (CBSE)",
        )
        class_label = col2.selectbox(PROFILE_FIELD_LABELS["semester"], grade_labels, index=2)
        submitted = st.form_submit_button("Create Student", use_container_width=True)

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

    st.divider()
    st.subheader("Student Directory")
    search_term = st.text_input("Search by name, username, or email")
    with get_db_session() as session:
        students = list_students(
            session, search_term=search_term, limit=100, admin_user_id=current_user["id"]
        )

    if students:
        st.dataframe(students, use_container_width=True, hide_index=True)
    else:
        st.info("No students found for the current search.")

    st.divider()
    st.subheader("Student Overview")
    if not students:
        st.caption("Create a student to view their combined profile, academic, risk, and assessment data.")
        return

    student_labels = {f"{student['full_name']} ({student['username']})": student["id"] for student in students}
    selected_label = st.selectbox("Select a student", list(student_labels.keys()))
    with get_db_session() as session:
        overview = get_student_overview(session, student_labels[selected_label])

    if overview:
        _render_student_overview(overview)

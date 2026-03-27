import streamlit as st
import pandas as pd

from src.db.database import get_db_session
from src.services.student_service import (
    academic_record_summary,
    add_academic_record,
    bulk_insert_academic_records,
    list_recent_academic_records,
    list_student_options,
)


def render() -> None:
    st.title("Academic Data Upload")
    st.caption("Admins can add one academic record manually or upload a CSV in the project schema.")

    with get_db_session() as session:
        student_options = list_student_options(session)
        summary = academic_record_summary(session)
        recent_records = list_recent_academic_records(session, limit=25)

    col1, col2 = st.columns(2)
    col1.metric("Students With Records", summary["students_with_records"])
    col2.metric("Total Academic Records", summary["total_records"])

    if not student_options:
        st.warning("Create at least one student account before adding academic data.")
        return

    option_map = {f"{student_name} (ID {student_id})": student_id for student_id, student_name in student_options}

    with st.form("manual_academic_record_form", clear_on_submit=True):
        st.subheader("Add Academic Record Manually")
        student_label = st.selectbox("Student", list(option_map.keys()))
        m1, m2, m3 = st.columns(3)
        attendance_percentage = m1.number_input("Attendance %", min_value=0.0, max_value=100.0, value=75.0)
        cgpa = m2.number_input("CGPA", min_value=0.0, max_value=10.0, value=7.0, step=0.1)
        internal_marks = m3.number_input("Internal Marks", min_value=0.0, max_value=100.0, value=70.0)
        m4, m5, m6 = st.columns(3)
        backlog_count = m4.number_input("Backlog Count", min_value=0, max_value=20, value=0)
        disciplinary_issues = m5.number_input("Disciplinary Issues", min_value=0, max_value=10, value=0)
        engagement_score = m6.number_input("Engagement Score", min_value=0.0, max_value=10.0, value=6.5, step=0.1)
        m7, m8, m9 = st.columns(3)
        stress_level = m7.number_input("Stress Level", min_value=0.0, max_value=10.0, value=4.5, step=0.1)
        fee_pending = m8.selectbox("Fee Pending", ["No", "Yes"])
        scholarship_status = m9.selectbox("Scholarship Status", ["No", "Yes"])
        extracurricular_participation = st.selectbox("Extracurricular Participation", ["No", "Yes"])
        manual_submit = st.form_submit_button("Save Academic Record", use_container_width=True)

    if manual_submit:
        with get_db_session() as session:
            add_academic_record(
                session,
                student_id=option_map[student_label],
                record_data={
                    "attendance_percentage": float(attendance_percentage),
                    "cgpa": float(cgpa),
                    "internal_marks": float(internal_marks),
                    "backlog_count": int(backlog_count),
                    "fee_pending": fee_pending,
                    "scholarship_status": scholarship_status,
                    "extracurricular_participation": extracurricular_participation,
                    "disciplinary_issues": int(disciplinary_issues),
                    "engagement_score": float(engagement_score),
                    "stress_level": float(stress_level),
                },
            )
        st.success("Academic record saved.")
        st.rerun()

    st.divider()
    st.subheader("Bulk CSV Upload")
    st.caption(
        "Required columns: student_username, attendance_percentage, cgpa, internal_marks, backlog_count, "
        "fee_pending, scholarship_status, extracurricular_participation, disciplinary_issues, engagement_score, stress_level"
    )
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        csv_frame = pd.read_csv(uploaded_file)
        st.dataframe(csv_frame.head(10), use_container_width=True, hide_index=True)
        if st.button("Import CSV Records", use_container_width=True):
            try:
                with get_db_session() as session:
                    inserted_count = bulk_insert_academic_records(session, csv_frame)
                st.success(f"Imported {inserted_count} academic records.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.divider()
    st.subheader("Recent Academic Records")
    if recent_records:
        st.dataframe(recent_records, use_container_width=True, hide_index=True)
    else:
        st.info("No academic records have been added yet.")

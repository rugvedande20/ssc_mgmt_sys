import streamlit as st
import pandas as pd

from config.constants import TARGET_GRADE_MAX, TARGET_GRADE_MIN
from config.school_context import (
    ACADEMIC_FIELD_LABELS,
    FUTURE_SCOPE_NOTE,
    SCHOOL_ACADEMIC_CSV_COLUMN_HELP,
    SCHOOL_ACADEMIC_CSV_COLUMNS,
    build_academic_csv_template_rows,
)
from src.db.database import get_db_session
from src.utils.file_upload import read_tabular_upload
from src.services.student_service import (
    academic_record_summary,
    add_academic_record,
    bulk_import_students_from_csv,
    list_recent_academic_records,
    list_student_options,
)


def render(current_user: dict) -> None:
    st.title("School Academic Data")
    st.caption(
        f"Add term-wise marks and attendance for Class {TARGET_GRADE_MIN}–{TARGET_GRADE_MAX} students. {FUTURE_SCOPE_NOTE}"
    )

    admin_id = current_user["id"] if current_user.get("role") == "admin" else None

    with get_db_session() as session:
        student_options = list_student_options(session, admin_user_id=admin_id)
        summary = academic_record_summary(session)
        recent_records = list_recent_academic_records(session, limit=25)

    col1, col2 = st.columns(2)
    col1.metric("Students With Records", summary["students_with_records"])
    col2.metric("Total Academic Records", summary["total_records"])

    if student_options:
        option_map = {f"{student_name} (ID {student_id})": student_id for student_id, student_name in student_options}

        with st.form("manual_academic_record_form", clear_on_submit=True):
            st.subheader("Add Academic Record Manually")
            student_label = st.selectbox("Student", list(option_map.keys()))
            m1, m2, m3 = st.columns(3)
            attendance_percentage = m1.number_input(
                ACADEMIC_FIELD_LABELS["attendance_percentage"], min_value=0.0, max_value=100.0, value=82.0
            )
            overall_marks = m2.number_input(
                ACADEMIC_FIELD_LABELS["cgpa"], min_value=0.0, max_value=100.0, value=68.0, step=0.5
            )
            term_score = m3.number_input(
                ACADEMIC_FIELD_LABELS["internal_marks"], min_value=0.0, max_value=100.0, value=65.0, step=0.5
            )
            m4, m5, m6 = st.columns(3)
            subjects_below_passing = m4.number_input(
                ACADEMIC_FIELD_LABELS["backlog_count"], min_value=0, max_value=10, value=0
            )
            disciplinary_issues = m5.number_input(
                ACADEMIC_FIELD_LABELS["disciplinary_issues"], min_value=0, max_value=10, value=0
            )
            engagement_score = m6.number_input(
                ACADEMIC_FIELD_LABELS["engagement_score"], min_value=0.0, max_value=10.0, value=6.5, step=0.1
            )
            m7, m8, m9 = st.columns(3)
            stress_level = m7.number_input(
                ACADEMIC_FIELD_LABELS["stress_level"], min_value=0.0, max_value=10.0, value=4.5, step=0.1
            )
            fee_pending = m8.selectbox(ACADEMIC_FIELD_LABELS["fee_pending"], ["No", "Yes"])
            scholarship_status = m9.selectbox(ACADEMIC_FIELD_LABELS["scholarship_status"], ["No", "Yes"])
            extracurricular_participation = st.selectbox(
                ACADEMIC_FIELD_LABELS["extracurricular_participation"], ["No", "Yes"]
            )
            manual_submit = st.form_submit_button("Save Academic Record", use_container_width=True)

        if manual_submit:
            with get_db_session() as session:
                add_academic_record(
                    session,
                    student_id=option_map[student_label],
                    record_data={
                        "attendance_percentage": float(attendance_percentage),
                        "cgpa": float(overall_marks),
                        "internal_marks": float(term_score),
                        "backlog_count": int(subjects_below_passing),
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
    else:
        st.info("No students linked to your account yet. Use bulk CSV import below to create students automatically.")

    st.divider()
    st.subheader("Bulk CSV Upload")
    st.caption(
        "Import creates student logins for your school (linked to you as admin), then saves academic data. "
        "Required columns: " + ", ".join(SCHOOL_ACADEMIC_CSV_COLUMNS)
    )
    st.markdown(
        "**Login format:** first 3 letters of first name + first 3 letters of last name "
        "(e.g. Aarav Patil → username `aarpat`, password `aarpat@123`). "
        "Use `student_username` as `firstname_lastname` (e.g. `aarav_patil`)."
    )

    with st.expander("Column guide (Class 6–10)"):
        for column_name in SCHOOL_ACADEMIC_CSV_COLUMNS:
            st.markdown(f"- **{column_name}** — {SCHOOL_ACADEMIC_CSV_COLUMN_HELP[column_name]}")
        st.markdown(
            "- **Optional:** `first_name`, `last_name`, `school_name`, `class_grade` (6–10)"
        )

    template_df = pd.DataFrame(build_academic_csv_template_rows())
    st.download_button(
        "Download CSV template",
        data=template_df.to_csv(index=False),
        file_name="school_academic_records_template.csv",
        mime="text/csv",
        use_container_width=True,
    )

    uploaded_file = st.file_uploader(
        "Upload CSV or Excel",
        type=["csv", "xlsx", "xls"],
        help="Maximum file size: 5 MB. All data rows in the file are imported.",
    )
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_size_mb = len(file_bytes) / (1024 * 1024)
        csv_frame = None

        if file_size_mb > 5:
            st.error(f"File is {file_size_mb:.1f} MB. Maximum allowed size is 5 MB.")
        else:
            try:
                csv_frame = read_tabular_upload(uploaded_file, file_bytes=file_bytes)
            except Exception as exc:
                st.error(f"Could not read file: {exc}")

        if csv_frame is not None:
            st.caption(f"**{len(csv_frame)}** row(s) found in file (preview shows first 10).")
            st.dataframe(csv_frame.head(10), use_container_width=True, hide_index=True)

        if csv_frame is not None and st.button(
            "Import all records", use_container_width=True, type="primary"
        ):
            if not admin_id:
                st.error("You must be logged in as an admin to import students.")
            else:
                try:
                    with get_db_session() as session:
                        result = bulk_import_students_from_csv(session, csv_frame, admin_user_id=admin_id)
                    failed = len(result["row_errors"])
                    st.success(
                        f"Processed **{result['total_rows']}** row(s) from file: "
                        f"**{result['records_imported']}** academic record(s) saved, "
                        f"**{result['students_created']}** new student account(s) created."
                    )
                    if failed:
                        st.warning(f"**{failed}** row(s) failed to import:")
                        for message in result["row_errors"][:25]:
                            st.caption(message)
                        if failed > 25:
                            st.caption(f"... and {failed - 25} more errors.")
                    if result["existing_accounts_used"]:
                        st.info(
                            f"Matched {len(result['existing_accounts_used'])} row(s) to existing student login(s)."
                        )

                    if result["created_accounts"]:
                        st.subheader("New student logins")
                        cred_df = pd.DataFrame(result["created_accounts"])
                        st.dataframe(cred_df, use_container_width=True, hide_index=True)
                        st.download_button(
                            "Download login credentials (CSV)",
                            data=cred_df.to_csv(index=False),
                            file_name="new_student_logins.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    st.divider()
    st.subheader("Recent Academic Records")
    if recent_records:
        st.dataframe(recent_records, use_container_width=True, hide_index=True)
    else:
        st.info("No academic records have been added yet.")

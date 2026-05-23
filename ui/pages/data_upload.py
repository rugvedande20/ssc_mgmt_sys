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
from src.utils.admin_context import (
    admin_page_subtitle,
    assigned_grade_for_user,
    grade_scope_label,
    student_scope_for_user,
)
from ui.components.layout import section
from ui.components.page_chrome import render_page_header
from src.utils.activity import format_activity_meta
from ui.components.tables import show_dataframe

BULK_UPLOAD_WIDGET_KEY = "bulk_academic_file_uploader"
BULK_UPLOAD_RESET_VERSION_KEY = "bulk_upload_widget_version"


def _reset_bulk_upload_widget() -> None:
    """Force file uploader back to empty state (drops preview and import button)."""
    st.session_state[BULK_UPLOAD_RESET_VERSION_KEY] = (
        int(st.session_state.get(BULK_UPLOAD_RESET_VERSION_KEY, 0)) + 1
    )


def _render_import_results(result: dict) -> None:
    failed = len(result["row_errors"])
    activity_meta = format_activity_meta(
        at=result.get("imported_at"),
        at_label="Imported at",
        by=result.get("activity_by"),
    )
    summary = (
        f"Processed **{result['total_rows']}** row(s): "
        f"**{result['records_imported']}** academic record(s) saved for matched students, "
        f"**{result['students_created']}** new account(s) created where needed."
    )
    if activity_meta:
        summary = f"{summary} · {activity_meta}"
    st.success(summary)
    if result["existing_accounts_used"]:
        st.info(
            f"**{len(result['existing_accounts_used'])}** row(s) matched students who already had accounts "
            f"(academic data still added)."
        )
    skipped_names = result.get("skipped_duplicate_names") or []
    if skipped_names:
        st.warning(
            f"**{len(skipped_names)}** row(s) skipped because the same full name already appeared in the file "
            "or already exists in the system (only the first row per name is imported)."
        )
        for message in skipped_names[:25]:
            st.caption(message)
        if len(skipped_names) > 25:
            st.caption(f"... and {len(skipped_names) - 25} more skipped rows.")
    if failed:
        st.warning(f"**{failed}** row(s) failed:")
        for message in result["row_errors"][:25]:
            st.caption(message)
        if failed > 25:
            st.caption(f"... and {failed - 25} more errors.")

    if result["created_accounts"]:
        st.subheader("New student logins (share with students)")
        cred_df = pd.DataFrame(result["created_accounts"])
        show_dataframe(result["created_accounts"])
        st.download_button(
            "Download login credentials (CSV)",
            data=cred_df.to_csv(index=False),
            file_name="new_student_logins.csv",
            mime="text/csv",
            use_container_width=True,
        )


def render(current_user: dict) -> None:
    grade_label = grade_scope_label(current_user)
    title = (
        f"Class {assigned_grade_for_user(current_user)} Academic Data Upload"
        if grade_label
        else "Academic Data Upload"
    )
    render_page_header(
        title,
        admin_page_subtitle(
            f"Bulk upload for all students — term-wise marks and attendance (Class {TARGET_GRADE_MIN}–{TARGET_GRADE_MAX}). {FUTURE_SCOPE_NOTE}",
            current_user,
        ),
        badge_text="Admin",
        badge_variant="indigo",
    )

    admin_id = current_user["id"]
    grade_scope = assigned_grade_for_user(current_user)
    scope = student_scope_for_user(current_user)

    if "last_bulk_import" in st.session_state:
        st.subheader("Last bulk import")
        _render_import_results(st.session_state["last_bulk_import"])
        if st.button("Dismiss import summary"):
            del st.session_state["last_bulk_import"]
            st.rerun()
        st.divider()

    with get_db_session() as session:
        student_options = list_student_options(session, **scope)
        summary = academic_record_summary(session, **scope)
        recent_records = list_recent_academic_records(session, limit=25, **scope)

    m1, m2 = st.columns(2)
    m1.metric("Students with records", summary["students_with_records"])
    m2.metric("Total academic records", summary["total_records"])

    if student_options:
        option_map = {f"{student_name} (ID {student_id})": student_id for student_id, student_name in student_options}

        with section("Manual entry", "Add or update one student at a time."):
            with st.form("manual_academic_record_form", clear_on_submit=True):
                student_label = st.selectbox("Student", list(option_map.keys()))
                mc1, mc2, mc3 = st.columns(3)
                attendance_percentage = mc1.number_input(
                    ACADEMIC_FIELD_LABELS["attendance_percentage"], min_value=0.0, max_value=100.0, value=82.0
                )
                overall_marks = mc2.number_input(
                    ACADEMIC_FIELD_LABELS["cgpa"], min_value=0.0, max_value=100.0, value=68.0, step=0.5
                )
                term_score = mc3.number_input(
                    ACADEMIC_FIELD_LABELS["internal_marks"], min_value=0.0, max_value=100.0, value=65.0, step=0.5
                )
                mc4, mc5, mc6 = st.columns(3)
                subjects_below_passing = mc4.number_input(
                    ACADEMIC_FIELD_LABELS["backlog_count"], min_value=0, max_value=10, value=0
                )
                disciplinary_issues = mc5.number_input(
                    ACADEMIC_FIELD_LABELS["disciplinary_issues"], min_value=0, max_value=10, value=0
                )
                engagement_score = mc6.number_input(
                    ACADEMIC_FIELD_LABELS["engagement_score"], min_value=0.0, max_value=10.0, value=6.5, step=0.1
                )
                mc7, mc8, mc9 = st.columns(3)
                stress_level = mc7.number_input(
                    ACADEMIC_FIELD_LABELS["stress_level"], min_value=0.0, max_value=10.0, value=4.5, step=0.1
                )
                fee_pending = mc8.selectbox(ACADEMIC_FIELD_LABELS["fee_pending"], ["No", "Yes"])
                scholarship_status = mc9.selectbox(ACADEMIC_FIELD_LABELS["scholarship_status"], ["No", "Yes"])
                extracurricular_participation = st.selectbox(
                    ACADEMIC_FIELD_LABELS["extracurricular_participation"], ["No", "Yes"]
                )
                manual_submit = st.form_submit_button("Save academic record", use_container_width=True)

            if manual_submit:
                with get_db_session() as session:
                    add_academic_record(
                        session,
                        student_id=option_map[student_label],
                        recorded_by_user_id=admin_id,
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
        st.info("No students linked to your account yet — bulk import below will create them.")

    with section(
        "Upload academic details for all students",
        "One Excel/CSV file — each row updates that student's academic data (and creates an account only if missing).",
    ):
        st.markdown(
            """
            **One file for the whole school cohort.** Each row must include `student_username` so the system
            knows which student to update. Existing students get a **new academic snapshot** from that row;
            new usernames get a student account plus their first academic record.

            - `student_username`: `firstname_lastname` (e.g. `aarav_patil`) — must be unique per student
            - **New accounts:** login username is generated from the student slug (see Student Management)
            - Students are linked to **you** as the admin who imported the file

            **Duplicate names:** If two or more rows have the **same exact full name** (e.g. two different
            `Priya Sharma` entries), only the **first row in the file** is imported. Later rows with that name
            are skipped — create those accounts manually under **Student Management → Create student**.
            """
        )
        st.info(
            "Students who share the same exact name cannot be bulk-created in one file. "
            "Use unique `student_username` slugs when names differ; otherwise add duplicates manually."
        )
        st.caption("Required columns: " + ", ".join(SCHOOL_ACADEMIC_CSV_COLUMNS))

        with st.expander("Column guide (Class 6–10)"):
            for column_name in SCHOOL_ACADEMIC_CSV_COLUMNS:
                st.markdown(f"- **{column_name}** — {SCHOOL_ACADEMIC_CSV_COLUMN_HELP[column_name]}")
            st.markdown("- **Optional:** `first_name`, `last_name`, `school_name`, `class_grade` (6–10)")

        template_df = pd.DataFrame(build_academic_csv_template_rows())
        st.download_button(
            "Download CSV template",
            data=template_df.to_csv(index=False),
            file_name="school_academic_records_template.csv",
            mime="text/csv",
            use_container_width=True,
        )

        upload_widget_key = (
            f"{BULK_UPLOAD_WIDGET_KEY}_{st.session_state.get(BULK_UPLOAD_RESET_VERSION_KEY, 0)}"
        )
        uploaded_file = st.file_uploader(
            "Upload CSV or Excel",
            type=["csv", "xlsx", "xls"],
            key=upload_widget_key,
            help="Maximum file size: 5 MB. All rows are imported and student accounts are created automatically.",
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
                st.caption(f"**{len(csv_frame)}** row(s) ready to import (preview shows first 10).")
                show_dataframe(csv_frame.head(10))

            if csv_frame is not None and st.button(
                "Import file — update all students",
                use_container_width=True,
                type="primary",
            ):
                if not admin_id:
                    st.error("You must be logged in as an admin to import students.")
                else:
                    try:
                        with get_db_session() as session:
                            result = bulk_import_students_from_csv(session, csv_frame, admin_user_id=admin_id)
                        st.session_state["last_bulk_import"] = result
                        _reset_bulk_upload_widget()
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

    with section("Recent records", "Latest uploads and manual entries."):
        if recent_records:
            show_dataframe(recent_records)
        else:
            st.info("No academic records have been added yet.")

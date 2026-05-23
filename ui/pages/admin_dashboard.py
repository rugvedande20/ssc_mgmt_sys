import streamlit as st
from sqlalchemy import select

from src.db.database import get_db_session
from src.db.models import User
from src.services.dropout_service import list_latest_predictions_per_student
from src.services.user_service import get_dashboard_counts
from src.utils.admin_context import (
    admin_page_subtitle,
    assigned_grade_for_user,
    grade_scope_label,
    student_owner_id,
)
from ui.components.layout import section
from ui.components.page_chrome import render_page_header
from ui.components.risk_display import _count_by_level, exclude_removed_students
from ui.components.tables import show_dataframe


def render(current_user: dict) -> None:
    grade_label = grade_scope_label(current_user)
    title = f"Class {assigned_grade_for_user(current_user)} Dashboard" if grade_label else "Dashboard"
    render_page_header(
        title,
        admin_page_subtitle(f"Welcome back, {current_user['full_name']}.", current_user),
        badge_text="Admin",
        badge_variant="indigo",
    )

    grade_scope = assigned_grade_for_user(current_user)
    owner_id = student_owner_id(current_user)
    with get_db_session() as session:
        counts = get_dashboard_counts(
            session, assigned_grade=grade_scope, admin_user_id=owner_id
        )
        student_filters = [User.role == "student"]
        if owner_id is not None:
            student_filters.append(User.created_by_admin_id == owner_id)
        student_query = select(User.full_name, User.email).where(*student_filters)
        if grade_scope is not None:
            from src.db.models import StudentProfile

            student_query = (
                select(User.full_name, User.email)
                .join(StudentProfile, StudentProfile.user_id == User.id)
                .where(*student_filters, StudentProfile.semester == grade_scope)
            )
        students = session.execute(student_query.order_by(User.full_name.asc())).all()
        predictions = list_latest_predictions_per_student(
            session,
            limit=100,
            assigned_grade=grade_scope,
            admin_user_id=owner_id,
        )

    metric_cols = st.columns(4)
    metric_cols[0].metric("Students", counts["total_students"])
    metric_cols[1].metric("Academic records", counts["academic_records"])
    metric_cols[2].metric("Predictions", len(predictions))
    metric_cols[3].metric("Assessments", counts["total_assessments"])

    left, right = st.columns((1.25, 1))
    with left:
        with section(
            "Latest dropout risk",
            "Most recent score per student. Refresh from Dropout Analysis.",
        ):
            if predictions:
                show_dataframe(
                    [
                        {
                            "student_name": row["student_name"],
                            "risk_score": row["risk_score"],
                            "risk_level": row["risk_level"],
                            "predicted_at": row["predicted_at"],
                        }
                        for row in predictions
                    ],
                    columns=["student_name", "risk_score", "risk_level", "predicted_at"],
                )
            else:
                st.info("No predictions yet. Upload data, train the model, and run predictions.")

    with right:
        with section("Students", "Accounts in the system."):
            if students:
                show_dataframe(
                    [{"full_name": row.full_name, "email": row.email} for row in students],
                    columns=["full_name", "email"],
                )
            else:
                st.info("No students yet. Create accounts under Student Management.")

    if predictions:
        filtered = exclude_removed_students(predictions)
        counts = _count_by_level(filtered)
        with section(
            "Dropout risk summary",
            "High-level counts. Open Dropout Analysis for full risk explanations per student.",
        ):
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("High risk", counts.get("High", 0))
            r2.metric("Medium risk", counts.get("Medium", 0))
            r3.metric("Low risk", counts.get("Low", 0))
            r4.metric("Students scored", len(filtered))
            if st.button("View details", type="primary", use_container_width=True, key="dash_risk_details"):
                st.session_state["nav_page"] = "Dropout Analysis"
                st.session_state["focus_risk_explanations"] = True
                st.rerun()

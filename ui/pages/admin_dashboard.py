import streamlit as st
from sqlalchemy import select

from src.db.database import get_db_session
from src.db.models import User
from src.services.dropout_service import list_latest_predictions_per_student
from src.services.user_service import get_dashboard_counts
from ui.components.charts import risk_distribution_chart
from ui.components.layout import section, show_plotly_chart
from ui.components.page_chrome import render_page_header
from ui.components.risk_display import render_risk_explanations_section
from ui.components.tables import show_dataframe


def render(current_user: dict) -> None:
    render_page_header(
        "Dashboard",
        f"Welcome back, {current_user['full_name']}.",
        badge_text="Admin",
        badge_variant="indigo",
    )

    with get_db_session() as session:
        counts = get_dashboard_counts(session)
        students = session.execute(
            select(User.full_name, User.email).where(User.role == "student").order_by(User.full_name.asc())
        ).all()
        predictions = list_latest_predictions_per_student(session, limit=100)

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
        st.divider()
        render_risk_explanations_section(predictions, section_key="admin_risk_expl")

    chart = risk_distribution_chart(predictions if predictions else [])
    with section("Risk distribution", "Count of students in each risk band."):
        if chart:
            show_plotly_chart(chart, key="admin_dashboard_risk_chart")
        else:
            st.info("Chart appears after predictions are available.")

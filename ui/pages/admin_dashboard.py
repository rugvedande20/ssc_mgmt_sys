import pandas as pd
import streamlit as st
from sqlalchemy import select

from src.db.database import get_db_session
from src.db.models import DropoutPrediction, User
from src.services.user_service import get_dashboard_counts
from ui.components.charts import risk_distribution_chart


def render(current_user: dict) -> None:
    st.title("Admin Dashboard")
    st.caption(f"Welcome, {current_user['full_name']}. This dashboard is intentionally lightweight for fast load times.")

    with get_db_session() as session:
        counts = get_dashboard_counts(session)
        students = session.execute(
            select(User.full_name, User.email).where(User.role == "student").order_by(User.full_name.asc())
        ).all()
        predictions = session.execute(
            select(User.full_name, DropoutPrediction.risk_score, DropoutPrediction.risk_level, DropoutPrediction.predicted_at)
            .join(DropoutPrediction, DropoutPrediction.student_id == User.id)
            .order_by(DropoutPrediction.predicted_at.desc())
        ).all()

    metric_cols = st.columns(4)
    metric_cols[0].metric("Students", counts["total_students"])
    metric_cols[1].metric("Academic Records", counts["academic_records"])
    metric_cols[2].metric("Predictions", counts["total_predictions"])
    metric_cols[3].metric("Assessments", counts["total_assessments"])

    left, right = st.columns((1.2, 1))
    with left:
        st.subheader("Recent Dropout Signals")
        prediction_rows = [
            {
                "student_name": row.full_name,
                "risk_score": round(row.risk_score * 100, 1),
                "risk_level": row.risk_level,
                "predicted_at": row.predicted_at.strftime("%Y-%m-%d %H:%M"),
            }
            for row in predictions
        ]
        if prediction_rows:
            st.dataframe(pd.DataFrame(prediction_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No dropout predictions yet.")

    with right:
        st.subheader("Students")
        if students:
            st.dataframe(pd.DataFrame(students, columns=["Full Name", "Email"]), use_container_width=True, hide_index=True)
        else:
            st.info("No students available yet.")

    chart = risk_distribution_chart(prediction_rows if prediction_rows else [])
    if chart:
        st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Risk distribution chart will appear once predictions are available.")

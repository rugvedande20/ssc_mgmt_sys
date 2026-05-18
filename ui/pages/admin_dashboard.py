import pandas as pd
import streamlit as st
from sqlalchemy import select

from src.db.database import get_db_session
from src.db.models import User
from src.services.dropout_service import list_latest_predictions_per_student
from src.services.user_service import get_dashboard_counts
from ui.components.charts import risk_distribution_chart


def render(current_user: dict) -> None:
    st.title("Admin Dashboard")
    st.caption(f"Welcome, {current_user['full_name']}.")

    with get_db_session() as session:
        counts = get_dashboard_counts(session)
        students = session.execute(
            select(User.full_name, User.email).where(User.role == "student").order_by(User.full_name.asc())
        ).all()
        predictions = list_latest_predictions_per_student(session, limit=100)

    metric_cols = st.columns(4)
    metric_cols[0].metric("Students", counts["total_students"])
    metric_cols[1].metric("Academic Records", counts["academic_records"])
    metric_cols[2].metric("Latest Predictions", len(predictions))
    metric_cols[3].metric("Assessments", counts["total_assessments"])

    left, right = st.columns((1.2, 1))
    with left:
        st.subheader("Latest Dropout Risk (Per Student)")
        st.caption("Shows the most recent prediction for each student. Re-run predictions on the Dropout Analysis page to refresh.")
        if predictions:
            prediction_rows = [
                {
                    "student_name": row["student_name"],
                    "risk_score": row["risk_score"],
                    "risk_level": row["risk_level"],
                    "predicted_at": row["predicted_at"],
                }
                for row in predictions
            ]
            display_df = pd.DataFrame(prediction_rows)
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            with st.expander("View risk explanations"):
                for row in predictions:
                    st.markdown(f"**{row['student_name']}** ({row['risk_level']}, {row['risk_score']}%)")
                    st.caption(row["top_factors"])
        else:
            st.info("No dropout predictions yet. Add academic data, train the model, and run predictions.")

    with right:
        st.subheader("Students")
        if students:
            st.dataframe(pd.DataFrame(students, columns=["Full Name", "Email"]), use_container_width=True, hide_index=True)
        else:
            st.info("No students available yet. Create accounts under Student Management.")

    chart = risk_distribution_chart(predictions if predictions else [])
    if chart:
        st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Risk distribution chart will appear once predictions are available.")

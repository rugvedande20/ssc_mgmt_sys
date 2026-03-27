import streamlit as st
import pandas as pd

from src.db.database import get_db_session
from src.services.dropout_service import (
    get_dropout_model_status,
    list_recent_predictions,
    run_predictions_for_latest_records,
    train_dropout_model,
)
from src.services.student_service import list_students_with_latest_records
from ui.components.charts import risk_distribution_chart


def render() -> None:
    st.title("Dropout Analysis")
    st.caption("Train the baseline model once, then score the latest academic record for each student.")

    model_status = get_dropout_model_status()
    status_col, action_col = st.columns((1.4, 1))
    with status_col:
        if model_status.get("available"):
            st.success("Dropout model available")
            metrics_df = pd.DataFrame(
                [
                    {
                        "Accuracy": model_status.get("accuracy"),
                        "F1 Score": model_status.get("f1_score"),
                        "ROC AUC": model_status.get("roc_auc"),
                        "Train Size": model_status.get("train_size"),
                        "Test Size": model_status.get("test_size"),
                    }
                ]
            )
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)
            st.caption(f"Last trained: {model_status.get('trained_at', '-')}")
            st.caption("Initial model uses synthetic baseline data until an institutional training dataset is added.")
        else:
            st.warning("No dropout model has been trained yet.")

    with action_col:
        st.subheader("Actions")
        if st.button("Train Baseline Model", use_container_width=True):
            with st.spinner("Training dropout model..."):
                metrics = train_dropout_model()
            st.success("Model trained successfully.")
            st.json(metrics)
            st.rerun()

        predict_disabled = not model_status.get("available")
        if st.button("Run Predictions For Latest Records", disabled=predict_disabled, use_container_width=True):
            with get_db_session() as session:
                results = run_predictions_for_latest_records(session)
            if results:
                st.success(f"Generated {len(results)} predictions.")
            else:
                st.warning("No student records were available for prediction.")
            st.rerun()

    with get_db_session() as session:
        latest_records = list_students_with_latest_records(session)
        recent_predictions = list_recent_predictions(session, limit=50)

    st.divider()
    st.subheader("Prediction Candidates")
    if latest_records:
        st.dataframe(pd.DataFrame(latest_records), use_container_width=True, hide_index=True)
    else:
        st.info("Add academic records in the upload page to make students eligible for prediction.")

    st.divider()
    st.subheader("Recent Predictions")
    if recent_predictions:
        recent_df = pd.DataFrame(recent_predictions)
        st.dataframe(recent_df, use_container_width=True, hide_index=True)
        chart = risk_distribution_chart(recent_predictions)
        if chart:
            st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No predictions yet. Train the model and run predictions to populate this view.")

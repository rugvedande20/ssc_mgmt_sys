import streamlit as st

from src.db.database import get_db_session
from src.services.dropout_service import (
    get_dropout_model_status,
    list_latest_predictions_per_student,
    run_predictions_for_latest_records,
    train_dropout_model,
)
from ui.components.charts import risk_distribution_chart
from ui.components.layout import section, show_plotly_chart
from ui.components.model_evaluation import render_model_metrics_table
from ui.components.risk_display import render_risk_explanations_section
from ui.components.tables import show_dataframe


def render() -> None:
    st.header("Dropout Analysis")
    st.caption("Train the model once, then score the latest record for each Class 6–10 student.")

    model_status = get_dropout_model_status()

    with section("Model & actions", "Train on baseline data, then score your uploaded records."):
        status_col, action_col = st.columns((1.35, 1))
        with status_col:
            if model_status.get("available"):
                st.success("Model ready")
                render_model_metrics_table(model_status)
                st.caption(f"Last trained: {model_status.get('trained_at', '-')}")
            else:
                st.warning("No model trained yet.")

        with action_col:
            if st.button("Train baseline model", use_container_width=True, key="dropout_train"):
                with st.spinner("Training…"):
                    train_dropout_model()
                st.success("Training complete.")
                st.rerun()

            predict_disabled = not model_status.get("available")
            if st.button(
                "Run predictions",
                disabled=predict_disabled,
                use_container_width=True,
                key="dropout_predict",
            ):
                with get_db_session() as session:
                    results = run_predictions_for_latest_records(session)
                if results:
                    st.success(f"Scored {len(results)} student(s).")
                else:
                    st.warning("No records available to score.")
                st.rerun()

    with get_db_session() as session:
        latest_predictions = list_latest_predictions_per_student(session, limit=100)

    if not latest_predictions:
        st.info("No predictions yet. Train the model and run predictions.")
        return

    with section("Latest predictions", "Summary table and risk distribution."):
        show_dataframe(
            latest_predictions,
            columns=["student_name", "username", "risk_score", "risk_level", "predicted_at"],
        )
        chart = risk_distribution_chart(latest_predictions)
        if chart:
            show_plotly_chart(chart, key="dropout_analysis_risk_chart")

    with section(
        "Risk explanations",
        "Readable breakdown of factors for each student (not hidden in a dropdown).",
    ):
        render_risk_explanations_section(latest_predictions)

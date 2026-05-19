from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from src.ml.evaluation import flatten_evaluation_for_display


def render_model_metrics_table(metadata: dict[str, Any]) -> None:
    """Compact test-set metrics row (same style as the original UI)."""
    evaluation = flatten_evaluation_for_display(metadata)
    row = {
        "Accuracy": evaluation.get("accuracy"),
        "Precision": evaluation.get("precision"),
        "Recall": evaluation.get("recall"),
        "F1 score": evaluation.get("f1_score"),
        "ROC AUC": evaluation.get("roc_auc"),
        "Train size": metadata.get("train_size"),
        "Test size": metadata.get("test_size"),
    }
    if not any(value is not None for value in row.values()):
        st.info("No evaluation metrics yet. Train the model to generate them.")
        return
    st.dataframe(pd.DataFrame([row]), use_container_width=True, hide_index=True)

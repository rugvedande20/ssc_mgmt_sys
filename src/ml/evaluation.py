from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def build_test_evaluation(
    y_true: np.ndarray | list[int],
    y_pred: np.ndarray | list[int],
    y_proba: np.ndarray | list[float],
) -> dict[str, Any]:
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred)
    y_proba_arr = np.asarray(y_proba)

    cm = confusion_matrix(y_true_arr, y_pred_arr, labels=[0, 1])
    report = classification_report(
        y_true_arr,
        y_pred_arr,
        labels=[0, 1],
        target_names=["retained", "at_risk"],
        output_dict=True,
        zero_division=0,
    )

    return {
        "accuracy": round(float(accuracy_score(y_true_arr, y_pred_arr)), 4),
        "precision": round(float(precision_score(y_true_arr, y_pred_arr, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true_arr, y_pred_arr, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_true_arr, y_pred_arr, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true_arr, y_proba_arr)), 4),
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
    }


def derive_risk_thresholds(probabilities: np.ndarray | list[float]) -> dict[str, float]:
    """Held-out cutoffs targeting ~top 10% High, with floors for deployment on new cohorts."""
    scores = np.asarray(probabilities, dtype=float)
    if scores.size == 0:
        return {"high": 0.70, "medium": 0.40}
    high = max(float(np.quantile(scores, 0.90)), 0.55)
    medium = max(float(np.quantile(scores, 0.60)), 0.30)
    if medium >= high:
        medium = round(high * 0.65, 4)
    return {"high": round(high, 4), "medium": round(medium, 4)}


def cohort_adjusted_thresholds(
    probabilities: np.ndarray | list[float],
    base_thresholds: dict[str, float],
    min_cohort_size: int = 10,
) -> dict[str, float]:
    """Blend saved test thresholds with the current batch distribution."""
    scores = np.asarray(probabilities, dtype=float)
    if scores.size < min_cohort_size:
        return base_thresholds
    high = max(float(base_thresholds["high"]), float(np.quantile(scores, 0.90)))
    medium = max(float(base_thresholds["medium"]), float(np.quantile(scores, 0.60)))
    if medium >= high:
        medium = round(high * 0.65, 4)
    return {"high": round(high, 4), "medium": round(medium, 4)}


def extract_feature_importances(pipeline, top_n: int = 12) -> list[dict[str, Any]]:
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]
    try:
        names = preprocessor.get_feature_names_out()
    except Exception:
        return []
    importances = getattr(classifier, "feature_importances_", None)
    if importances is None:
        return []
    pairs = sorted(zip(names, importances), key=lambda item: item[1], reverse=True)
    return [
        {"feature": str(name), "importance": round(float(value), 4)}
        for name, value in pairs[:top_n]
    ]


def flatten_evaluation_for_display(metadata: dict[str, Any]) -> dict[str, Any]:
    """Merge legacy top-level metrics with nested evaluation block."""
    evaluation = dict(metadata.get("evaluation") or {})
    for key in ("accuracy", "precision", "recall", "f1_score", "roc_auc"):
        if key not in evaluation and key in metadata:
            evaluation[key] = metadata[key]
    return evaluation


def evaluation_metrics_rows(evaluation: dict[str, Any]) -> list[dict[str, str]]:
    label_map = {
        "accuracy": "Accuracy",
        "precision": "Precision",
        "recall": "Recall",
        "f1_score": "F1 score",
        "roc_auc": "ROC AUC",
    }
    rows: list[dict[str, str]] = []
    for key, label in label_map.items():
        value = evaluation.get(key)
        if value is not None:
            rows.append({"Metric": label, "Value": f"{float(value):.4f}"})
    return rows

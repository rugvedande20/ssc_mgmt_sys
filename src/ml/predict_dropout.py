from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from config.settings import settings
from src.ml.evaluation import cohort_adjusted_thresholds
from src.ml.train_dropout import FEATURE_COLUMNS

DEFAULT_RISK_THRESHOLDS = {"high": 0.70, "medium": 0.40}


def model_artifact_paths() -> tuple[Path, Path]:
    return settings.model_dir / "dropout_pipeline.joblib", settings.model_dir / "dropout_metadata.json"


def model_exists() -> bool:
    model_path, metadata_path = model_artifact_paths()
    return model_path.exists() and metadata_path.exists()


def load_model_bundle() -> tuple[object, dict]:
    model_path, metadata_path = model_artifact_paths()
    pipeline = joblib.load(model_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return pipeline, metadata


def get_risk_thresholds(metadata: dict | None = None) -> dict[str, float]:
    meta = metadata if metadata is not None else (load_model_bundle()[1] if model_exists() else {})
    thresholds = meta.get("risk_thresholds") or DEFAULT_RISK_THRESHOLDS
    return {
        "high": float(thresholds.get("high", DEFAULT_RISK_THRESHOLDS["high"])),
        "medium": float(thresholds.get("medium", DEFAULT_RISK_THRESHOLDS["medium"])),
    }


def predict_dropout_batch(records: list[dict]) -> list[dict]:
    if not records:
        return []
    pipeline, metadata = load_model_bundle()
    base_thresholds = get_risk_thresholds(metadata)
    features = pd.DataFrame(records)
    features = features.reindex(columns=FEATURE_COLUMNS)
    probabilities = pipeline.predict_proba(features)[:, 1]
    thresholds = cohort_adjusted_thresholds(probabilities, base_thresholds)
    return [
        {
            "risk_score": float(probability),
            "risk_level": score_to_risk_level(float(probability), thresholds),
        }
        for probability in probabilities
    ]


def score_to_risk_level(score: float, thresholds: dict[str, float] | None = None) -> str:
    cuts = thresholds or DEFAULT_RISK_THRESHOLDS
    high = cuts["high"]
    medium = cuts["medium"]
    if score >= high:
        return "High"
    if score >= medium:
        return "Medium"
    return "Low"

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from config.settings import settings
from src.ml.train_dropout import FEATURE_COLUMNS


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


def predict_dropout_batch(records: list[dict]) -> list[dict]:
    if not records:
        return []
    pipeline, _ = load_model_bundle()
    features = pd.DataFrame(records)
    features = features.reindex(columns=FEATURE_COLUMNS)
    probabilities = pipeline.predict_proba(features)[:, 1]
    return [
        {
            "risk_score": float(probability),
            "risk_level": score_to_risk_level(float(probability)),
        }
        for probability in probabilities
    ]


def score_to_risk_level(score: float) -> str:
    if score >= 0.66:
        return "High"
    if score >= 0.35:
        return "Medium"
    return "Low"

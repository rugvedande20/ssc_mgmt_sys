from __future__ import annotations

import json
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from config.settings import settings


FEATURE_COLUMNS = [
    "attendance_percentage",
    "cgpa",
    "internal_marks",
    "backlog_count",
    "fee_pending",
    "scholarship_status",
    "extracurricular_participation",
    "disciplinary_issues",
    "engagement_score",
    "stress_level",
    "age",
    "semester",
    "family_income_band",
    "parental_education",
    "travel_distance_km",
    "internet_access",
    "department",
]

NUMERIC_FEATURES = [
    "attendance_percentage",
    "cgpa",
    "internal_marks",
    "backlog_count",
    "disciplinary_issues",
    "engagement_score",
    "stress_level",
    "age",
    "semester",
    "travel_distance_km",
]

CATEGORICAL_FEATURES = [
    "fee_pending",
    "scholarship_status",
    "extracurricular_participation",
    "family_income_band",
    "parental_education",
    "internet_access",
    "department",
]

TARGET_COLUMN = "dropout_label"


def train_and_save_dropout_model(random_state: int = 42) -> dict:
    settings.model_dir.mkdir(parents=True, exist_ok=True)
    dataset = build_synthetic_dropout_dataset(random_state=random_state)

    train_df, test_df = train_test_split(
        dataset,
        test_size=0.2,
        stratify=dataset[TARGET_COLUMN],
        random_state=random_state,
    )

    preprocessor = build_preprocessor()
    classifier = RandomForestClassifier(
        n_estimators=220,
        max_depth=8,
        min_samples_leaf=3,
        random_state=random_state,
    )
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )
    pipeline.fit(train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN])

    probabilities = pipeline.predict_proba(test_df[FEATURE_COLUMNS])[:, 1]
    predictions = pipeline.predict(test_df[FEATURE_COLUMNS])

    metrics = {
        "accuracy": round(float(accuracy_score(test_df[TARGET_COLUMN], predictions)), 4),
        "f1_score": round(float(f1_score(test_df[TARGET_COLUMN], predictions)), 4),
        "roc_auc": round(float(roc_auc_score(test_df[TARGET_COLUMN], probabilities)), 4),
        "train_size": int(len(train_df)),
        "test_size": int(len(test_df)),
        "trained_at": datetime.utcnow().isoformat(),
        "dataset_type": "synthetic_baseline",
    }

    model_path = settings.model_dir / "dropout_pipeline.joblib"
    metadata_path = settings.model_dir / "dropout_metadata.json"
    joblib.dump(pipeline, model_path)
    metadata_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def build_preprocessor() -> ColumnTransformer:
    numeric_transformer = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )


def build_synthetic_dropout_dataset(rows: int = 1400, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    from config.school_context import SCHOOL_FOCUS_AREAS_FOR_ML

    streams = np.array(SCHOOL_FOCUS_AREAS_FOR_ML)
    income_bands = np.array(["Low", "Middle", "Upper Middle", "High"])
    parental_education = np.array(["Up to Class 10", "Graduate", "Postgraduate"])
    yes_no = np.array(["Yes", "No"])
    internet_levels = np.array(["Yes", "No", "Limited"])

    df = pd.DataFrame(
        {
            "attendance_percentage": rng.normal(82, 11, rows).clip(40, 100),
            "cgpa": rng.normal(68, 14, rows).clip(35, 98),
            "internal_marks": rng.normal(66, 15, rows).clip(30, 98),
            "backlog_count": rng.poisson(0.9, rows).clip(0, 6),
            "fee_pending": rng.choice(yes_no, rows, p=[0.28, 0.72]),
            "scholarship_status": rng.choice(yes_no, rows, p=[0.33, 0.67]),
            "extracurricular_participation": rng.choice(yes_no, rows, p=[0.55, 0.45]),
            "disciplinary_issues": rng.poisson(0.35, rows).clip(0, 5),
            "engagement_score": rng.normal(6.3, 1.8, rows).clip(1, 10),
            "stress_level": rng.normal(5.2, 1.9, rows).clip(1, 10),
            "age": rng.integers(11, 17, rows),
            "semester": rng.integers(6, 11, rows),
            "family_income_band": rng.choice(income_bands, rows, p=[0.32, 0.38, 0.2, 0.1]),
            "parental_education": rng.choice(parental_education, rows, p=[0.38, 0.42, 0.2]),
            "travel_distance_km": rng.normal(8, 6, rows).clip(0, 35),
            "internet_access": rng.choice(internet_levels, rows, p=[0.78, 0.08, 0.14]),
            "department": rng.choice(streams, rows),
        }
    )

    risk_signal = (
        (100 - df["attendance_percentage"]) * 0.055
        + (72 - df["cgpa"]) * 0.09
        + df["backlog_count"] * 0.45
        + (df["fee_pending"] == "Yes").astype(float) * 0.85
        + (df["scholarship_status"] == "No").astype(float) * 0.18
        + (df["extracurricular_participation"] == "No").astype(float) * 0.15
        + df["disciplinary_issues"] * 0.4
        + (7.5 - df["engagement_score"]) * 0.38
        + (df["stress_level"] - 4.5) * 0.28
        + (df["internet_access"] != "Yes").astype(float) * 0.32
        + (df["family_income_band"] == "Low").astype(float) * 0.42
        + (df["travel_distance_km"] > 18).astype(float) * 0.25
    )
    noise = rng.normal(0, 0.75, rows)
    dropout_probability = 1 / (1 + np.exp(-(risk_signal - 2.9 + noise)))
    df[TARGET_COLUMN] = (dropout_probability > 0.5).astype(int)
    return df

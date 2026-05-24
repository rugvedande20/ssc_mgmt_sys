from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

# Internal field keys -> human-readable column titles
COLUMN_LABELS: dict[str, str] = {
    "id": "ID",
    "full_name": "Full name",
    "student_name": "Student",
    "username": "Username",
    "email": "Email",
    "school": "School",
    "class": "Class",
    "attendance_percentage": "Attendance (%)",
    "overall_marks_pct": "Overall marks (%)",
    "internal_marks": "Term test (%)",
    "subjects_below_passing": "Subjects below passing",
    "recorded_at": "Recorded at",
    "predicted_at": "Predicted at",
    "activity_by": "Activity by",
    "updated_at": "Updated at",
    "risk_score": "Risk score (%)",
    "risk_level": "Risk level",
    "top_factors": "Key factors",
    "intervention_type": "Type",
    "module": "Module",
    "priority": "Priority",
    "intensity": "Intensity",
    "status": "Status",
    "scheduled_at": "Scheduled at",
    "completed_at": "Completed at",
    "action_taken": "Action taken",
    "suggested_priority": "Suggested priority",
    "suggested_intensity": "Suggested intensity",
    "scheduled_count": "Scheduled",
    "completed_count": "Completed",
    "student_username": "Student username",
    "login_username": "Login username",
    "password": "Password",
    "temporary_password": "Temporary password",
    "csv_label": "CSV label",
    "submitted_at": "Submitted at",
    "generated_at": "Generated at",
    "top_codes": "Top codes",
    "summary": "Summary",
    "section": "Section",
    "score": "Score",
    "match_score": "Match score",
    "career_title": "Career idea",
    "reason": "Reason",
}


def _coerce_arrow_safe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in out.columns:
        if out[column].dtype == object:
            out[column] = out[column].map(lambda value: "" if value is None else str(value))
    return out


def label_dataframe(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    if columns is not None:
        available = [column for column in columns if column in df.columns]
        df = df[available]
    rename = {key: COLUMN_LABELS.get(key, key.replace("_", " ").strip().title()) for key in df.columns}
    return _coerce_arrow_safe(df.rename(columns=rename))


def show_dataframe(
    data: pd.DataFrame | list[dict[str, Any]],
    *,
    columns: list[str] | None = None,
    **kwargs: Any,
) -> None:
    frame = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data
    st.dataframe(label_dataframe(frame, columns=columns), use_container_width=True, hide_index=True, **kwargs)

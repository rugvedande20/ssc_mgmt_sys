from __future__ import annotations

import io

import pandas as pd

from config.school_context import ACADEMIC_CSV_ALIASES


def read_tabular_upload(uploaded_file, file_bytes: bytes | None = None) -> pd.DataFrame:
    """Read a CSV or Excel upload into a DataFrame (all rows, empty rows removed)."""
    filename = (uploaded_file.name or "").lower()
    raw_bytes = file_bytes if file_bytes is not None else uploaded_file.getvalue()

    if filename.endswith((".xlsx", ".xls")):
        frame = pd.read_excel(io.BytesIO(raw_bytes))
    else:
        frame = _read_csv_bytes(raw_bytes)

    return prepare_import_dataframe(frame)


def _read_csv_bytes(raw_bytes: bytes) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        for sep in (",", ";", "\t"):
            try:
                return pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding, sep=sep)
            except Exception:
                continue
    return pd.read_csv(io.BytesIO(raw_bytes))


def rename_import_columns(frame: pd.DataFrame) -> pd.DataFrame:
    column_map: dict[str, str] = {}
    for column in frame.columns:
        normalized = str(column).strip().lower().replace(" ", "_")
        if normalized in ACADEMIC_CSV_ALIASES:
            column_map[column] = ACADEMIC_CSV_ALIASES[normalized]
        else:
            column_map[column] = normalized
    return frame.rename(columns=column_map)


def prepare_import_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    frame = rename_import_columns(frame.copy())
    frame = frame.dropna(how="all")

    has_slug = "student_username" in frame.columns
    has_names = "first_name" in frame.columns and "last_name" in frame.columns
    if not has_slug and not has_names:
        raise ValueError(
            "CSV must include a student_username column (e.g. aarav_patil) "
            "or both first_name and last_name columns."
        )

    if has_slug:
        frame["student_username"] = frame["student_username"].astype(str).str.strip()
        frame = frame[frame["student_username"].str.len() > 0]
        invalid_names = {"nan", "none", ""}
        frame = frame[~frame["student_username"].str.lower().isin(invalid_names)]

    return frame.reset_index(drop=True)

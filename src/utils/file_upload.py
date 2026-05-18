from __future__ import annotations

import io

import pandas as pd


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


def prepare_import_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    frame = frame.dropna(how="all")
    if "student_username" in frame.columns:
        frame["student_username"] = frame["student_username"].astype(str).str.strip()
        frame = frame[frame["student_username"].str.len() > 0]
        invalid_names = {"nan", "none", ""}
        frame = frame[~frame["student_username"].str.lower().isin(invalid_names)]
    return frame.reset_index(drop=True)

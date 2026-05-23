"""Display activity timestamp + actor in the UI."""

from __future__ import annotations

import streamlit as st

from src.utils.activity import ACTIVITY_BY_UNKNOWN, format_activity_meta


def render_activity_caption(
    *,
    at: str | None = None,
    at_label: str = "Recorded at",
    by: str | None = None,
) -> None:
    if not at and not by:
        return
    st.caption(format_activity_meta(at=at, at_label=at_label, by=by or ACTIVITY_BY_UNKNOWN))

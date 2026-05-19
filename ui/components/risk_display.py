from __future__ import annotations

import html
import re
from typing import Any

import streamlit as st

RISK_LEVEL_STYLES: dict[str, tuple[str, str, str]] = {
    "Low": ("#FEF9C3", "#A16207", "#FACC15"),
    "Medium": ("#FFEDD5", "#C2410C", "#FB923C"),
    "High": ("#FEE2E2", "#B91C1C", "#F87171"),
}


def format_display_value(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(value)


def risk_level_badge(level: str) -> str:
    safe_level = html.escape(level or "—")
    bg, text, border = RISK_LEVEL_STYLES.get(level, ("#F1F5F9", "#475569", "#CBD5E1"))
    return (
        f'<span style="display:inline-block;background:{bg};color:{text};'
        f'border:1px solid {border};padding:0.25rem 0.75rem;border-radius:999px;'
        f'font-weight:700;font-size:0.82rem;">{safe_level}</span>'
    )


def parse_factor_bullets(top_factors: str) -> list[str]:
    if not top_factors:
        return []
    text = top_factors.strip()
    if text.lower().startswith("key factors:"):
        text = text.split(":", 1)[1]
    parts = re.split(r",|;|\n", text)
    return [part.strip().rstrip(".") for part in parts if part.strip()]


def render_factor_list(top_factors: str) -> None:
    bullets = parse_factor_bullets(top_factors)
    if bullets:
        for item in bullets:
            st.markdown(f"- {item}")
    elif top_factors:
        st.write(top_factors)
    else:
        st.caption("No specific factors recorded.")


def render_risk_explanations_section(predictions: list[dict[str, Any]]) -> None:
    if not predictions:
        st.caption("No explanations available yet.")
        return

    for index in range(0, len(predictions), 2):
        row_pair = predictions[index : index + 2]
        cols = st.columns(len(row_pair))
        for col, row in zip(cols, row_pair):
            with col:
                with st.container(border=True):
                    head_left, head_right = st.columns((1.4, 1))
                    name = row.get("student_name", "Student")
                    head_left.markdown(f"**{name}**")
                    head_right.markdown(
                        risk_level_badge(str(row.get("risk_level", "—"))),
                        unsafe_allow_html=True,
                    )
                    st.caption(
                        f"Score **{row.get('risk_score', '—')}%** · "
                        f"{row.get('predicted_at', '—')}"
                    )
                    render_factor_list(str(row.get("top_factors", "")))

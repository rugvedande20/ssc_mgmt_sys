from __future__ import annotations

import html
import re
from datetime import datetime

from src.utils.datetime_ist import format_date_ist, parse_display_datetime
from typing import Any

import streamlit as st

EXCLUDED_STUDENT_NAME = "Rahul Verma"
RISK_EXPLANATIONS_ANCHOR_ID = "risk-explanations-section"

RISK_LEVEL_STYLES: dict[str, tuple[str, str, str]] = {
    "Low": ("#F0FDF4", "#15803D", "#86EFAC"),
    "Medium": ("#FFF7ED", "#C2410C", "#FDBA74"),
    "High": ("#FEE2E2", "#B91C1C", "#FCA5A5"),
}

RISK_BAR_COLORS: dict[str, str] = {
    "Low": "#22C55E",
    "Medium": "#F97316",
    "High": "#EF4444",
}

AVATAR_STYLES: dict[str, tuple[str, str]] = {
    "High": ("#FEE2E2", "#B91C1C"),
    "Medium": ("#FFEDD5", "#C2410C"),
    "Low": ("#F0FDF4", "#15803D"),
}

FACTOR_TAG_STYLES: dict[str, tuple[str, str, str]] = {
    "low attendance": ("#FFF7ED", "#EA580C", "Low Attendance"),
    "low overall marks": ("#EFF6FF", "#2563EB", "Low Overall Marks"),
    "multiple subjects below passing level": ("#F5F3FF", "#7C3AED", "Multiple Subjects Below Passing"),
    "pending fees": ("#FEF2F2", "#DC2626", "Pending Fees"),
    "low engagement": ("#F8FAFC", "#475569", "Low Engagement"),
    "high stress": ("#FDF4FF", "#A21CAF", "High Stress"),
    "limited internet access": ("#ECFEFF", "#0891B2", "Limited Internet Access"),
}

RISK_FILTER_OPTIONS = ("All Students", "High Risk", "Medium Risk", "Low Risk")
FILTER_TO_LEVEL = {
    "All Students": None,
    "High Risk": "High",
    "Medium Risk": "Medium",
    "Low Risk": "Low",
}

CARD_SECTION_LABEL_STYLE = (
    "font-size:0.85rem;font-weight:700;color:#475569;"
    "margin:0 0 0.5rem 0;line-height:1.2;"
)


def format_display_value(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(value)


def exclude_removed_students(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in predictions
        if str(row.get("student_name", "")).strip().lower() != EXCLUDED_STUDENT_NAME.lower()
    ]


def risk_level_badge(level: str) -> str:
    safe_level = html.escape(level or "—")
    bg, text, border = RISK_LEVEL_STYLES.get(level, ("#F1F5F9", "#475569", "#CBD5E1"))
    return (
        f'<span style="display:inline-block;background:{bg};color:{text};'
        f'border:1px solid {border};padding:0.2rem 0.55rem;border-radius:999px;'
        f'font-weight:700;font-size:0.68rem;letter-spacing:0.03em;">'
        f"{safe_level.upper()} RISK</span>"
    )


def parse_factor_bullets(top_factors: str) -> list[str]:
    if not top_factors:
        return []
    text = top_factors.strip()
    if text.lower().startswith("key factors:"):
        text = text.split(":", 1)[1]
    parts = re.split(r",|;|\n", text)
    return [part.strip().rstrip(".") for part in parts if part.strip()]


def student_initials(name: str) -> str:
    parts = [part for part in re.split(r"\s+", name.strip()) if part]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def format_long_date(value: str) -> str:
    parsed = parse_display_datetime(value)
    if parsed:
        return format_date_ist(parsed)
    return value


def _risk_score_percent(score: Any) -> float:
    try:
        return max(0.0, min(100.0, float(score)))
    except (TypeError, ValueError):
        return 0.0


def _inject_risk_explanations_styles() -> None:
    st.markdown(
        """
        <style>
          .risk-expl-anchor {
            scroll-margin-top: 5.5rem;
          }
          .risk-expl-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.35rem;
          }
          .risk-expl-title {
            font-size: 1.65rem;
            font-weight: 800;
            color: #0f172a;
            margin: 0;
            line-height: 1.2;
          }
          .risk-expl-subtitle {
            color: #64748b;
            font-size: 0.95rem;
            margin: 0.35rem 0 0 0;
          }
          .risk-summary-card {
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 12px;
            padding: 0.85rem 1rem;
            min-width: 210px;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            box-shadow: 0 2px 10px rgba(239, 68, 68, 0.08);
          }
          .risk-summary-icon {
            width: 42px;
            height: 42px;
            border-radius: 10px;
            background: #fee2e2;
            color: #dc2626;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            font-weight: 700;
          }
          .risk-summary-label {
            color: #991b1b;
            font-size: 0.78rem;
            font-weight: 600;
          }
          .risk-summary-value {
            color: #dc2626;
            font-size: 1.75rem;
            font-weight: 800;
            line-height: 1;
          }
          .risk-summary-caption {
            color: #b91c1c;
            font-size: 0.72rem;
          }
          div[data-testid="stPills"] > div,
          div[data-testid="stRadio"] > div[role="radiogroup"] {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
            padding: 0.5rem 0.55rem;
            border-radius: 14px;
            border: 1px solid #e2e8f0;
          }
          div[data-testid="stPills"] button,
          div[data-testid="stRadio"] > div[role="radiogroup"] > label {
            background: #ffffff !important;
            border: 1.5px solid #e2e8f0 !important;
            border-radius: 999px !important;
            padding: 0.48rem 1rem !important;
            margin: 0 !important;
            font-weight: 600 !important;
            font-size: 0.84rem !important;
            transition: all 0.15s ease;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
          }
          div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
            display: none !important;
          }
          div[data-testid="stPills"] button:hover,
          div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
            transform: translateY(-1px);
            box-shadow: 0 3px 8px rgba(15, 23, 42, 0.08);
          }
          div[data-testid="stPills"] button:nth-child(1),
          div[data-testid="stRadio"] > div[role="radiogroup"] > label:nth-child(1) {
            color: #4338ca !important;
            border-color: #c7d2fe !important;
          }
          div[data-testid="stPills"] button:nth-child(2),
          div[data-testid="stRadio"] > div[role="radiogroup"] > label:nth-child(2) {
            color: #b91c1c !important;
            border-color: #fecaca !important;
          }
          div[data-testid="stPills"] button:nth-child(3),
          div[data-testid="stRadio"] > div[role="radiogroup"] > label:nth-child(3) {
            color: #c2410c !important;
            border-color: #fed7aa !important;
          }
          div[data-testid="stPills"] button:nth-child(4),
          div[data-testid="stRadio"] > div[role="radiogroup"] > label:nth-child(4) {
            color: #15803d !important;
            border-color: #bbf7d0 !important;
          }
          div[data-testid="stPills"] button[kind="primary"],
          div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"]:nth-child(1) {
            background: linear-gradient(135deg, #e0e7ff 0%, #ede9fe 100%) !important;
            border-color: #818cf8 !important;
            color: #3730a3 !important;
            font-weight: 700 !important;
          }
          div[data-testid="stPills"] button[kind="primary"]:nth-child(2),
          div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"]:nth-child(2) {
            background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%) !important;
            border-color: #f87171 !important;
            color: #991b1b !important;
            font-weight: 700 !important;
          }
          div[data-testid="stPills"] button[kind="primary"]:nth-child(3),
          div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"]:nth-child(3) {
            background: linear-gradient(135deg, #ffedd5 0%, #fed7aa 100%) !important;
            border-color: #fb923c !important;
            color: #9a3412 !important;
            font-weight: 700 !important;
          }
          div[data-testid="stPills"] button[kind="primary"]:nth-child(4),
          div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"]:nth-child(4) {
            background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%) !important;
            border-color: #4ade80 !important;
            color: #166534 !important;
            font-weight: 700 !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _card_header_html(name: str, initials: str, level: str, pct: float) -> str:
    safe_name = html.escape(name)
    safe_initials = html.escape(initials)
    score_color = RISK_BAR_COLORS.get(level, "#EF4444")
    avatar_bg, avatar_text = AVATAR_STYLES.get(level, ("#FEE2E2", "#B91C1C"))
    badge = risk_level_badge(level)
    return (
        "<div style='display:flex;align-items:center;justify-content:space-between;"
        "gap:12px;width:100%;'>"
        "<div style='display:flex;align-items:center;gap:12px;min-width:0;flex:1;'>"
        f"<div style='flex-shrink:0;width:48px;height:48px;border-radius:50%;"
        f"background:{avatar_bg};color:{avatar_text};font-weight:800;font-size:0.95rem;"
        f"display:flex;align-items:center;justify-content:center;'>{safe_initials}</div>"
        "<div style='min-width:0;display:flex;flex-direction:column;justify-content:center;"
        "gap:5px;'>"
        f"<div style='font-size:1.05rem;font-weight:700;color:#0f172a;line-height:1.2;"
        f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{safe_name}</div>"
        f"<div>{badge}</div></div></div>"
        "<div style='text-align:right;flex-shrink:0;padding-left:8px;'>"
        f"<div style='font-size:2rem;font-weight:800;color:{score_color};line-height:1;'>"
        f"{pct:.0f}%</div>"
        "<div style='font-size:0.72rem;color:#94a3b8;margin-top:2px;'>risk score</div>"
        "</div></div>"
    )


def _render_card_section_label(text: str, *, first: bool = False) -> None:
    style = CARD_SECTION_LABEL_STYLE
    if first:
        style += "padding-top:0.55rem;border-top:1px solid #e2e8f0;"
    st.markdown(
        f"<div style='{style}'>{html.escape(text)}</div>",
        unsafe_allow_html=True,
    )


def _risk_bar_section_html(pct: float, level: str) -> str:
    color = RISK_BAR_COLORS.get(level, "#EF4444")
    return (
        f"<div style='height:12px;border-radius:999px;background:#f1f5f9;overflow:hidden;"
        f"margin-bottom:0.85rem;'>"
        f"<div style='width:{pct:.1f}%;height:100%;background:{color};"
        f"border-radius:999px;'></div></div>"
    )


def render_student_card(row: dict[str, Any]) -> None:
    """Native Streamlit card — no iframe or large HTML blocks."""
    name = str(row.get("student_name", "Student"))
    level = str(row.get("risk_level", "—"))
    initials = student_initials(name)
    pct = _risk_score_percent(row.get("risk_score", 0))
    factor_items = parse_factor_bullets(str(row.get("top_factors", "")))

    with st.container(border=True):
        st.markdown(_card_header_html(name, initials, level, pct), unsafe_allow_html=True)
        _render_card_section_label("Risk bar", first=True)
        st.markdown(_risk_bar_section_html(pct, level), unsafe_allow_html=True)
        _render_card_section_label("Risk factors")
        if factor_items:
            chip_html = " ".join(_factor_chip_html(item) for item in factor_items)
            st.markdown(chip_html, unsafe_allow_html=True)
        else:
            st.caption("No specific factors recorded.")


def _factor_chip_html(factor_key: str) -> str:
    normalized = factor_key.strip().lower()
    bg, color, label = FACTOR_TAG_STYLES.get(
        normalized,
        ("#F1F5F9", "#475569", factor_key.strip().title() or "Risk factor"),
    )
    safe_label = html.escape(label)
    return (
        f"<span style='display:inline-block;margin:0 0.35rem 0.35rem 0;padding:0.35rem 0.6rem;"
        f"border-radius:999px;font-size:0.72rem;font-weight:700;background:{bg};color:{color};'>"
        f"{safe_label}</span>"
    )


def _render_student_cards_grid(rows: list[dict[str, Any]]) -> None:
    for index in range(0, len(rows), 2):
        pair = rows[index : index + 2]
        cols = st.columns(len(pair))
        for col, row in zip(cols, pair):
            with col:
                render_student_card(row)


def _count_by_level(predictions: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"High": 0, "Medium": 0, "Low": 0}
    for row in predictions:
        level = str(row.get("risk_level", ""))
        if level in counts:
            counts[level] += 1
    return counts


def _filter_predictions(
    predictions: list[dict[str, Any]],
    *,
    risk_filter: str,
    selected_date: str | None,
) -> list[dict[str, Any]]:
    filtered = predictions
    level = FILTER_TO_LEVEL.get(risk_filter)
    if level:
        filtered = [row for row in filtered if row.get("risk_level") == level]

    if selected_date:
        filtered = [
            row
            for row in filtered
            if format_long_date(str(row.get("predicted_at", ""))) == selected_date
        ]
    return filtered


def render_factor_list(top_factors: str) -> None:
    bullets = parse_factor_bullets(top_factors)
    if bullets:
        for item in bullets:
            st.markdown(f"- {item}")
    elif top_factors:
        st.write(top_factors)
    else:
        st.caption("No specific factors recorded.")


def render_risk_explanations_section(
    predictions: list[dict[str, Any]],
    *,
    section_key: str = "risk_expl",
) -> None:
    predictions = exclude_removed_students(predictions)
    _inject_risk_explanations_styles()

    if not predictions:
        st.caption("No explanations available yet.")
        return

    counts = _count_by_level(predictions)
    high_risk_count = counts["High"]
    parsed_dates = [
        parsed
        for row in predictions
        if (parsed := _parse_display_date(format_long_date(str(row.get("predicted_at", "")))))
    ]
    latest_date = format_date_ist(max(parsed_dates)) if parsed_dates else ""
    unique_dates = sorted(
        {format_long_date(str(row.get("predicted_at", ""))) for row in predictions},
        key=lambda value: _parse_display_date(value) or datetime.min,
        reverse=True,
    )

    st.markdown(
        f'<div id="{RISK_EXPLANATIONS_ANCHOR_ID}" class="risk-expl-anchor"></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="risk-expl-header">
          <div>
            <h2 class="risk-expl-title">Risk Explanations</h2>
            <p class="risk-expl-subtitle">Factors behind each student's latest risk band. &#9432;</p>
          </div>
          <div class="risk-summary-card">
            <div class="risk-summary-icon">&#128737;</div>
            <div>
              <div class="risk-summary-label">High Risk Students</div>
              <div class="risk-summary-value">{high_risk_count}</div>
              <div class="risk-summary-caption">Students need immediate attention</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    toolbar_left, toolbar_right = st.columns((2.4, 1))
    with toolbar_left:
        risk_filter = st.pills(
            "Risk level",
            RISK_FILTER_OPTIONS,
            default=RISK_FILTER_OPTIONS[0],
            selection_mode="single",
            label_visibility="collapsed",
            key=f"{section_key}_risk_filter",
            format_func=lambda option: _risk_filter_label(option, counts, len(predictions)),
        )
        if not risk_filter:
            risk_filter = RISK_FILTER_OPTIONS[0]
    with toolbar_right:
        date_options = [f"Latest ({latest_date})"] + [
            date for date in unique_dates if date != latest_date
        ]
        selected_date_label = st.selectbox(
            "Snapshot date",
            date_options,
            label_visibility="collapsed",
            key=f"{section_key}_date_filter",
        )

    selected_date: str | None = None
    if selected_date_label and not selected_date_label.startswith("Latest ("):
        selected_date = selected_date_label
    elif selected_date_label.startswith("Latest (") and latest_date:
        selected_date = latest_date

    visible = _filter_predictions(
        predictions,
        risk_filter=risk_filter,
        selected_date=selected_date,
    )

    if not visible:
        st.info("No students match the selected filters.")
        return

    _render_student_cards_grid(visible)


def _parse_display_date(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%b %d, %Y")
    except ValueError:
        return None


def scroll_to_risk_explanations() -> None:
    """Scroll main page to the risk explanations anchor (after navigation from dashboard)."""
    import streamlit.components.v1 as components

    anchor = RISK_EXPLANATIONS_ANCHOR_ID
    components.html(
        f"""
        <script>
        (function() {{
          const id = "{anchor}";
          function go() {{
            const doc = window.parent.document;
            const el = doc.getElementById(id);
            if (el) {{
              el.scrollIntoView({{ behavior: "smooth", block: "start" }});
              return true;
            }}
            return false;
          }}
          if (!go()) {{
            let attempts = 0;
            const timer = setInterval(function() {{
              if (go() || ++attempts > 50) clearInterval(timer);
            }}, 120);
          }}
        }})();
        </script>
        """,
        height=0,
    )


def _risk_filter_label(option: str, counts: dict[str, int], total: int) -> str:
    icons = {
        "All Students": "◉",
        "High Risk": "▲",
        "Medium Risk": "◆",
        "Low Risk": "▼",
    }
    icon = icons.get(option, "•")
    if option == "All Students":
        return f"{icon}  All Students ({total})"
    level = FILTER_TO_LEVEL[option]
    assert level is not None
    return f"{icon}  {option} ({counts.get(level, 0)})"

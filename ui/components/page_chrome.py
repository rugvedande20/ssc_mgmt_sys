from __future__ import annotations

import html
from typing import Any

import streamlit as st

BADGE_VARIANTS: dict[str, tuple[str, str, str]] = {
    "indigo": ("#EEF2FF", "#4338CA", "#C7D2FE"),
    "violet": ("#F5F3FF", "#6D28D9", "#DDD6FE"),
    "sky": ("#F0F9FF", "#0369A1", "#BAE6FD"),
    "emerald": ("#ECFDF5", "#047857", "#A7F3D0"),
    "amber": ("#FFFBEB", "#B45309", "#FDE68A"),
    "rose": ("#FFF1F2", "#BE123C", "#FECDD3"),
}

PANEL_VARIANTS: dict[str, tuple[str, str, str]] = {
    "indigo": ("#EEF2FF", "#4338CA", "#E0E7FF"),
    "sky": ("#F0F9FF", "#0369A1", "#E0F2FE"),
    "emerald": ("#ECFDF5", "#047857", "#D1FAE5"),
    "amber": ("#FFFBEB", "#B45309", "#FEF3C7"),
    "rose": ("#FFF1F2", "#BE123C", "#FFE4E6"),
}


def render_page_header(
    title: str,
    subtitle: str,
    *,
    badge_text: str | None = None,
    badge_variant: str = "indigo",
) -> None:
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    badge_html = ""
    if badge_text:
        bg, color, border = BADGE_VARIANTS.get(badge_variant, BADGE_VARIANTS["indigo"])
        safe_badge = html.escape(badge_text)
        badge_html = (
            f'<div class="page-header-badge" style="background:{bg};color:{color};'
            f'border:1px solid {border};">{safe_badge}</div>'
        )
    st.markdown(
        f"""
        <div class="page-header">
          <div>
            <h2 class="page-header-title">{safe_title}</h2>
            <p class="page-header-subtitle">{safe_subtitle}</p>
          </div>
          {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_highlight_panel(
    title: str,
    body: str,
    *,
    variant: str = "indigo",
    icon: str = "✦",
) -> None:
    bg, color, border = PANEL_VARIANTS.get(variant, PANEL_VARIANTS["indigo"])
    safe_title = html.escape(title)
    safe_body = html.escape(body)
    safe_icon = html.escape(icon)
    st.markdown(
        f"""
        <div class="highlight-panel" style="background:{bg};border-color:{border};">
          <div class="highlight-panel-icon" style="color:{color};background:#ffffff99;">
            {safe_icon}
          </div>
          <div>
            <div class="highlight-panel-title" style="color:{color};">{safe_title}</div>
            <div class="highlight-panel-body">{safe_body}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress_panel(
    *,
    title: str,
    percent: int,
    detail: str,
    variant: str = "indigo",
) -> None:
    color = BADGE_VARIANTS.get(variant, BADGE_VARIANTS["indigo"])[1]
    safe_title = html.escape(title)
    safe_detail = html.escape(detail)
    pct = max(0, min(100, int(percent)))
    st.markdown(
        f"""
        <div class="progress-panel">
          <div class="progress-panel-top">
            <span class="progress-panel-title">{safe_title}</span>
            <span class="progress-panel-pct" style="color:{color};">{pct}%</span>
          </div>
          <div class="progress-panel-track">
            <div class="progress-panel-fill" style="width:{pct}%;background:linear-gradient(
              90deg, {color} 0%, #818cf8 100%);"></div>
          </div>
          <div class="progress-panel-detail">{safe_detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_form_section_header(icon: str, title: str, subtitle: str = "") -> None:
    safe_icon = html.escape(icon)
    safe_title = html.escape(title)
    subtitle_html = (
        f'<div class="form-section-subtitle">{html.escape(subtitle)}</div>' if subtitle else ""
    )
    st.markdown(
        f"""
        <div class="form-section-header">
          <div class="form-section-icon">{safe_icon}</div>
          <div>
            <div class="form-section-title">{safe_title}</div>
            {subtitle_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_step_journey(steps: list[dict[str, Any]]) -> None:
    cards: list[str] = []
    for index, step in enumerate(steps, start=1):
        done = bool(step.get("done"))
        label = html.escape(str(step.get("label", "")))
        hint = html.escape(str(step.get("hint", "")))
        state_class = "step-card-done" if done else "step-card-pending"
        marker = "✓" if done else str(index)
        cards.append(
            f'<div class="step-card {state_class}">'
            f'<div class="step-card-marker">{marker}</div>'
            f'<div class="step-card-label">{label}</div>'
            f'<div class="step-card-hint">{hint}</div></div>'
        )
    st.markdown(f'<div class="step-journey">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_snapshot_grid(items: list[tuple[str, str]]) -> None:
    cells = []
    for label, value in items:
        cells.append(
            f'<div class="snapshot-cell">'
            f'<div class="snapshot-label">{html.escape(label)}</div>'
            f'<div class="snapshot-value">{html.escape(str(value))}</div></div>'
        )
    st.markdown(f'<div class="snapshot-grid">{"".join(cells)}</div>', unsafe_allow_html=True)


def render_career_card(
    *,
    career_name: str,
    match_score: float,
    rationale: str,
    skills: list[str],
    activities: list[str],
) -> None:
    safe_name = html.escape(career_name)
    safe_rationale = html.escape(rationale)
    score_color = "#4338CA"
    chips = ""
    for skill in skills[:4]:
        chips += (
            f'<span class="career-chip" style="background:#EEF2FF;color:#4338CA;">'
            f"{html.escape(skill)}</span>"
        )
    for item in activities[:3]:
        chips += (
            f'<span class="career-chip" style="background:#F0FDF4;color:#047857;">'
            f"{html.escape(item)}</span>"
        )
    st.markdown(
        f"""
        <div class="career-card">
          <div class="career-card-head">
            <div class="career-card-name">{safe_name}</div>
            <div class="career-card-score" style="color:{score_color};">{match_score:.0f}%</div>
          </div>
          <div class="career-card-caption">match score</div>
          <p class="career-card-rationale">{safe_rationale}</p>
          <div class="career-card-chips">{chips or '<span class="career-chip-muted">No tags yet</span>'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

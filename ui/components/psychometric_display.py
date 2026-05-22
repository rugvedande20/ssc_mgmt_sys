from __future__ import annotations

import html
from typing import Any

import streamlit as st

from config.constants import RIASEC_TYPES

RIASEC_META: dict[str, dict[str, str]] = {
    "Realistic": {"icon": "🔧", "color": "#EA580C", "bg": "#FFF7ED", "tag": "Hands-on & practical"},
    "Investigative": {"icon": "🔬", "color": "#2563EB", "bg": "#EFF6FF", "tag": "Curious & analytical"},
    "Artistic": {"icon": "🎨", "color": "#7C3AED", "bg": "#F5F3FF", "tag": "Creative & expressive"},
    "Social": {"icon": "🤝", "color": "#059669", "bg": "#ECFDF5", "tag": "Helping & teamwork"},
    "Enterprising": {"icon": "🚀", "color": "#DC2626", "bg": "#FEF2F2", "tag": "Leadership & ideas"},
    "Conventional": {"icon": "📋", "color": "#475569", "bg": "#F8FAFC", "tag": "Organized & structured"},
}


def render_assessment_invite(*, minutes: int = 12, question_count: int = 30) -> None:
    st.markdown(
        f"""
        <div class="assess-invite">
          <div class="assess-invite-glow"></div>
          <div class="assess-invite-content">
            <div class="assess-invite-badge">✨ Discover your interests</div>
            <h3 class="assess-invite-title">Ready to find what excites you?</h3>
            <p class="assess-invite-body">
              A fun, quick quiz across 6 interest areas — about {minutes} minutes,
              {question_count} statements, no right or wrong answers.
            </p>
            <div class="assess-invite-perks">
              <span class="assess-perk">🎯 Personal interest profile</span>
              <span class="assess-perk">📊 Visual results chart</span>
              <span class="assess-perk">💡 Unlocks career ideas</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_riasec_trail(current_step: int) -> None:
    chips: list[str] = []
    for index, category in enumerate(RIASEC_TYPES):
        meta = RIASEC_META[category]
        state = "done" if index < current_step else ("active" if index == current_step else "upcoming")
        safe_cat = html.escape(category)
        chips.append(
            f'<div class="riasec-chip riasec-{state}" style="--chip-color:{meta["color"]};'
            f'--chip-bg:{meta["bg"]};">'
            f'<span class="riasec-chip-icon">{meta["icon"]}</span>'
            f'<span class="riasec-chip-label">{safe_cat}</span></div>'
        )
    st.markdown(f'<div class="riasec-trail">{"".join(chips)}</div>', unsafe_allow_html=True)


def render_section_hero(category: str, step: int, total_sections: int, question_count: int) -> None:
    meta = RIASEC_META.get(category, {"icon": "✦", "color": "#4338CA", "bg": "#EEF2FF", "tag": ""})
    safe_cat = html.escape(category)
    safe_tag = html.escape(meta["tag"])
    st.markdown(
        f"""
        <div class="assess-section-hero" style="--section-color:{meta['color']};--section-bg:{meta['bg']};">
          <div class="assess-section-step">Section {step} of {total_sections}</div>
          <div class="assess-section-head">
            <span class="assess-section-icon">{meta['icon']}</span>
            <div>
              <div class="assess-section-title">{safe_cat}</div>
              <div class="assess-section-tag">{safe_tag}</div>
            </div>
          </div>
          <div class="assess-section-meta">{question_count} quick statements · pick what feels most like you</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_likert_legend() -> None:
    st.markdown(
        """
        <div class="likert-legend">
          <span class="likert-legend-label">Scale:</span>
          <span class="likert-pill">1 Strongly disagree</span>
          <span class="likert-pill">3 Neutral</span>
          <span class="likert-pill">5 Strongly agree</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

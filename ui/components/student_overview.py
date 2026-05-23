from __future__ import annotations

from typing import Any

import streamlit as st

from config.school_context import ACADEMIC_FIELD_LABELS, PROFILE_FIELD_LABELS, format_class
from ui.components.activity_meta import render_activity_caption
from ui.components.risk_display import format_display_value, render_factor_list, risk_level_badge


def _field_rows(items: list[tuple[str, Any]]) -> None:
    for label, value in items:
        col_label, col_value = st.columns((1.1, 2))
        col_label.markdown(f"**{label}**")
        col_value.write(format_display_value(value))


def render_profile_tab(profile: dict[str, Any] | None) -> None:
    if not profile:
        st.info("No profile saved yet. The student can complete this under **Profile** (student login).")
        return

    st.caption("School and background details")

    col_a, col_b = st.columns(2)
    with col_a:
        _field_rows(
            [
                (PROFILE_FIELD_LABELS["department"], profile.get("department")),
                (PROFILE_FIELD_LABELS["semester"], format_class(profile.get("semester"))),
                ("Age", profile.get("age")),
                ("Gender", profile.get("gender")),
                (PROFILE_FIELD_LABELS["family_income_band"], profile.get("family_income_band")),
            ]
        )
    with col_b:
        _field_rows(
            [
                (PROFILE_FIELD_LABELS["parental_education"], profile.get("parental_education")),
                (PROFILE_FIELD_LABELS["travel_distance_km"], profile.get("travel_distance_km")),
                (PROFILE_FIELD_LABELS["internet_access"], profile.get("internet_access")),
            ]
        )

    if profile.get("updated_at"):
        render_activity_caption(
            at=profile.get("updated_at"),
            at_label="Profile updated",
            by=profile.get("activity_by"),
        )

    st.markdown("**Interests and strengths**")
    int_col, str_col = st.columns(2)
    with int_col:
        with st.container(border=True):
            st.caption(PROFILE_FIELD_LABELS["interests_summary"])
            st.write(format_display_value(profile.get("interests_summary")))
    with str_col:
        with st.container(border=True):
            st.caption(PROFILE_FIELD_LABELS["strengths_summary"])
            st.write(format_display_value(profile.get("strengths_summary")))


def render_academic_tab(academic: dict[str, Any] | None) -> None:
    if not academic:
        st.info("No academic records yet. Add data under **Academic Data Upload**.")
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Attendance", f"{academic.get('attendance_percentage', '—')}%")
    m2.metric("Overall marks", f"{academic.get('overall_marks_pct', '—')}%")
    m3.metric("Term test", f"{academic.get('latest_term_score_pct', '—')}%")
    m4.metric("Below passing", academic.get("subjects_below_passing", "—"))

    m5, m6, m7 = st.columns(3)
    m5.metric(
        ACADEMIC_FIELD_LABELS["engagement_score"].replace(" (1–10)", ""),
        academic.get("engagement_score", "—"),
    )
    m6.metric(
        ACADEMIC_FIELD_LABELS["stress_level"].replace(" (1–10)", ""),
        academic.get("stress_level", "—"),
    )
    m7.metric("Last updated", academic.get("recorded_at", "—"))
    render_activity_caption(by=academic.get("activity_by"))


def render_risk_tab(prediction: dict[str, Any] | None) -> None:
    if not prediction:
        st.info("No dropout prediction yet. Train the model and run predictions on **Dropout Analysis**.")
        return

    level = prediction.get("risk_level", "—")
    c1, c2, c3 = st.columns(3)
    c1.metric("Risk score", f"{prediction.get('risk_score', '—')}%")
    with c2:
        st.markdown("**Risk level**")
        st.markdown(risk_level_badge(str(level)), unsafe_allow_html=True)
    c3.metric("Predicted at", prediction.get("predicted_at", "—"))
    render_activity_caption(by=prediction.get("activity_by"))

    with st.container(border=True):
        st.markdown("**Why this rating?**")
        render_factor_list(str(prediction.get("top_factors", "")))


def render_psychometric_tab(psych: dict[str, Any] | None) -> None:
    if not psych:
        st.info("Student has not completed the **Interest Assessment** yet.")
        return

    with st.container(border=True):
        st.markdown("**Assessment summary**")
        st.write(psych.get("summary") or "—")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Top interest codes**")
        codes = psych.get("top_codes") or "—"
        if codes and codes != "—":
            for code in str(codes).split(","):
                code = code.strip()
                if code:
                    st.markdown(f"`{code}`")
        else:
            st.write("—")
    with col2:
        st.metric("Submitted", psych.get("submitted_at", "—"))
        render_activity_caption(by=psych.get("activity_by"))

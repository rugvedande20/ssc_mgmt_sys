from __future__ import annotations

import html
from typing import Any

import streamlit as st

from ui.components.activity_meta import render_activity_caption
from ui.components.risk_display import format_display_value, render_factor_list, risk_level_badge
from ui.components.tables import show_dataframe

LEVEL_STYLES: dict[str, tuple[str, str, str]] = {
    "Low": ("#F0FDF4", "#15803D", "#86EFAC"),
    "Medium": ("#FFF7ED", "#C2410C", "#FDBA74"),
    "High": ("#FEE2E2", "#B91C1C", "#FCA5A5"),
}

RISK_INTERVENTION_GUIDANCE: dict[str, dict[str, str]] = {
    "High": {
        "title": "Priority one-on-one support",
        "summary": (
            "This student needs immediate individualized counseling. Schedule weekly one-on-one sessions, "
            "coordinate with parents, and track attendance and engagement closely."
        ),
        "cadence": "Weekly 1:1 sessions recommended",
        "focus": "Crisis prevention, attendance recovery, stress reduction",
    },
    "Medium": {
        "title": "Proactive guidance check-ins",
        "summary": (
            "Moderate risk indicators suggest regular counseling touchpoints. Use structured modules "
            "and monitor whether risk factors improve after each session."
        ),
        "cadence": "Bi-weekly check-ins recommended",
        "focus": "Skill building, engagement, early problem solving",
    },
    "Low": {
        "title": "Wellness monitoring",
        "summary": (
            "Risk is currently low. Maintain an open door for support, offer optional group or "
            "career modules, and re-assess if academic or personal circumstances change."
        ),
        "cadence": "Monthly wellness touchpoint or as needed",
        "focus": "Preventive support, strengths-based coaching",
    },
}

STUDENT_SUPPORT_GUIDANCE: dict[str, dict[str, str]] = {
    "High": {
        "title": "Personalized support plan",
        "message": (
            "Your school team has set up focused one-on-one support for you. "
            "Attend your scheduled sessions and reach out if you need help between meetings."
        ),
        "badge_level": "High",
    },
    "Medium": {
        "title": "Guidance check-ins",
        "message": (
            "Your counselor may schedule periodic check-ins to help you stay on track. "
            "These sessions are meant to support your goals, not to judge you."
        ),
        "badge_level": "Medium",
    },
    "Low": {
        "title": "You're on track",
        "message": (
            "Based on your latest school review, no urgent intervention is needed right now. "
            "Support sessions remain available whenever you want extra guidance."
        ),
        "badge_level": "Low",
    },
}


def level_badge(label: str, level: str) -> str:
    safe_label = html.escape(label)
    safe_level = html.escape(level or "—")
    bg, text, border = LEVEL_STYLES.get(level, ("#F1F5F9", "#475569", "#CBD5E1"))
    return (
        f'<span style="display:inline-block;background:{bg};color:{text};'
        f'border:1px solid {border};padding:0.2rem 0.55rem;border-radius:999px;'
        f'font-weight:700;font-size:0.68rem;letter-spacing:0.03em;">'
        f"{safe_label.upper()}: {safe_level.upper()}</span>"
    )


def render_risk_intervention_context(prediction: dict[str, Any] | None, *, student_view: bool = False) -> None:
    if not prediction:
        st.info(
            "No admin risk analysis yet. Run predictions on **Dropout Analysis** before planning interventions."
            if not student_view
            else "Your support plan will appear here after your school completes a risk review."
        )
        return

    level = str(prediction.get("risk_level", "—"))
    guidance = (
        STUDENT_SUPPORT_GUIDANCE.get(level, STUDENT_SUPPORT_GUIDANCE["Low"])
        if student_view
        else RISK_INTERVENTION_GUIDANCE.get(level, RISK_INTERVENTION_GUIDANCE["Low"])
    )

    with st.container(border=True):
        c1, c2 = st.columns((1.4, 1))
        with c1:
            st.markdown(f"**{guidance['title']}**")
            st.write(guidance["message"] if student_view else guidance["summary"])
        with c2:
            if student_view:
                badge_level = guidance.get("badge_level", "Low")
                st.markdown(level_badge("Support tier", badge_level), unsafe_allow_html=True)
            else:
                st.markdown("**Admin risk analysis**")
                st.markdown(risk_level_badge(level), unsafe_allow_html=True)
                st.metric("Risk score", f"{prediction.get('risk_score', '—')}%")

        if not student_view:
            st.caption(f"Recommended cadence: **{guidance['cadence']}** · Focus: **{guidance['focus']}**")
            with st.expander("Risk factors from latest analysis"):
                render_factor_list(str(prediction.get("top_factors", "")))


def render_intervention_metrics(interventions: list[dict[str, Any]]) -> None:
    scheduled = sum(1 for row in interventions if row.get("status") == "scheduled")
    completed = sum(1 for row in interventions if row.get("status") == "completed")
    high_priority = sum(1 for row in interventions if row.get("priority") == "High")
    c1, c2, c3 = st.columns(3)
    c1.metric("Scheduled", scheduled)
    c2.metric("Completed", completed)
    c3.metric("High priority", high_priority)


def _intervention_table_rows(rows: list[dict[str, Any]], *, include_student: bool = False) -> list[dict[str, Any]]:
    table_rows = []
    for row in rows:
        entry = {
            "intervention_type": row.get("intervention_type"),
            "module": row.get("module") or "—",
            "priority": row.get("priority"),
            "intensity": row.get("intensity"),
            "status": row.get("status"),
            "scheduled_at": row.get("scheduled_at") or "—",
            "completed_at": row.get("completed_at") or "—",
            "action_taken": row.get("action_taken"),
            "activity_by": row.get("activity_by"),
        }
        if include_student:
            entry = {"student_name": row.get("student_name"), **entry}
        table_rows.append(entry)
    return table_rows


def render_intervention_history_table(
    rows: list[dict[str, Any]],
    *,
    include_student: bool = False,
    empty_message: str = "No intervention records yet.",
) -> None:
    if not rows:
        st.info(empty_message)
        return
    columns = (
        [
            "student_name",
            "intervention_type",
            "module",
            "priority",
            "intensity",
            "status",
            "scheduled_at",
            "action_taken",
            "activity_by",
        ]
        if include_student
        else [
            "intervention_type",
            "module",
            "priority",
            "intensity",
            "status",
            "scheduled_at",
            "completed_at",
            "action_taken",
            "activity_by",
        ]
    )
    show_dataframe(_intervention_table_rows(rows, include_student=include_student), columns=columns)


def render_interventions_tab(
    overview: dict[str, Any],
    interventions: list[dict[str, Any]],
    *,
    current_user: dict,
    key_prefix: str,
) -> None:
    from src.db.database import get_db_session
    from src.services.intervention_service import create_intervention_log, schedule_intervention

    prediction = overview.get("latest_prediction")
    render_risk_intervention_context(prediction, student_view=False)

    if prediction:
        suggested = overview.get("intervention_suggested") or {}
        p_col, i_col = st.columns(2)
        with p_col:
            st.markdown(
                level_badge("Suggested priority", suggested.get("priority", "Medium")),
                unsafe_allow_html=True,
            )
        with i_col:
            st.markdown(
                level_badge("Suggested intensity", suggested.get("intensity", "Medium")),
                unsafe_allow_html=True,
            )

    render_intervention_metrics(interventions)

    scheduled = [row for row in interventions if row.get("status") == "scheduled"]
    if scheduled:
        st.markdown("**Upcoming scheduled sessions**")
        render_intervention_history_table(scheduled, empty_message="")

    st.markdown("**Record history**")
    completed = [row for row in interventions if row.get("status") == "completed"]
    render_intervention_history_table(completed, empty_message="No completed interventions logged yet.")

    with st.expander("Log or schedule intervention for this student"):
        action = st.radio(
            "Action",
            ["Log completed session", "Schedule session"],
            horizontal=True,
            key=f"{key_prefix}_action",
        )
        with st.form(f"{key_prefix}_intervention_form"):
            from config.constants import INTERVENTION_MODULES, INTERVENTION_PRIORITIES, INTERVENTION_TYPES

            col1, col2 = st.columns(2)
            intervention_type = col1.selectbox("Type", INTERVENTION_TYPES)
            module = col2.selectbox("Module", ["—"] + list(INTERVENTION_MODULES))
            module_value = None if module == "—" else module

            defaults = overview.get("intervention_suggested") or {"priority": "Medium", "intensity": "Medium"}
            priority = col1.selectbox(
                "Priority",
                INTERVENTION_PRIORITIES,
                index=INTERVENTION_PRIORITIES.index(defaults["priority"]),
            )
            intensity = col2.selectbox(
                "Intensity",
                INTERVENTION_PRIORITIES,
                index=INTERVENTION_PRIORITIES.index(defaults["intensity"]),
            )

            if action == "Schedule session":
                scheduled_date = st.date_input("Session date")
                scheduled_time = st.time_input("Session time")
                note = st.text_area("Scheduling notes (optional)", placeholder="Reason, location, or prep notes…")
                submitted = st.form_submit_button("Schedule session", use_container_width=True)
                if submitted:
                    from datetime import datetime

                    scheduled_at = datetime.combine(scheduled_date, scheduled_time)
                    try:
                        with get_db_session() as session:
                            schedule_intervention(
                                session,
                                student_id=overview["id"],
                                admin_user_id=current_user["id"],
                                scheduled_at=scheduled_at,
                                intervention_type=intervention_type,
                                module=module_value,
                                priority=priority,
                                intensity=intensity,
                                note=note,
                            )
                        st.success("Session scheduled.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            else:
                action_taken = st.text_input("Action taken", placeholder="e.g. 45-min counseling session")
                note = st.text_area("Session notes", placeholder="Observations, agreements, follow-up plan…")
                submitted = st.form_submit_button("Save intervention record", use_container_width=True)
                if submitted:
                    if not action_taken.strip() or not note.strip():
                        st.error("Action taken and session notes are required.")
                    else:
                        try:
                            with get_db_session() as session:
                                create_intervention_log(
                                    session,
                                    student_id=overview["id"],
                                    admin_user_id=current_user["id"],
                                    note=note,
                                    action_taken=action_taken,
                                    intervention_type=intervention_type,
                                    module=module_value,
                                    priority=priority,
                                    intensity=intensity,
                                )
                            st.success("Intervention record saved.")
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))


def render_student_interventions_page(payload: dict[str, Any]) -> None:
    prediction = payload.get("latest_prediction")
    render_risk_intervention_context(prediction, student_view=True)

    scheduled = payload.get("scheduled") or []
    completed = payload.get("completed") or []

    m1, m2 = st.columns(2)
    m1.metric("Upcoming sessions", len(scheduled))
    m2.metric("Completed sessions", len(completed))

    if scheduled:
        with st.container(border=True):
            st.markdown("**Your upcoming sessions**")
            for row in scheduled:
                st.markdown(
                    f"- **{format_display_value(row.get('intervention_type'))}**"
                    f" · {format_display_value(row.get('module'))}"
                    f" · scheduled **{format_display_value(row.get('scheduled_at'))}**"
                )
                render_activity_caption(by=row.get("activity_by"))
    else:
        st.info("No upcoming sessions scheduled. Your counselor will add them here when needed.")

    if completed:
        with st.container(border=True):
            st.markdown("**Past support sessions**")
            for row in completed:
                st.markdown(
                    f"**{format_display_value(row.get('intervention_type'))}** — "
                    f"{format_display_value(row.get('action_taken'))}"
                )
                st.caption(format_display_value(row.get("module")))
                if row.get("completed_at"):
                    render_activity_caption(
                        at=row["completed_at"],
                        at_label="Completed",
                        by=row.get("activity_by"),
                    )

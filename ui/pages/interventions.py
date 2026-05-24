import streamlit as st

from config.constants import INTERVENTION_MODULES, INTERVENTION_PRIORITIES, INTERVENTION_TYPES
from src.db.database import get_db_session
from src.services.intervention_service import (
    cancel_intervention,
    complete_scheduled_intervention,
    create_intervention_log,
    get_intervention_summary_for_scope,
    list_at_risk_students_for_intervention,
    list_interventions_for_scope,
    schedule_intervention,
    suggested_priority_intensity,
)
from src.utils.admin_context import admin_page_subtitle, assigned_grade_for_user, grade_scope_label, student_scope_for_user
from ui.components.intervention_display import (
    level_badge,
    render_intervention_history_table,
    render_risk_intervention_context,
)
from ui.components.layout import section
from ui.components.page_chrome import render_page_header
from ui.components.risk_display import risk_level_badge
from ui.components.tables import show_dataframe


def render(current_user: dict) -> None:
    grade_label = grade_scope_label(current_user)
    title = f"Class {assigned_grade_for_user(current_user)} Interventions" if grade_label else "Interventions"
    render_page_header(
        title,
        admin_page_subtitle(
            "One-on-one counseling and intervention records for at-risk students. "
            "High-risk learners are the primary focus.",
            current_user,
        ),
        badge_text="Admin",
        badge_variant="indigo",
    )

    scope = student_scope_for_user(current_user)
    preselected_student_id = st.session_state.pop("intervention_student_id", None)

    with get_db_session() as session:
        summary = get_intervention_summary_for_scope(session, **scope)
        at_risk = list_at_risk_students_for_intervention(session, **scope, risk_levels=("High", "Medium"))
        high_risk = [row for row in at_risk if row.get("risk_level") == "High"]
        all_interventions = list_interventions_for_scope(session, **scope, limit=200)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("High-risk students", len(high_risk))
    m2.metric("Scheduled sessions", summary["scheduled"])
    m3.metric("Completed records", summary["completed"])
    m4.metric("At-risk (High + Medium)", len(at_risk))

    with section(
        "Primary focus — high-risk students",
        "Students flagged for immediate one-on-one intervention and counseling.",
    ):
        if not high_risk:
            st.info("No high-risk students in scope. Run predictions on Dropout Analysis after uploading academic data.")
        else:
            show_dataframe(
                [
                    {
                        "student_name": row["student_name"],
                        "risk_score": row["risk_score"],
                        "risk_level": row["risk_level"],
                        "suggested_priority": row["suggested_priority"],
                        "suggested_intensity": row["suggested_intensity"],
                        "scheduled_count": row["scheduled_count"],
                        "completed_count": row["completed_count"],
                    }
                    for row in high_risk
                ],
                columns=[
                    "student_name",
                    "risk_score",
                    "risk_level",
                    "suggested_priority",
                    "suggested_intensity",
                    "scheduled_count",
                    "completed_count",
                ],
            )

            pick_labels = {f"{row['student_name']} ({row['username']})": row["student_id"] for row in high_risk}
            default_label = next(
                (label for label, sid in pick_labels.items() if sid == preselected_student_id),
                list(pick_labels.keys())[0],
            )
            selected_label = st.selectbox(
                "Quick view — high-risk student",
                list(pick_labels.keys()),
                index=list(pick_labels.keys()).index(default_label),
            )
            selected = next(row for row in high_risk if row["student_id"] == pick_labels[selected_label])
            render_risk_intervention_context(
                {
                    "risk_level": selected["risk_level"],
                    "risk_score": selected["risk_score"],
                    "top_factors": selected["top_factors"],
                }
            )
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(
                    level_badge("Priority", selected["suggested_priority"]),
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    level_badge("Intensity", selected["suggested_intensity"]),
                    unsafe_allow_html=True,
                )

    with section("Schedule or log intervention", "Create records and modules for any student in your cohort."):
        student_options = {f"{row['student_name']} ({row['username']})": row["student_id"] for row in at_risk}
        if not student_options:
            with get_db_session() as session:
                from src.services.dropout_service import list_latest_predictions_per_student

                predictions = list_latest_predictions_per_student(session, limit=100, **scope)
            student_options = {
                f"{row['student_name']} ({row['username']})": row["student_id"] for row in predictions
            }

        if not student_options:
            st.info("No students with risk scores yet. Upload data and run dropout predictions first.")
        else:
            default_idx = 0
            if preselected_student_id and preselected_student_id in student_options.values():
                default_idx = list(student_options.values()).index(preselected_student_id)

            student_label = st.selectbox(
                "Student",
                list(student_options.keys()),
                index=default_idx,
                key="interventions_student_pick",
            )
            student_id = student_options[student_label]
            selected_prediction = next(
                (row for row in at_risk if row["student_id"] == student_id),
                None,
            )
            defaults = (
                suggested_priority_intensity(selected_prediction["risk_level"])
                if selected_prediction
                else {"priority": "Medium", "intensity": "Medium"}
            )

            if selected_prediction:
                st.markdown(
                    risk_level_badge(str(selected_prediction["risk_level"])),
                    unsafe_allow_html=True,
                )

            action = st.radio(
                "Action",
                ["Schedule one-on-one session", "Log completed session"],
                horizontal=True,
                key="interventions_action",
            )

            with st.form("interventions_main_form"):
                col1, col2 = st.columns(2)
                intervention_type = col1.selectbox("Intervention type", INTERVENTION_TYPES)
                module = col2.selectbox("Counseling module", ["—"] + list(INTERVENTION_MODULES))
                module_value = None if module == "—" else module
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

                if action == "Schedule one-on-one session":
                    scheduled_date = st.date_input("Session date")
                    scheduled_time = st.time_input("Session time")
                    note = st.text_area("Scheduling notes (optional)")
                    submitted = st.form_submit_button("Schedule session", use_container_width=True)
                    if submitted:
                        from datetime import datetime

                        try:
                            with get_db_session() as session:
                                schedule_intervention(
                                    session,
                                    student_id=student_id,
                                    admin_user_id=current_user["id"],
                                    scheduled_at=datetime.combine(scheduled_date, scheduled_time),
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
                    action_taken = st.text_input("Action taken")
                    note = st.text_area("Session notes")
                    submitted = st.form_submit_button("Save intervention record", use_container_width=True)
                    if submitted:
                        if not action_taken.strip() or not note.strip():
                            st.error("Action taken and session notes are required.")
                        else:
                            try:
                                with get_db_session() as session:
                                    create_intervention_log(
                                        session,
                                        student_id=student_id,
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

    with section("Intervention records", "All scheduled and completed interventions in your cohort."):
        scheduled_rows = [row for row in all_interventions if row.get("status") == "scheduled"]
        if scheduled_rows:
            st.markdown("**Manage scheduled sessions**")
            for row in scheduled_rows:
                with st.container(border=True):
                    st.markdown(
                        f"**{row['student_name']}** · {row.get('intervention_type')} · "
                        f"{row.get('module') or 'General'} · **{row.get('scheduled_at')}**"
                    )
                    st.caption(
                        f"Priority: {row.get('priority')} · Intensity: {row.get('intensity')} · "
                        f"Risk at scheduling: {row.get('risk_level_at_time') or '—'}"
                    )
                    with st.form(f"complete_sched_{row['id']}"):
                        action_taken = st.text_input("Action taken", key=f"action_{row['id']}")
                        note = st.text_area("Session notes", key=f"note_{row['id']}")
                        c1, c2 = st.columns(2)
                        complete = c1.form_submit_button("Mark completed", use_container_width=True)
                        cancel = c2.form_submit_button("Cancel session", use_container_width=True)
                        if complete:
                            if not action_taken.strip() or not note.strip():
                                st.error("Action taken and session notes are required.")
                            else:
                                try:
                                    with get_db_session() as session:
                                        complete_scheduled_intervention(
                                            session,
                                            row["id"],
                                            note=note,
                                            action_taken=action_taken,
                                        )
                                    st.success("Session marked completed.")
                                    st.rerun()
                                except ValueError as exc:
                                    st.error(str(exc))
                        if cancel:
                            try:
                                with get_db_session() as session:
                                    cancel_intervention(session, row["id"])
                                st.warning("Session cancelled.")
                                st.rerun()
                            except ValueError as exc:
                                st.error(str(exc))

        render_intervention_history_table(all_interventions, include_student=True)

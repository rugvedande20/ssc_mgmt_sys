import pandas as pd
import plotly.express as px
import streamlit as st

from config.constants import RIASEC_TYPES
from src.db.database import get_db_session
from src.psychometric.questions import LIKERT_OPTIONS
from src.services.psychometric_service import (
    get_latest_attempt_payload,
    get_question_bank,
    list_recent_attempts,
    save_psychometric_attempt,
)
from ui.components.layout import section, show_plotly_chart
from ui.components.page_chrome import render_highlight_panel, render_page_header
from ui.components.tables import show_dataframe


def _init_psychometric_state() -> None:
    st.session_state.setdefault("psychometric_step", 0)
    st.session_state.setdefault("psychometric_responses", {})


def _reset_psychometric_state() -> None:
    st.session_state.psychometric_step = 0
    st.session_state.psychometric_responses = {}


def _render_assessment_flow(student_id: int) -> None:
    _init_psychometric_state()
    question_bank = get_question_bank()
    categories = list(RIASEC_TYPES)
    step = st.session_state.psychometric_step
    category = categories[step]
    section_questions = [question for question in question_bank if question["category"] == category]
    total_questions = len(question_bank)
    answered_count = len(st.session_state.psychometric_responses)

    st.progress(
        (step + 1) / len(categories),
        text=f"Section {step + 1} of {len(categories)}: {category}",
    )
    st.caption(f"Progress: {answered_count} of {total_questions} questions saved across all sections.")

    with st.form(f"psychometric_section_{step}"):
        st.markdown(f"### {category}")
        st.caption("Rate how much each statement describes you.")
        section_responses: dict[str, int] = {}
        for question in section_questions:
            current_value = st.session_state.psychometric_responses.get(question["id"])
            default_index = (current_value - 1) if current_value else 2
            section_responses[question["id"]] = st.radio(
                question["text"],
                options=list(range(1, 6)),
                index=default_index,
                format_func=lambda value: LIKERT_OPTIONS[value],
                horizontal=True,
                key=f"psych_{question['id']}_{step}",
            )

        nav_prev, nav_next, nav_reset = st.columns((1, 1.2, 1))
        previous_clicked = nav_prev.form_submit_button("← Previous", disabled=step == 0)
        next_label = "Next →" if step < len(categories) - 1 else "Submit Assessment"
        next_clicked = nav_next.form_submit_button(next_label, use_container_width=True)
        reset_clicked = nav_reset.form_submit_button("Reset")

    if reset_clicked:
        _reset_psychometric_state()
        st.rerun()

    if previous_clicked and step > 0:
        st.session_state.psychometric_responses.update(section_responses)
        st.session_state.psychometric_step -= 1
        st.rerun()

    if next_clicked:
        st.session_state.psychometric_responses.update(section_responses)
        if step < len(categories) - 1:
            st.session_state.psychometric_step += 1
            st.rerun()

        if len(st.session_state.psychometric_responses) < total_questions:
            st.error("Please complete every section before submitting.")
            return

        with get_db_session() as session:
            save_psychometric_attempt(session, student_id, st.session_state.psychometric_responses)
        _reset_psychometric_state()
        st.success("Psychometric assessment submitted successfully.")
        st.rerun()


def render(current_user: dict) -> None:
    from src.services.student_service import get_student_profile_payload
    from src.utils.helpers import is_student_profile_complete

    with get_db_session() as session:
        profile = get_student_profile_payload(session, current_user["id"])
    if not is_student_profile_complete(profile):
        render_page_header(
            "Interest & Strength Assessment",
            "Complete your school profile first to unlock this assessment.",
            badge_text="Locked",
            badge_variant="amber",
        )
        render_highlight_panel(
            "Profile required",
            "Open **Complete Profile** from the menu, then return here.",
            variant="amber",
            icon="!",
        )
        return

    render_page_header(
        "Interest & Strength Assessment",
        "A short RIASEC-style questionnaire — discover subjects and activities you enjoy (Class 6–10).",
        badge_text="RIASEC",
        badge_variant="violet",
    )

    with get_db_session() as session:
        latest_attempt = get_latest_attempt_payload(session, current_user["id"])
        recent_attempts = list_recent_attempts(session, current_user["id"], limit=5)

    latest_scores = latest_attempt["score_map"] if latest_attempt else {}
    if latest_attempt:
        with section("Your latest results", "Saved assessment summary and interest chart."):
            render_highlight_panel(
                "Assessment complete",
                latest_attempt["summary"],
                variant="emerald",
                icon="✓",
            )
            st.caption(f"Last taken: {latest_attempt['submitted_at']} · Top codes: {latest_attempt['top_codes']}")
            if latest_scores:
                chart_df = pd.DataFrame(
                    [{"Category": category, "Score": score} for category, score in latest_scores.items()]
                ).sort_values("Score", ascending=False)
                chart = px.bar(chart_df, x="Category", y="Score", color="Category", title="Your Interest Profile")
                show_plotly_chart(chart, key="psychometric_interest_chart")

    with section(
        "Take or retake the assessment",
        "Six short sections — rate how much each statement describes you.",
    ):
        with st.expander("Open questionnaire", expanded=not latest_attempt):
            _render_assessment_flow(current_user["id"])

    with section("Recent attempts", "Your last five submissions."):
        if recent_attempts:
            show_dataframe(recent_attempts)
        else:
            st.info("No assessment attempts found yet.")

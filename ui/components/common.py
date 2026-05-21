import streamlit as st

from src.utils.helpers import get_missing_profile_fields, is_student_profile_complete, profile_completeness_percent
from ui.components.page_chrome import render_progress_panel, render_step_journey


def render_empty_state(message: str, *, icon: str = "ℹ️") -> None:
    st.info(f"{icon} {message}")


def render_profile_completeness(profile: dict | None, *, title: str = "Profile completeness") -> int:
    percent = profile_completeness_percent(profile)
    missing = get_missing_profile_fields(profile)
    if missing:
        detail = "Still needed: " + ", ".join(missing[:6])
        if len(missing) > 6:
            detail += f" (+{len(missing) - 6} more)"
    elif percent >= 100:
        detail = "All required fields are complete."
    else:
        detail = "Fill in the remaining sections below."
    render_progress_panel(title=title, percent=percent, detail=detail, variant="indigo" if percent < 100 else "emerald")
    return percent


def render_student_next_steps(
    *,
    assessment_done: bool,
    has_recommendations: bool,
    profile_complete: bool | None = None,
    profile: dict | None = None,
) -> None:
    if profile_complete is None:
        profile_complete = is_student_profile_complete(profile)
    render_step_journey(
        [
            {
                "label": "School profile",
                "hint": "Done" if profile_complete else "Required first",
                "done": profile_complete,
            },
            {
                "label": "Interest assessment",
                "hint": "Completed" if assessment_done else "Up next",
                "done": assessment_done,
            },
            {
                "label": "Career ideas",
                "hint": "Unlocked" if has_recommendations else "After assessment",
                "done": has_recommendations,
            },
        ]
    )

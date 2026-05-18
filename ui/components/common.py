import streamlit as st

from src.utils.helpers import profile_completeness_percent


def render_empty_state(message: str, *, icon: str = "ℹ️") -> None:
    st.info(f"{icon} {message}")


def render_profile_completeness(profile: dict | None) -> int:
    percent = profile_completeness_percent(profile)
    st.progress(percent / 100, text=f"Profile completeness: {percent}%")
    return percent


def render_student_next_steps(
    *,
    profile_complete: bool,
    assessment_done: bool,
    has_recommendations: bool,
) -> None:
    steps = [
        ("Complete your school profile", profile_complete),
        ("Take the interest assessment", assessment_done),
        ("Explore career ideas", has_recommendations),
    ]
    st.subheader("Your Next Steps")
    for label, done in steps:
        marker = "✅" if done else "⬜"
        st.markdown(f"{marker} {label}")

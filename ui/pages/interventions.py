import streamlit as st

from ui.components.page_chrome import render_page_header


def render(current_user: dict | None = None) -> None:
    render_page_header(
        "Interventions",
        "Log counseling notes and track actions taken for at-risk students.",
        badge_text="Admin",
        badge_variant="indigo",
    )

    st.info(
        "Intervention logging is planned for a later milestone. "
        "Use **Student Management → Student Overview** and **Dropout Analysis** to review risk and student context today."
    )

    st.subheader("Planned capabilities")
    st.markdown(
        """
        - Record counseling sessions and follow-up actions
        - Link interventions to dropout risk level and top factors
        - View intervention history per student
        - Export intervention reports for institutional review
        """
    )

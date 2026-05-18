import streamlit as st


def render() -> None:
    st.title("Interventions")
    st.caption("Log counseling notes and track actions taken for at-risk students.")

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

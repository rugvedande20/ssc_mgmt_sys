import streamlit as st

from config.constants import TARGET_GRADE_MAX, TARGET_GRADE_MIN
from config.school_context import FUTURE_SCOPE_NOTE, GRADE_LABELS, PROFILE_FIELD_LABELS
from src.db.database import get_db_session
from src.services.career_recommendation_service import get_student_career_payload
from src.services.student_service import create_student_user, get_student_overview, list_students
from src.utils.admin_context import (
    admin_page_subtitle,
    assigned_grade_for_user,
    grade_default_index,
    grade_scope_label,
    student_scope_for_user,
)
from src.utils.helpers import profile_completeness_percent, parse_json_list
from ui.components.activity_meta import render_activity_caption
from ui.components.layout import section
from ui.components.risk_display import risk_level_badge
from ui.components.page_chrome import render_career_card, render_highlight_panel, render_page_header
from ui.components.student_overview import (
    render_academic_tab,
    render_profile_tab,
    render_psychometric_tab,
    render_risk_tab,
)
from ui.components.tables import show_dataframe


def _render_career_guidance_tab(student_id: int, overview: dict) -> None:
    with get_db_session() as session:
        payload = get_student_career_payload(session, student_id)

    snapshot = payload.get("snapshot")
    if not snapshot:
        st.info(
            f"The student hasn't generated their career guidance report yet. "
            f"Please follow up on **{overview['full_name']}**."
        )
        return

    render_highlight_panel(
        "Latest guidance",
        snapshot["summary"],
        variant="violet",
        icon="◆",
    )
    render_activity_caption(
        at=snapshot["generated_at"],
        at_label="Generated",
        by=snapshot.get("activity_by"),
    )
    st.caption(f"Phase: **{snapshot['phase']}**")

    report = snapshot.get("report") or {}
    if snapshot["phase"] == "class_10_report" and report.get("class_10"):
        c10 = report["class_10"]
        st.subheader(c10.get("title", "Class 10 report"))
        st.write(c10.get("summary", ""))
        if c10.get("stream_recommendations"):
            st.markdown("**Stream suggestions after 10th**")
            for item in c10["stream_recommendations"]:
                st.markdown(f"- **{item['stream']}** — {item['reason']}")
        if c10.get("next_steps"):
            st.markdown("**Next steps**")
            for step in c10["next_steps"]:
                st.markdown(f"- {step}")

    if report.get("meta", {}).get("rising_sectors"):
        st.markdown("**Rising sectors (5-year outlook)**")
        for sector in report["meta"]["rising_sectors"]:
            pct = round(float(sector.get("growth_rate", 0)) * 100)
            st.caption(f"{sector['name']} — projected demand ~{pct}%")

    recommendations = payload.get("recommendations") or []
    if recommendations:
        st.markdown("**Top career matches**")
        for rec in recommendations:
            render_career_card(
                career_name=rec["career_name"],
                match_score=rec["match_score"],
                rationale=rec["rationale"],
                skills=parse_json_list(rec["skill_gap"]),
                activities=parse_json_list(rec["certifications"]),
            )

    history = payload.get("history") or []
    if history:
        with st.expander("Guidance history (year-on-year)"):
            show_dataframe(history)


def _render_student_overview(overview: dict, current_user: dict) -> None:
    st.markdown(f"### {overview['full_name']}")
    st.caption(f"@{overview['username']} · {overview['email']}")

    col1, col2, col3, col4 = st.columns(4)
    profile = overview["profile"]
    completeness = profile_completeness_percent(profile)
    col1.metric("Profile", f"{completeness}%")
    col2.metric("Career records", overview["recommendation_count"])
    col3.metric("Guidance runs", overview.get("guidance_history_count", 0))
    with col4:
        st.markdown("**Latest risk**")
        prediction = overview.get("latest_prediction")
        if prediction:
            st.markdown(
                risk_level_badge(str(prediction.get("risk_level", "—"))),
                unsafe_allow_html=True,
            )
        else:
            st.write("—")

    tab_profile, tab_academic, tab_risk, tab_psych, tab_career = st.tabs(
        ["Profile", "Academics", "Dropout risk", "Psychometric", "Career guidance"]
    )

    with tab_profile:
        render_profile_tab(profile)
    with tab_academic:
        render_academic_tab(overview.get("latest_academic"))
    with tab_risk:
        render_risk_tab(overview.get("latest_prediction"))
    with tab_psych:
        render_psychometric_tab(overview.get("latest_psychometric"))
    with tab_career:
        _render_career_guidance_tab(overview["id"], overview)


def render(current_user: dict) -> None:
    grade_label = grade_scope_label(current_user)
    title = f"Class {assigned_grade_for_user(current_user)} Student Management" if grade_label else "Student Management"
    render_page_header(
        title,
        admin_page_subtitle(
            f"Create and review student accounts for Class {TARGET_GRADE_MIN}–{TARGET_GRADE_MAX}. {FUTURE_SCOPE_NOTE}",
            current_user,
        ),
        badge_text="Admin",
        badge_variant="indigo",
    )

    grade_scope = assigned_grade_for_user(current_user)
    scope = student_scope_for_user(current_user)
    grade_options = list(range(TARGET_GRADE_MIN, TARGET_GRADE_MAX + 1))
    grade_labels = [GRADE_LABELS[g] for g in grade_options]
    default_class_index = grade_default_index(current_user, grade_options)

    with section("Create student", "New Class 6–10 login and profile."):
        st.caption(
            "Use this for students skipped during bulk upload when the file has the same exact full name "
            "more than once — only the first matching row in the file is imported automatically."
        )
        with st.form("create_student_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            full_name = col1.text_input("Full name")
            username = col2.text_input("Username")
            email = col1.text_input("Email")
            password = col2.text_input("Temporary password", type="password")
            school_name = col1.text_input(
                PROFILE_FIELD_LABELS["department"],
                placeholder="e.g. City Public School (CBSE)",
            )
            class_label = col2.selectbox(
                PROFILE_FIELD_LABELS["semester"],
                grade_labels,
                index=default_class_index,
                disabled=grade_scope is not None,
            )
            submitted = st.form_submit_button("Create student", use_container_width=True)

        if submitted:
            if not all([full_name.strip(), username.strip(), email.strip(), password]):
                st.error("Full name, username, email, and password are required.")
            else:
                try:
                    selected_grade = grade_scope or grade_options[grade_labels.index(class_label)]
                    with get_db_session() as session:
                        create_student_user(
                            session,
                            username=username,
                            full_name=full_name,
                            email=email,
                            password=password,
                            profile_data={"department": school_name, "semester": int(selected_grade)},
                            created_by_admin_id=current_user["id"],
                        )
                    st.success("Student account created successfully.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    with section("Student directory", "Search and pick a student for the overview below."):
        search_term = st.text_input(
            "Search by name, username, or email",
            placeholder="Search by name, username, or email…",
        )
        with get_db_session() as session:
            students = list_students(session, search_term=search_term, limit=100, **scope)

        if students:
            show_dataframe(students, columns=["full_name", "username", "email", "school", "class"])
        else:
            st.info("No students found for the current search.")
            return

    with section("Student overview", "Profile, academics, risk, psychometric, and career guidance."):
        student_labels = {f"{student['full_name']} ({student['username']})": student["id"] for student in students}
        selected_label = st.selectbox("Select a student", list(student_labels.keys()))
        with get_db_session() as session:
            overview = get_student_overview(session, student_labels[selected_label])

        if overview:
            _render_student_overview(overview, current_user)

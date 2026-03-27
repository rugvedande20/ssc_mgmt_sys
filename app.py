import streamlit as st

from config.settings import settings
from src.auth.guards import get_current_user, init_session_state, logout_user
from src.db.database import Base, get_database_mode, get_engine, get_db_session
from src.db.seed import seed_demo_data
from ui.pages import (
    admin_dashboard,
    career_recommendations,
    data_upload,
    dropout_analysis,
    interventions,
    login,
    profile,
    psychometric_test,
    student_dashboard,
    student_management,
)


st.set_page_config(
    page_title=settings.app_name,
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner=False)
def bootstrap_database() -> bool:
    Base.metadata.create_all(bind=get_engine())
    with get_db_session() as session:
        seed_demo_data(session)
    return True


def render_sidebar(user: dict | None) -> str:
    st.sidebar.title("Navigation")
    if not user:
        return "Login"

    st.sidebar.write(f"Signed in as **{user['full_name']}**")
    st.sidebar.caption(user["role"].title())

    if user["role"] == "admin":
        options = [
            "Dashboard",
            "Student Management",
            "Academic Data Upload",
            "Dropout Analysis",
            "Interventions",
        ]
    else:
        options = [
            "Dashboard",
            "Profile",
            "Psychometric Test",
            "Career Recommendations",
        ]

    selected = st.sidebar.radio("Go to", options, label_visibility="collapsed")

    st.sidebar.divider()
    st.sidebar.caption("Performance notes")
    st.sidebar.caption("- DB engine is cached")
    st.sidebar.caption("- Heavy modules will load lazily")
    st.sidebar.caption("- Dashboards use limited queries")
    database_mode = get_database_mode()
    if database_mode == "memory":
        st.sidebar.warning("Using in-memory database fallback in this environment.")

    if st.sidebar.button("Logout", use_container_width=True):
        logout_user()
        st.rerun()
    return selected


def render_page(page_name: str, user: dict | None) -> None:
    if not user:
        login.render()
        return

    if user["role"] == "admin":
        admin_pages = {
            "Dashboard": lambda: admin_dashboard.render(user),
            "Student Management": student_management.render,
            "Academic Data Upload": data_upload.render,
            "Dropout Analysis": dropout_analysis.render,
            "Interventions": interventions.render,
        }
        admin_pages.get(page_name, lambda: admin_dashboard.render(user))()
        return

    student_pages = {
        "Dashboard": lambda: student_dashboard.render(user),
        "Profile": lambda: profile.render(user),
        "Psychometric Test": psychometric_test.render,
        "Career Recommendations": career_recommendations.render,
    }
    student_pages.get(page_name, lambda: student_dashboard.render(user))()


def main() -> None:
    init_session_state()
    bootstrap_database()
    current_user = get_current_user()

    st.title(settings.app_name)
    st.caption("AI/ML-assisted dropout intelligence and career guidance for educational institutions.")

    page_name = render_sidebar(current_user)
    render_page(page_name, current_user)


if __name__ == "__main__":
    main()

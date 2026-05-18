import streamlit as st

from config.settings import settings
from src.auth.guards import get_current_user, init_session_state, logout_user
from src.db.database import Base, apply_schema_patches, get_database_mode, get_engine, get_db_session
from src.db.seed import seed_demo_data


st.set_page_config(
    page_title=settings.app_name,
    page_icon=":mortar_board:",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner=False)
def bootstrap_database() -> bool:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    apply_schema_patches(engine)
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
            "Interest Assessment",
            "Career Ideas",
        ]

    selected = st.sidebar.radio("Go to", options, label_visibility="collapsed")

    database_mode = get_database_mode()
    if database_mode == "memory":
        st.sidebar.divider()
        st.sidebar.warning(
            "Using in-memory database — data resets when the app restarts. "
            "Use a writable data folder for persistent SQLite."
        )

    if st.sidebar.button("Logout", use_container_width=True):
        logout_user()
        st.rerun()
    return selected


def render_page(page_name: str, user: dict | None) -> None:
    if not user:
        from ui.pages import login

        login.render()
        return

    if user["role"] == "admin":
        from ui.pages import (
            admin_dashboard,
            data_upload,
            dropout_analysis,
            interventions,
            student_management,
        )

        admin_pages = {
            "Dashboard": lambda: admin_dashboard.render(user),
            "Student Management": lambda: student_management.render(user),
            "Academic Data Upload": lambda: data_upload.render(user),
            "Dropout Analysis": dropout_analysis.render,
            "Interventions": interventions.render,
        }
        admin_pages.get(page_name, lambda: admin_dashboard.render(user))()
        return

    from ui.pages import career_recommendations, profile, psychometric_test, student_dashboard

    student_pages = {
        "Dashboard": lambda: student_dashboard.render(user),
        "Profile": lambda: profile.render(user),
        "Interest Assessment": lambda: psychometric_test.render(user),
        "Career Ideas": lambda: career_recommendations.render(user),
    }
    student_pages.get(page_name, lambda: student_dashboard.render(user))()


def main() -> None:
    init_session_state()
    bootstrap_database()
    current_user = get_current_user()

    st.title(settings.app_name)
    from config.school_context import APP_TAGLINE

    st.caption(APP_TAGLINE)

    page_name = render_sidebar(current_user)
    render_page(page_name, current_user)


if __name__ == "__main__":
    main()

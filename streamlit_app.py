import streamlit as st

from config.settings import settings
from src.auth.guards import get_current_user, init_session_state, logout_user
from src.db.database import Base, apply_schema_patches, get_database_mode, get_engine, get_db_session
from src.db.seed import remove_legacy_demo_student, seed_demo_data
from ui.components.theme import inject_app_theme, render_app_hero


st.set_page_config(
    page_title=settings.app_name,
    page_icon=":mortar_board:",
    layout="wide",
    initial_sidebar_state="expanded",
)

ADMIN_PAGES = [
    "Dashboard",
    "Student Management",
    "Academic Data Upload",
    "Dropout Analysis",
    "Interventions",
]

STUDENT_PAGES = [
    "Dashboard",
    "Profile",
    "Interest Assessment",
    "Career Ideas",
]


@st.cache_resource(show_spinner=False)
def bootstrap_database() -> bool:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    apply_schema_patches(engine)
    with get_db_session() as session:
        remove_legacy_demo_student(session)
        seed_demo_data(session)
    return True


def page_options_for(user: dict) -> list[str]:
    return ADMIN_PAGES if user["role"] == "admin" else STUDENT_PAGES


def render_sidebar_nav(user: dict) -> str:
    options = page_options_for(user)
    if "nav_page" not in st.session_state or st.session_state["nav_page"] not in options:
        st.session_state["nav_page"] = options[0]

    st.sidebar.markdown('<p class="nav-heading">Menu</p>', unsafe_allow_html=True)
    selected = st.sidebar.radio(
        "Navigation",
        options,
        index=options.index(st.session_state["nav_page"]),
        label_visibility="collapsed",
        key="sidebar_nav_radio",
    )
    st.session_state["nav_page"] = selected
    return selected


def render_sidebar(user: dict | None) -> str | None:
    if not user:
        return None

    st.sidebar.markdown(
        f"""
        <div class="sidebar-account">
          <strong>{user["full_name"]}</strong><br/>
          <span style="color:#64748b;font-size:0.85rem;">{user["role"].title()}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if get_database_mode() == "memory":
        st.sidebar.warning("In-memory DB — data resets on restart.")

    page_name = render_sidebar_nav(user)

    st.sidebar.divider()
    if st.sidebar.button("Logout", use_container_width=True, key="sidebar_logout"):
        logout_user()
        st.session_state.pop("nav_page", None)
        st.rerun()

    return page_name


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
    inject_app_theme()

    current_user = get_current_user()
    from config.school_context import APP_TAGLINE

    if not current_user:
        render_app_hero(settings.app_name, APP_TAGLINE)
        render_page("Login", None)
        return

    page_name = render_sidebar(current_user)
    render_app_hero(settings.app_name, APP_TAGLINE)
    render_page(page_name, current_user)


if __name__ == "__main__":
    main()

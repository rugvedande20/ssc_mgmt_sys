import streamlit as st

from config.settings import settings
from src.auth.guards import clear_login_form_state, login_user
from src.auth.service import authenticate_user, is_superadmin_username
from src.db.database import get_db_session
from src.services.user_service import build_user_payload, enrich_staff_user_payload


def _sync_superadmin_hint() -> None:
    username = (st.session_state.get("login_username_input") or "").strip()
    if not username:
        st.session_state["login_is_superadmin"] = False
        return
    with get_db_session() as session:
        st.session_state["login_is_superadmin"] = is_superadmin_username(session, username)


def render() -> None:
    st.markdown(
        """
        <style>
        section.main > div {
          max-width: 22rem;
          margin-left: auto;
          margin-right: auto;
        }
        section.main .block-container {
          padding-top: 0.25rem;
          padding-bottom: 1rem;
          max-width: 22rem;
        }
        section.main { padding-top: 0.25rem; }
        .login-page div[data-testid="stForm"] input[type="password"] {
          padding-right: 2.75rem !important;
        }
        .login-page div[data-testid="stForm"] [data-testid="InputInstructions"] {
          position: static !important;
          display: block !important;
          width: 100% !important;
          margin: 0.2rem 0 0.5rem 0 !important;
          padding: 0 !important;
          font-size: 0.75rem !important;
          color: #94a3b8 !important;
          text-align: left !important;
          line-height: 1.35 !important;
        }
        .login-page div[data-testid="stForm"] [data-testid="stRadio"] label[data-testid="stWidgetLabel"] {
          display: none;
        }
        .login-page div[data-testid="stForm"] [data-testid="stRadio"] {
          margin: 0.35rem 0 0.5rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "login_is_superadmin" not in st.session_state:
        st.session_state["login_is_superadmin"] = False

    username_value = (st.session_state.get("login_username_input") or "").strip()
    if username_value:
        _sync_superadmin_hint()

    _spacer_l, login_col, _spacer_r = st.columns([1, 1.15, 1])
    with login_col:
        st.markdown('<div class="login-page">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="login-project-title">{settings.login_app_name}</div>
            <p class="login-project-tagline">School success &amp; career guidance · Class 6–10</p>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="login-card-compact">
              <div class="login-brand">Sign in</div>
              <p class="login-tagline">Superadmin, Admin, or student account</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False, enter_to_submit=True, border=False):
            st.text_input("Username", key="login_username_input")
            password = st.text_input("Password", type="password")
            portal_choice = None
            if username_value and st.session_state.get("login_is_superadmin"):
                portal_choice = st.radio(
                    "Super Admin destination",
                    options=["Admin UI", "User Management"],
                    horizontal=True,
                    label_visibility="collapsed",
                    key="superadmin_portal_choice",
                )
            submitted = st.form_submit_button("Sign in", use_container_width=True, type="primary")

        if submitted:
            _sync_superadmin_hint()
            username = (st.session_state.get("login_username_input") or "").strip()
            password = (password or "").strip()

            if not username:
                st.error("Enter your username.")
            elif not password:
                if st.session_state.get("login_is_superadmin"):
                    st.rerun()
                st.error("Enter your password.")
            else:
                with get_db_session() as session:
                    user = authenticate_user(session, username=username, password=password)
                    if not user:
                        user_payload = None
                    else:
                        portal = None
                        if user.role == "superadmin":
                            choice = portal_choice or "Admin UI"
                            portal = "users" if choice == "User Management" else "admin"
                        user_payload = enrich_staff_user_payload(
                            session,
                            build_user_payload(user),
                            portal=portal,
                        )
                if not user_payload:
                    st.error("Invalid credentials. Please try again.")
                else:
                    login_user(user_payload, portal=user_payload.get("portal"))
                    clear_login_form_state()
                    st.success("Login successful.")
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

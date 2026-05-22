import streamlit as st

from src.auth.guards import login_user
from src.auth.service import authenticate_user
from src.db.database import get_db_session
from src.services.user_service import build_user_payload


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
        .login-page div[data-testid="stForm"] [data-testid="stTextInput"]:last-of-type {
          margin-bottom: 0.15rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _spacer_l, login_col, _spacer_r = st.columns([1, 1.15, 1])
    with login_col:
        st.markdown('<div class="login-page">', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="login-project-title">SSC Management System</div>
            <p class="login-project-tagline">School success &amp; career guidance · Class 6–10</p>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="login-card-compact">
              <div class="login-brand">Sign in</div>
              <p class="login-tagline">Teacher, admin, or student account</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False, enter_to_submit=True, border=False):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True, type="primary")

        if submitted:
            with get_db_session() as session:
                user = authenticate_user(session, username=username.strip(), password=password)
                user_payload = build_user_payload(user) if user else None
            if not user_payload:
                st.error("Invalid credentials. Please try again.")
            else:
                login_user(user_payload)
                st.success("Login successful.")
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

"""Sidebar footer: superadmin portal switch and logout."""

from __future__ import annotations

import streamlit as st

from src.auth.guards import logout_user, switch_superadmin_portal


def render_superadmin_portal_switch(user: dict) -> None:
    if user.get("role") != "superadmin":
        return

    st.sidebar.markdown('<p class="nav-heading">Portal</p>', unsafe_allow_html=True)
    with st.sidebar.container(border=True):
        if user.get("portal") == "users":
            if st.sidebar.button(
                "Switch to Admin UI",
                use_container_width=True,
                type="primary",
                key="sidebar_switch_admin_ui",
            ):
                switch_superadmin_portal("admin")
                st.rerun()
        else:
            if st.sidebar.button(
                "Switch to User Management",
                use_container_width=True,
                type="primary",
                key="sidebar_switch_user_management",
            ):
                switch_superadmin_portal("users")
                st.rerun()


def render_logout_button() -> None:
    if st.sidebar.button("Logout", use_container_width=True, key="sidebar_logout"):
        logout_user()
        st.session_state.pop("nav_page", None)
        st.rerun()

"""Shared sidebar navigation — same menu UI for admin and student."""

from __future__ import annotations

import streamlit as st

SIDEBAR_NAV_RADIO_KEY = "sidebar_nav_radio"


def render_sidebar_nav(options: list[str]) -> str:
    """Pill-style menu in a bordered tray; used on every authenticated page."""
    if "nav_page" not in st.session_state or st.session_state["nav_page"] not in options:
        st.session_state["nav_page"] = options[0]

    st.sidebar.markdown('<p class="nav-heading">Menu</p>', unsafe_allow_html=True)

    with st.sidebar.container(border=True):
        selected = st.radio(
            "Navigation",
            options,
            index=options.index(st.session_state["nav_page"]),
            label_visibility="collapsed",
            key=SIDEBAR_NAV_RADIO_KEY,
        )

    st.session_state["nav_page"] = selected
    return selected

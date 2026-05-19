from __future__ import annotations

import streamlit as st


def inject_app_theme() -> None:
  st.markdown(
    """
    <style>
      /* Page background */
      .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 48%, #eef2ff 100%);
      }

      /* Main header */
      .app-hero {
        background: linear-gradient(135deg, #ffffff 0%, #eff6ff 55%, #fdf4ff 100%);
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.1rem 1.35rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 18px rgba(99, 102, 241, 0.08);
      }
      .app-hero h1 {
        font-size: 1.55rem !important;
        margin-bottom: 0.25rem !important;
        color: #1e293b !important;
      }
      .app-hero p {
        color: #64748b !important;
        margin: 0 !important;
      }

      /* Sidebar */
      section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border-right: 1px solid #e2e8f0;
      }
      section[data-testid="stSidebar"] .sidebar-account {
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: 10px;
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.75rem;
      }
      section[data-testid="stSidebar"] .nav-heading {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #64748b;
        margin: 0.25rem 0 0.5rem 0;
      }

      /* Sidebar nav — vertical tab-style radio */
      section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 0.45rem;
        width: 100%;
      }
      section[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.62rem 0.85rem !important;
        margin: 0 !important;
        width: 100%;
        transition: all 0.15s ease;
        color: #475569;
        font-weight: 500;
      }
      section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        border-color: #93c5fd;
        background: #f8fafc;
      }
      section[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(135deg, #dbeafe 0%, #e0e7ff 100%) !important;
        border-color: #818cf8 !important;
        color: #3730a3 !important;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
      }
      section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
        display: none;
      }

      /* Section cards in main area */
      div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 2px 12px rgba(15, 23, 42, 0.04);
      }

      /* Metrics */
      div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.65rem 0.85rem;
        box-shadow: 0 1px 6px rgba(15, 23, 42, 0.04);
      }
      div[data-testid="stMetric"] label {
        color: #64748b !important;
      }
      div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #1d4ed8 !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
  )


def render_app_hero(title: str, tagline: str) -> None:
  st.markdown(
    f"""
    <div class="app-hero">
      <h1>{title}</h1>
      <p>{tagline}</p>
    </div>
    """,
    unsafe_allow_html=True,
  )

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

      /* Inputs — subtle light grey (fixes invisible fields on light backgrounds) */
      .stTextInput input,
      .stTextArea textarea,
      .stNumberInput input,
      div[data-testid="stDateInput"] input,
      div[data-testid="stTimeInput"] input {
        background-color: #f1f5f9 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        color: #1e293b !important;
        caret-color: #1e293b !important;
      }

      .stTextInput input:focus,
      .stTextArea textarea:focus,
      .stNumberInput input:focus,
      div[data-testid="stDateInput"] input:focus {
        border-color: #94a3b8 !important;
        box-shadow: 0 0 0 1px #e2e8f0 !important;
        background-color: #f8fafc !important;
      }

      /* Selectbox, multiselect, combobox */
      div[data-baseweb="select"] > div,
      div[data-baseweb="input"] > div {
        background-color: #f1f5f9 !important;
        border-color: #d1d5db !important;
        color: #1e293b !important;
      }

      div[data-baseweb="select"] span,
      div[data-baseweb="input"] input {
        color: #1e293b !important;
      }

      /* File uploader dropzone */
      div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
        background-color: #f1f5f9 !important;
        border: 1px dashed #cbd5e1 !important;
      }

      /* Dataframe / table filter inputs */
      div[data-testid="stDataFrame"] input {
        background-color: #f1f5f9 !important;
        color: #1e293b !important;
      }

      /* Search & labels above fields */
      label[data-testid="stWidgetLabel"] {
        color: #475569 !important;
        font-weight: 500 !important;
      }

      /* Placeholder text */
      .stTextInput input::placeholder,
      .stTextArea textarea::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
      }

      /* Page chrome — shared admin & student headers */
      .page-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 0.85rem;
      }
      .page-header-title {
        font-size: 1.65rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
        line-height: 1.2;
      }
      .page-header-subtitle {
        color: #64748b;
        font-size: 0.95rem;
        margin: 0.35rem 0 0 0;
      }
      .page-header-badge {
        padding: 0.45rem 0.85rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        white-space: nowrap;
      }

      .section-title {
        font-size: 1.08rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0 0 0.2rem 0;
      }
      .section-caption {
        color: #64748b;
        font-size: 0.88rem;
        margin: 0 0 0.65rem 0;
      }

      .highlight-panel {
        display: flex;
        align-items: flex-start;
        gap: 0.85rem;
        border: 1px solid;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.85rem;
      }
      .highlight-panel-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        font-weight: 700;
        flex-shrink: 0;
      }
      .highlight-panel-title {
        font-size: 0.92rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
      }
      .highlight-panel-body {
        color: #475569;
        font-size: 0.86rem;
        line-height: 1.45;
      }

      .progress-panel {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
      }
      .progress-panel-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.45rem;
      }
      .progress-panel-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #64748b;
      }
      .progress-panel-pct {
        font-size: 1.15rem;
        font-weight: 800;
      }
      .progress-panel-track {
        height: 10px;
        border-radius: 999px;
        background: #f1f5f9;
        overflow: hidden;
      }
      .progress-panel-fill {
        height: 100%;
        border-radius: 999px;
      }
      .progress-panel-detail {
        margin-top: 0.45rem;
        font-size: 0.8rem;
        color: #64748b;
      }

      .form-section-header {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        margin: 0.35rem 0 0.65rem 0;
        padding-bottom: 0.35rem;
        border-bottom: 1px solid #f1f5f9;
      }
      .form-section-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
        color: #4338ca;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        flex-shrink: 0;
      }
      .form-section-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1e293b;
      }
      .form-section-subtitle {
        font-size: 0.78rem;
        color: #94a3b8;
        margin-top: 0.1rem;
      }

      .step-journey {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.65rem;
        margin: 0.25rem 0 0.5rem 0;
      }
      .step-card {
        border-radius: 12px;
        padding: 0.75rem 0.8rem;
        border: 1px solid #e2e8f0;
        background: #ffffff;
      }
      .step-card-done {
        background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
        border-color: #86efac;
      }
      .step-card-pending {
        background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
      }
      .step-card-marker {
        width: 28px;
        height: 28px;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.82rem;
        margin-bottom: 0.4rem;
      }
      .step-card-done .step-card-marker {
        background: #22c55e;
        color: #ffffff;
      }
      .step-card-pending .step-card-marker {
        background: #e0e7ff;
        color: #4338ca;
      }
      .step-card-label {
        font-size: 0.82rem;
        font-weight: 700;
        color: #1e293b;
        line-height: 1.25;
      }
      .step-card-hint {
        font-size: 0.72rem;
        color: #94a3b8;
        margin-top: 0.2rem;
      }

      .snapshot-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.55rem;
      }
      .snapshot-cell {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.55rem 0.7rem;
      }
      .snapshot-label {
        font-size: 0.72rem;
        color: #64748b;
        font-weight: 600;
      }
      .snapshot-value {
        font-size: 0.9rem;
        color: #0f172a;
        font-weight: 700;
        margin-top: 0.15rem;
      }

      .career-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.06);
      }
      .career-card-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.5rem;
      }
      .career-card-name {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0f172a;
      }
      .career-card-score {
        font-size: 1.65rem;
        font-weight: 800;
        line-height: 1;
      }
      .career-card-caption {
        text-align: right;
        font-size: 0.72rem;
        color: #94a3b8;
        margin-top: 0.1rem;
      }
      .career-card-rationale {
        color: #475569;
        font-size: 0.88rem;
        line-height: 1.45;
        margin: 0.65rem 0 0.5rem 0;
      }
      .career-card-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
      }
      .career-chip {
        display: inline-block;
        padding: 0.3rem 0.55rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
      }
      .career-chip-muted {
        color: #94a3b8;
        font-size: 0.8rem;
      }

      .login-shell {
        max-width: 440px;
        margin: 0.5rem auto 1rem auto;
      }
      .login-card {
        background: linear-gradient(135deg, #ffffff 0%, #eff6ff 55%, #fdf4ff 100%);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.35rem 1.4rem 1.1rem;
        box-shadow: 0 8px 28px rgba(99, 102, 241, 0.12);
      }
      .login-card h2 {
        margin: 0 0 0.35rem 0;
        font-size: 1.45rem;
        color: #1e293b;
      }
      .login-card p {
        margin: 0 0 1rem 0;
        color: #64748b;
        font-size: 0.92rem;
      }

      div[data-testid="stForm"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 0.85rem 1rem 1rem !important;
        background: #ffffff !important;
        box-shadow: 0 2px 12px rgba(15, 23, 42, 0.04) !important;
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

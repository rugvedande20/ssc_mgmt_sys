from __future__ import annotations

import streamlit as st


def inject_app_theme() -> None:
  st.markdown(
    """
    <style>
      /* Typography & page background */
      .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 48%, #eef2ff 100%);
        font-size: 0.9375rem !important;
        line-height: 1.5 !important;
        color: #1e293b !important;
      }
      .stApp h1 { font-size: 1.5rem !important; font-weight: 800 !important; color: #0f172a !important; }
      .stApp h2 { font-size: 1.25rem !important; font-weight: 700 !important; color: #1e293b !important; }
      .stApp h3 { font-size: 1.0625rem !important; font-weight: 700 !important; color: #1e293b !important; }
      .stApp p, .stApp li { font-size: 0.9375rem !important; line-height: 1.55 !important; }
      [data-testid="stCaptionContainer"], .stCaption {
        font-size: 0.875rem !important;
        color: #64748b !important;
      }
      label[data-testid="stWidgetLabel"] { font-size: 0.875rem !important; }
      div[data-testid="stMetric"] label { font-size: 0.8125rem !important; }
      div[data-testid="stMetric"] div[data-testid="stMetricValue"] { font-size: 1.375rem !important; }

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
        font-size: 1.375rem !important;
        margin-bottom: 0.25rem !important;
        color: #1e293b !important;
      }
      .app-hero p {
        color: #64748b !important;
        font-size: 0.9375rem !important;
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

      /* Sidebar nav — pill menu (admin & student, all pages) */
      section[data-testid="stSidebar"] [data-testid="stRadio"] {
        width: 100%;
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        width: 100%;
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
        background: #ffffff !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 999px !important;
        padding: 0.58rem 1rem 0.58rem 1.05rem !important;
        margin: 0 !important;
        width: 100% !important;
        min-height: 2.35rem;
        transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        cursor: pointer;
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(1) {
        border-color: #c7d2fe !important;
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2) {
        border-color: #fecaca !important;
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(3) {
        border-color: #fed7aa !important;
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(4) {
        border-color: #bbf7d0 !important;
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(5) {
        border-color: #bfdbfe !important;
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(6) {
        border-color: #ddd6fe !important;
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(1):hover,
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(1)[data-checked="true"] {
        background: #eef2ff !important;
        border-color: #818cf8 !important;
        color: #3730a3 !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.12);
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2):hover,
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2)[data-checked="true"] {
        background: #fff1f2 !important;
        border-color: #f87171 !important;
        color: #9f1239 !important;
        box-shadow: 0 2px 8px rgba(248, 113, 113, 0.12);
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(3):hover,
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(3)[data-checked="true"] {
        background: #fff7ed !important;
        border-color: #fb923c !important;
        color: #9a3412 !important;
        box-shadow: 0 2px 8px rgba(251, 146, 60, 0.12);
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(4):hover,
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(4)[data-checked="true"] {
        background: #ecfdf5 !important;
        border-color: #34d399 !important;
        color: #065f46 !important;
        box-shadow: 0 2px 8px rgba(52, 211, 153, 0.12);
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(5):hover,
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(5)[data-checked="true"] {
        background: #eff6ff !important;
        border-color: #60a5fa !important;
        color: #1e40af !important;
        box-shadow: 0 2px 8px rgba(96, 165, 250, 0.12);
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(6):hover,
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(6)[data-checked="true"] {
        background: #f5f3ff !important;
        border-color: #a78bfa !important;
        color: #5b21b6 !important;
        box-shadow: 0 2px 8px rgba(167, 139, 250, 0.12);
      }
      section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] {
        font-weight: 700 !important;
      }
      /* Menu tray container (st.container border around nav radio) */
      section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stRadio"]) {
        background: #f1f5f9 !important;
        border-color: #e2e8f0 !important;
        border-radius: 14px !important;
        padding: 0.55rem 0.5rem 0.6rem !important;
        margin-bottom: 0.35rem;
      }
      /* Fallback when :has() is unavailable — tray padding on radio block */
      section[data-testid="stSidebar"] [data-testid="stRadio"] {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 0.55rem 0.5rem 0.6rem;
        box-sizing: border-box;
      }
      section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stRadio"]) [data-testid="stRadio"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
      }
      /* Sidebar logout */
      section[data-testid="stSidebar"] [data-testid="stSidebar"] [data-testid="stButton"] > button,
      section[data-testid="stSidebar"] [data-testid="stButton"] > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: 1px solid #e2e8f0 !important;
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
        font-size: 1.375rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
        line-height: 1.25;
      }
      .page-header-subtitle {
        color: #64748b;
        font-size: 0.9375rem;
        margin: 0.35rem 0 0 0;
        line-height: 1.45;
      }
      .page-header-badge {
        padding: 0.4rem 0.75rem;
        border-radius: 999px;
        font-size: 0.8125rem;
        font-weight: 700;
        white-space: nowrap;
      }

      .section-title {
        font-size: 1.0625rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0 0 0.2rem 0;
      }
      .section-caption {
        color: #64748b;
        font-size: 0.875rem;
        margin: 0 0 0.65rem 0;
        line-height: 1.45;
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
        font-size: 0.9375rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
      }
      .highlight-panel-body {
        color: #475569;
        font-size: 0.875rem;
        line-height: 1.5;
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
        font-size: 0.875rem;
        font-weight: 700;
        color: #64748b;
      }
      .progress-panel-pct {
        font-size: 1.125rem;
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
        font-size: 0.8125rem;
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
        font-size: 0.9375rem;
        font-weight: 700;
        color: #1e293b;
      }
      .form-section-subtitle {
        font-size: 0.8125rem;
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
        font-size: 0.875rem;
        font-weight: 700;
        color: #1e293b;
        line-height: 1.3;
      }
      .step-card-hint {
        font-size: 0.8125rem;
        color: #94a3b8;
        margin-top: 0.2rem;
      }

      .snapshot-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.55rem;
        margin-bottom: 0.85rem;
        padding-bottom: 0.25rem;
      }
      div[data-testid="stVerticalBlockBorderWrapper"] .snapshot-grid:last-child {
        margin-bottom: 1rem;
      }
      .snapshot-cell {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.55rem 0.7rem;
      }
      .snapshot-label {
        font-size: 0.8125rem;
        color: #64748b;
        font-weight: 600;
      }
      .snapshot-value {
        font-size: 0.9375rem;
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
        font-size: 1.0625rem;
        font-weight: 800;
        color: #0f172a;
      }
      .career-card-score {
        font-size: 1.5rem;
        font-weight: 800;
        line-height: 1;
      }
      .career-card-caption {
        text-align: right;
        font-size: 0.8125rem;
        color: #94a3b8;
        margin-top: 0.1rem;
      }
      .career-card-rationale {
        color: #475569;
        font-size: 0.875rem;
        line-height: 1.5;
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
        font-size: 0.8125rem;
        font-weight: 700;
      }
      .career-chip-muted {
        color: #94a3b8;
        font-size: 0.8rem;
      }

      .login-page {
        display: flex;
        flex-direction: column;
        align-items: stretch;
        justify-content: flex-start;
        width: 100%;
        max-width: 22rem;
        margin: 0 auto 1.25rem auto;
        padding: 0 0 1rem 0;
      }
      .login-project-title {
        text-align: center;
        font-size: 1.375rem;
        font-weight: 800;
        color: #1e293b;
        margin: 0 0 0.25rem 0;
        line-height: 1.25;
      }
      .login-project-tagline {
        text-align: center;
        font-size: 0.875rem;
        color: #64748b;
        margin: 0 0 1rem 0;
        line-height: 1.4;
      }
      .login-page .login-card-compact,
      .login-page div[data-testid="stForm"],
      .login-page details {
        width: 100%;
        max-width: 100%;
      }
      .login-card-compact {
        background: linear-gradient(135deg, #ffffff 0%, #eff6ff 55%, #fdf4ff 100%);
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 1.15rem 1.25rem 0.95rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 6px 22px rgba(99, 102, 241, 0.1);
        text-align: center;
      }
      .login-brand {
        font-size: 1.25rem;
        font-weight: 800;
        color: #1e293b;
        margin: 0;
      }
      .login-tagline {
        margin: 0.35rem 0 0 0;
        color: #64748b;
        font-size: 0.875rem;
        line-height: 1.4;
      }
      .login-page div[data-testid="stForm"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 1rem 1.1rem 1.05rem !important;
        background: #ffffff !important;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06) !important;
      }
      .login-page details {
        margin-top: 0.75rem;
        font-size: 0.875rem;
      }

      /* Interest assessment — student engagement */
      .assess-invite {
        position: relative;
        border-radius: 16px;
        padding: 1.25rem 1.35rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 48%, #a855f7 100%);
        overflow: hidden;
        box-shadow: 0 10px 32px rgba(99, 102, 241, 0.28);
      }
      .assess-invite-glow {
        position: absolute;
        right: -20px;
        top: -30px;
        width: 140px;
        height: 140px;
        border-radius: 50%;
        background: rgba(255,255,255,0.15);
      }
      .assess-invite-content { position: relative; z-index: 1; }
      .assess-invite-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        color: #ffffff;
        font-size: 0.8125rem;
        font-weight: 700;
        padding: 0.3rem 0.65rem;
        border-radius: 999px;
        margin-bottom: 0.55rem;
      }
      .assess-invite-title {
        color: #ffffff;
        font-size: 1.25rem;
        font-weight: 800;
        margin: 0 0 0.45rem 0;
        line-height: 1.25;
      }
      .assess-invite-body {
        color: #e0e7ff;
        font-size: 0.9375rem;
        margin: 0 0 0.75rem 0;
        line-height: 1.5;
        max-width: 52rem;
      }
      .assess-invite-perks {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
      }
      .assess-perk {
        background: rgba(255,255,255,0.16);
        color: #ffffff;
        font-size: 0.8125rem;
        font-weight: 600;
        padding: 0.35rem 0.6rem;
        border-radius: 999px;
      }
      .riasec-trail {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin: 0.5rem 0 0.85rem 0;
      }
      .riasec-chip {
        display: flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.35rem 0.55rem;
        border-radius: 999px;
        border: 1.5px solid #e2e8f0;
        background: #f8fafc;
        font-size: 0.8125rem;
        font-weight: 600;
        color: #64748b;
      }
      .riasec-chip-icon { font-size: 0.95rem; }
      .riasec-chip-label { font-size: 0.8125rem; }
      .riasec-done {
        border-color: var(--chip-color);
        background: var(--chip-bg);
        color: var(--chip-color);
        opacity: 0.85;
      }
      .riasec-active {
        border-color: var(--chip-color);
        background: var(--chip-bg);
        color: var(--chip-color);
        box-shadow: 0 2px 10px rgba(99, 102, 241, 0.2);
        font-weight: 700;
      }
      .riasec-upcoming { opacity: 0.65; }
      .assess-section-hero {
        background: var(--section-bg);
        border: 1px solid #e2e8f0;
        border-left: 4px solid var(--section-color);
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.75rem;
      }
      .assess-section-step {
        font-size: 0.8125rem;
        font-weight: 700;
        color: var(--section-color);
        margin-bottom: 0.4rem;
      }
      .assess-section-head {
        display: flex;
        align-items: center;
        gap: 0.65rem;
      }
      .assess-section-icon { font-size: 1.5rem; }
      .assess-section-title {
        font-size: 1.125rem;
        font-weight: 800;
        color: #0f172a;
      }
      .assess-section-tag {
        font-size: 0.875rem;
        color: #64748b;
        margin-top: 0.1rem;
      }
      .assess-section-meta {
        font-size: 0.8125rem;
        color: #94a3b8;
        margin-top: 0.55rem;
      }
      .likert-legend {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.4rem;
        margin-bottom: 0.65rem;
        padding: 0.5rem 0.65rem;
        background: #f8fafc;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
      }
      .likert-legend-label {
        font-size: 0.8125rem;
        font-weight: 700;
        color: #64748b;
        margin-right: 0.25rem;
      }
      .likert-pill {
        font-size: 0.8125rem;
        color: #475569;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 0.2rem 0.5rem;
        border-radius: 999px;
      }
      div[data-testid="stForm"] div[role="radiogroup"] {
        background: #fafafa;
        border: 1px solid #f1f5f9;
        border-radius: 10px;
        padding: 0.55rem 0.65rem 0.45rem !important;
        margin-bottom: 0.45rem;
      }
      div[data-testid="stForm"] div[role="radiogroup"] > label {
        font-size: 0.9375rem !important;
        font-weight: 500 !important;
        color: #334155 !important;
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

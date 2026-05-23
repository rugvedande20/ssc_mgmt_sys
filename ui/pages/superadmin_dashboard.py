import streamlit as st

from src.db.database import get_db_session
from src.services.user_service import list_admin_status_dashboard
from ui.components.layout import section
from ui.components.page_chrome import render_page_header
from ui.components.change_password_panel import render_change_password_panel
from ui.components.tables import show_dataframe


def render(current_user: dict) -> None:
    render_page_header(
        "Admin overview",
        "Status and activity for each class admin account in the system.",
        badge_text="Super Admin",
        badge_variant="violet",
    )

    with get_db_session() as session:
        payload = list_admin_status_dashboard(session, include_inactive=True)

    summary = payload["summary"]
    rows = payload["admins"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Class admins", summary["total_admins"])
    m2.metric("Active admins", summary["active_admins"])
    m3.metric("Students (all admins)", summary["total_students"])
    m4.metric("Academic records", summary["total_academic_records"])

    s1, s2 = st.columns(2)
    s1.metric("Admins with students", summary["admins_with_students"])
    s2.metric("Awaiting academic data", summary["admins_awaiting_data"])

    with section(
        "Admin status",
        "Counts are shared by assigned class — multiple admins for the same grade see the same students and data.",
    ):
        if rows:
            show_dataframe(
                rows,
                columns=[
                    "admin_name",
                    "username",
                    "assigned_class",
                    "account_status",
                    "activity_status",
                    "students",
                    "academic_records",
                    "predictions",
                    "assessments",
                ],
            )
        else:
            st.info("No class admin accounts yet. Create admins under **User Creation**.")

    with section("Account security", "Update your sign-in password."):
        render_change_password_panel(current_user, key_prefix="superadmin_dash_pwd")

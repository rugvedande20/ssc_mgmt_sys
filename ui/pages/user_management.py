import streamlit as st

from config.constants import STAFF_ROLES
from src.db.database import get_db_session
from src.services.student_reset_service import CLEAR_STUDENTS_CONFIRM_PHRASE, clear_all_student_data, count_student_data
from src.services.user_service import delete_staff_user, list_staff_users, update_staff_user
from ui.components.layout import section
from ui.components.page_chrome import render_page_header
from ui.components.superadmin_reset_password_panel import render_superadmin_reset_password_panel
from ui.components.tables import show_dataframe


def render(current_user: dict) -> None:
    render_page_header(
        "User Management",
        "Search, edit, and deactivate admin accounts.",
        badge_text="Super Admin",
        badge_variant="violet",
    )

    with section("Staff directory", "Search and filter admin accounts. Edit or deactivate users below."):
        col1, col2 = st.columns((2, 1))
        with col1:
            search_term = st.text_input("Search users", placeholder="Name, username, email, or contact…")
        with col2:
            role_filter = st.selectbox("Filter by role", ["All", "admin", "superadmin"])

        with get_db_session() as session:
            staff = list_staff_users(session, search_term=search_term, role_filter=role_filter)

        if not staff:
            st.info("No staff accounts match your search.")
            return

        show_dataframe(
            staff,
            columns=["full_name", "username", "email", "role", "contact_phone", "assigned_grade"],
        )

        labels = {f"{row['full_name']} ({row['username']})": row["id"] for row in staff}
        selected_label = st.selectbox("Select user to edit or delete", list(labels.keys()))
        user_id = labels[selected_label]
        selected = next(row for row in staff if row["id"] == user_id)

        tab_edit, tab_reset_password, tab_delete, tab_clear_students = st.tabs(
            ["Edit user", "Reset password", "Delete user", "Clear student database"]
        )

        with tab_edit:
            with st.form("edit_staff_form"):
                new_username = st.text_input("Username", value=selected["username"])
                new_role = st.selectbox(
                    "Role",
                    STAFF_ROLES,
                    index=STAFF_ROLES.index(selected["role"]) if selected["role"] in STAFF_ROLES else 0,
                    format_func=lambda r: r.title(),
                )
                new_contact = st.text_input(
                    "Contact number",
                    value="" if selected["contact_phone"] == "—" else selected["contact_phone"],
                )
                save = st.form_submit_button("Save changes", use_container_width=True)

            if save:
                try:
                    with get_db_session() as session:
                        update_staff_user(
                            session,
                            user_id,
                            username=new_username,
                            role=new_role,
                            contact_phone=new_contact,
                            editor_id=current_user["id"],
                        )
                    st.success("User updated.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

        with tab_reset_password:
            render_superadmin_reset_password_panel(
                staff_id=user_id,
                staff_name=selected["full_name"],
                first_name=selected["first_name"],
                last_name=selected["last_name"],
                full_name=selected["full_name"],
                role=selected["role"],
                key_prefix=f"staff_pwd_{user_id}",
            )

        with tab_delete:
            st.warning(f"This will deactivate **{selected['full_name']}** (`{selected['username']}`).")
            if st.button("Deactivate user", type="primary", use_container_width=True):
                try:
                    with get_db_session() as session:
                        delete_staff_user(session, user_id, editor_id=current_user["id"])
                    st.success("User deactivated.")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

        with tab_clear_students:
            st.error(
                "**Critical:** Permanently deletes every student account and all related data "
                "(profiles, academic records, dropout predictions, assessments, career reports, interventions). "
                "Staff accounts are kept. Admin dashboards will show an empty cohort, as on first setup."
            )
            with get_db_session() as session:
                totals = count_student_data(session)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Students", totals["students"])
            m2.metric("Academic records", totals["academic_records"])
            m3.metric("Predictions", totals["predictions"])
            m4.metric("Assessments", totals["assessments"])

            acknowledge = st.checkbox(
                "I understand this cannot be undone and will remove all student data from the system.",
                key="clear_students_ack",
            )
            confirm_text = st.text_input(
                f"Type {CLEAR_STUDENTS_CONFIRM_PHRASE} to enable reset",
                placeholder=CLEAR_STUDENTS_CONFIRM_PHRASE,
                key="clear_students_confirm_text",
            )
            can_clear = acknowledge and confirm_text.strip() == CLEAR_STUDENTS_CONFIRM_PHRASE

            if st.button(
                "Clear student database",
                type="primary",
                use_container_width=True,
                disabled=not can_clear,
                key="clear_students_submit",
            ):
                with get_db_session() as session:
                    result = clear_all_student_data(session)
                for key in ("last_bulk_import", "nav_page", "sidebar_nav_radio"):
                    st.session_state.pop(key, None)
                removed = result.get("removed_students", 0)
                st.success(
                    f"Removed {removed} student account(s) and all linked records. "
                    "Admin views are reset to an empty cohort."
                )
                st.rerun()

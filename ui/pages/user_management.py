import pandas as pd
import streamlit as st

from config.constants import STAFF_ROLES, TARGET_GRADE_MAX, TARGET_GRADE_MIN
from config.school_context import GRADE_LABELS
from src.db.database import get_db_session
from src.services.user_service import (
    bulk_create_staff_users,
    create_staff_user,
    delete_staff_user,
    list_staff_users,
    update_staff_user,
)
from src.utils.file_upload import read_tabular_upload
from ui.components.layout import section
from ui.components.page_chrome import render_page_header
from ui.components.tables import show_dataframe

STAFF_BULK_COLUMNS = [
    "first_name",
    "last_name",
    "email",
    "contact",
    "role",
    "assigned_grade",
]


def _grade_options() -> tuple[list[int], list[str]]:
    grades = list(range(TARGET_GRADE_MIN, TARGET_GRADE_MAX + 1))
    return grades, [GRADE_LABELS[g] for g in grades]


def _bulk_template_rows() -> list[dict[str, object]]:
    return [
        {
            "first_name": "Ananya",
            "last_name": "Sharma",
            "email": "ananya.sharma@school.edu",
            "contact": "9876543210",
            "role": "admin",
            "assigned_grade": 6,
        },
        {
            "first_name": "Ravi",
            "last_name": "Patel",
            "email": "ravi.patel@school.edu",
            "contact": "9876543211",
            "role": "admin",
            "assigned_grade": 7,
        },
    ]


def _render_single_create(current_user: dict) -> None:
    grade_options, grade_labels = _grade_options()

    with section(
        "Create user",
        "Username and password are generated automatically (e.g. anasha_admin6 / anasha@123).",
    ):
        with st.form("create_staff_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            first_name = col1.text_input("First name")
            last_name = col2.text_input("Last name")
            email = col1.text_input("Email")
            contact = col2.text_input("Contact number")
            role = st.selectbox("Account role", STAFF_ROLES, format_func=lambda r: r.title())
            class_label = st.selectbox(
                "Assigned class (admins only)",
                grade_labels,
                index=0,
                disabled=role == "superadmin",
            )
            submitted = st.form_submit_button("Create user", use_container_width=True, type="primary")

        if submitted:
            try:
                assigned_grade = None
                if role == "admin":
                    assigned_grade = grade_options[grade_labels.index(class_label)]
                with get_db_session() as session:
                    account = create_staff_user(
                        session,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        contact_phone=contact,
                        role=role,
                        assigned_grade=assigned_grade,
                        created_by_id=current_user["id"],
                    )
                st.success(
                    f"Created **{account['full_name']}**. "
                    f"Username: `{account['username']}` · Password: `{account['password']}`"
                )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def _render_bulk_create(current_user: dict) -> None:
    template_df = pd.DataFrame(_bulk_template_rows())

    with section(
        "Bulk admin creation",
        "Upload a CSV or Excel file with one row per staff account.",
    ):
        st.markdown("**Required columns:** `first_name`, `last_name`, `email`, `contact`, `role`, `assigned_grade`")
        st.caption("`role` = admin or superadmin. `assigned_grade` = 6–10 (required for admin rows).")

        st.download_button(
            "Download template (CSV)",
            data=template_df.to_csv(index=False),
            file_name="staff_accounts_template.csv",
            mime="text/csv",
            use_container_width=True,
        )

        upload = st.file_uploader(
            "Upload staff file",
            type=["csv", "xlsx", "xls"],
            key="staff_bulk_upload",
        )

        if upload is not None:
            try:
                frame = read_tabular_upload(upload)
            except ValueError as exc:
                st.error(str(exc))
                return

            normalized = {str(c).strip().lower(): c for c in frame.columns}
            missing = [col for col in STAFF_BULK_COLUMNS if col not in normalized]
            if missing:
                st.error(f"Missing columns: {', '.join(missing)}")
                return

            rename_map = {normalized[col]: col for col in STAFF_BULK_COLUMNS}
            frame = frame.rename(columns=rename_map)
            rows = frame[STAFF_BULK_COLUMNS].fillna("").to_dict(orient="records")

            st.caption(f"**{len(rows)}** row(s) ready to import.")
            show_dataframe(rows[:10])

            if st.button("Import staff accounts", type="primary", use_container_width=True):
                with get_db_session() as session:
                    result = bulk_create_staff_users(session, rows, created_by_id=current_user["id"])
                st.success(f"Created **{result['accounts_created']}** of **{result['total_rows']}** account(s).")
                if result["created_accounts"]:
                    show_dataframe(result["created_accounts"])
                    cred_df = pd.DataFrame(result["created_accounts"])
                    st.download_button(
                        "Download credentials (CSV)",
                        data=cred_df.to_csv(index=False),
                        file_name="new_staff_logins.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                if result["row_errors"]:
                    st.warning("Some rows failed:")
                    for message in result["row_errors"][:25]:
                        st.caption(message)


def _render_directory(current_user: dict) -> None:
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

        tab_edit, tab_delete = st.tabs(["Edit user", "Delete user"])

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


def render(current_user: dict) -> None:
    render_page_header(
        "User Management",
        "Create and manage admin and superadmin accounts for the SSC Management System.",
        badge_text="Super Admin",
        badge_variant="violet",
    )

    tab_manage, tab_create = st.tabs(["User Management", "User Creation"])

    with tab_manage:
        _render_directory(current_user)

    with tab_create:
        _render_single_create(current_user)
        _render_bulk_create(current_user)

import pandas as pd
import streamlit as st

from config.constants import STAFF_ROLES, TARGET_GRADE_MAX, TARGET_GRADE_MIN
from config.school_context import GRADE_LABELS
from src.db.database import get_db_session
from src.services.user_service import bulk_create_staff_users, create_staff_user
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


def render(current_user: dict) -> None:
    render_page_header(
        "User Creation",
        "Create class admin and superadmin accounts. Share the generated username; set an initial password separately or use Change password after sign-in.",
        badge_text="Super Admin",
        badge_variant="violet",
    )

    grade_options, grade_labels = _grade_options()

    with section(
        "Create user",
        "Username is generated automatically. Share the username with the user; they can change their password from their dashboard after sign-in.",
    ):
        with st.form("create_staff_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            first_name = col1.text_input("First name")
            last_name = col2.text_input("Last name")
            email = col1.text_input("Email")
            contact = col2.text_input("Contact number")
            role = st.selectbox("Account role", STAFF_ROLES, format_func=lambda r: r.title())
            class_label = st.selectbox("Assigned class", grade_labels, index=0)
            submitted = st.form_submit_button("Create user", use_container_width=True, type="primary")

        if submitted:
            missing = [
                label
                for label, value in [
                    ("First name", first_name),
                    ("Last name", last_name),
                    ("Email", email),
                    ("Contact number", contact),
                ]
                if not str(value).strip()
            ]
            if missing:
                st.error(f"User creation failed. Required: {', '.join(missing)}.")
            else:
                try:
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
                        f"User created successfully. **{account['full_name']}** · "
                        f"username `{account['username']}`. They can use **Change password** on their dashboard after sign-in."
                    )
                    st.rerun()
                except ValueError as exc:
                    st.error(f"User creation failed. {exc}")

    template_df = pd.DataFrame(_bulk_template_rows())

    with section(
        "Bulk admin creation",
        "Upload a CSV or Excel file with one row per staff account.",
    ):
        st.markdown("**Required columns:** `first_name`, `last_name`, `email`, `contact`, `role`, `assigned_grade`")
        st.caption("`role` = admin or superadmin. `assigned_grade` = 6–10.")

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
                st.error(f"Upload failed. {exc}")
                return

            normalized = {str(c).strip().lower(): c for c in frame.columns}
            missing = [col for col in STAFF_BULK_COLUMNS if col not in normalized]
            if missing:
                st.error(f"Upload failed. Missing columns: {', '.join(missing)}")
                return

            rename_map = {normalized[col]: col for col in STAFF_BULK_COLUMNS}
            frame = frame.rename(columns=rename_map)
            rows = frame[STAFF_BULK_COLUMNS].fillna("").to_dict(orient="records")

            st.caption(f"**{len(rows)}** row(s) ready to import.")
            show_dataframe(rows[:10])

            if st.button("Import staff accounts", type="primary", use_container_width=True):
                with get_db_session() as session:
                    result = bulk_create_staff_users(session, rows, created_by_id=current_user["id"])
                if result["accounts_created"] == result["total_rows"]:
                    st.success(f"Successfully created {result['accounts_created']} account(s).")
                elif result["accounts_created"] > 0:
                    st.warning(
                        f"Partially successful: {result['accounts_created']} of {result['total_rows']} account(s) created."
                    )
                else:
                    st.error("User creation failed. No accounts were created.")
                if result["created_accounts"]:
                    show_dataframe(result["created_accounts"])
                    cred_df = pd.DataFrame(result["created_accounts"])
                    st.download_button(
                        "Download usernames (CSV)",
                        data=cred_df.to_csv(index=False),
                        file_name="new_staff_usernames.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                if result["row_errors"]:
                    st.warning("Some rows failed:")
                    for message in result["row_errors"][:25]:
                        st.caption(message)

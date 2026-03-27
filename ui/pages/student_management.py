import streamlit as st

from src.db.database import get_db_session
from src.services.student_service import create_student_user, list_students


def render() -> None:
    st.title("Student Management")
    st.caption("Create student accounts and browse the current roster without loading more records than needed.")

    with st.form("create_student_form", clear_on_submit=True):
        st.subheader("Create Student Account")
        col1, col2 = st.columns(2)
        full_name = col1.text_input("Full Name")
        username = col2.text_input("Username")
        email = col1.text_input("Email")
        password = col2.text_input("Temporary Password", type="password")
        department = col1.text_input("Department")
        semester = col2.number_input("Semester", min_value=1, max_value=12, value=1)
        submitted = st.form_submit_button("Create Student", use_container_width=True)

    if submitted:
        if not all([full_name.strip(), username.strip(), email.strip(), password]):
            st.error("Full name, username, email, and password are required.")
        else:
            try:
                with get_db_session() as session:
                    create_student_user(
                        session,
                        username=username,
                        full_name=full_name,
                        email=email,
                        password=password,
                        profile_data={"department": department, "semester": int(semester)},
                    )
                st.success("Student account created successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.divider()
    st.subheader("Student Directory")
    search_term = st.text_input("Search by name, username, or email")
    with get_db_session() as session:
        students = list_students(session, search_term=search_term, limit=100)

    if students:
        st.dataframe(students, use_container_width=True, hide_index=True)
    else:
        st.info("No students found for the current search.")

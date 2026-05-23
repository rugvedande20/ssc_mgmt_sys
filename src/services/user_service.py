from __future__ import annotations

from typing import Any

from sqlalchemy import func, or_, select

from src.auth.hashing import hash_password
from src.db.models import AcademicRecord, CareerRecommendation, DropoutPrediction, PsychometricAttempt, User
from src.services.staff_credentials import (
    allocate_unique_staff_username,
    build_staff_password,
    build_staff_username,
)


def build_user_payload(user: User, *, portal: str | None = None) -> dict:
    payload = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "contact_phone": user.contact_phone or "",
        "assigned_grade": user.assigned_grade,
    }
    if portal is not None:
        payload["portal"] = portal
    elif user.role == "superadmin":
        payload["portal"] = "admin"
    return payload


def get_dashboard_counts(
    session,
    *,
    assigned_grade: int | None = None,
    admin_user_id: int | None = None,
) -> dict:
    from src.db.models import StudentProfile

    student_filters = [User.role == "student"]
    if admin_user_id is not None:
        student_filters.append(User.created_by_admin_id == admin_user_id)
    if assigned_grade is not None:
        student_filters.append(StudentProfile.semester == assigned_grade)

    if assigned_grade is not None:
        total_students = (
            session.scalar(
                select(func.count())
                .select_from(User)
                .join(StudentProfile, StudentProfile.user_id == User.id)
                .where(*student_filters)
            )
            or 0
        )
    else:
        total_students = (
            session.scalar(select(func.count()).select_from(User).where(*student_filters)) or 0
        )

    total_admins = session.scalar(
        select(func.count()).select_from(User).where(User.role.in_(("admin", "superadmin")), User.is_active.is_(True))
    ) or 0
    total_predictions = session.scalar(select(func.count()).select_from(DropoutPrediction)) or 0
    total_assessments = session.scalar(select(func.count()).select_from(PsychometricAttempt)) or 0
    total_recommendations = session.scalar(select(func.count()).select_from(CareerRecommendation)) or 0
    academic_records = session.scalar(select(func.count()).select_from(AcademicRecord)) or 0
    return {
        "total_students": total_students,
        "total_admins": total_admins,
        "total_predictions": total_predictions,
        "total_assessments": total_assessments,
        "total_recommendations": total_recommendations,
        "academic_records": academic_records,
    }


def list_staff_users(
    session,
    *,
    search_term: str = "",
    role_filter: str = "All",
    include_inactive: bool = False,
) -> list[dict[str, Any]]:
    filters = [User.role.in_(("admin", "superadmin"))]
    if not include_inactive:
        filters.append(User.is_active.is_(True))
    if role_filter in ("admin", "superadmin"):
        filters.append(User.role == role_filter)

    query = select(User).where(*filters).order_by(User.full_name.asc())

    search_term = search_term.strip()
    if search_term:
        pattern = f"%{search_term}%"
        query = query.where(
            or_(
                User.full_name.ilike(pattern),
                User.username.ilike(pattern),
                User.email.ilike(pattern),
                User.contact_phone.ilike(pattern),
            )
        )

    users = session.scalars(query).all()
    return [_staff_row(user) for user in users]


def _staff_row(user: User) -> dict[str, Any]:
    from config.school_context import format_class

    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "contact_phone": user.contact_phone or "—",
        "assigned_grade": format_class(user.assigned_grade) if user.assigned_grade else "—",
        "is_active": user.is_active,
    }


def create_staff_user(
    session,
    *,
    first_name: str,
    last_name: str,
    email: str,
    contact_phone: str,
    role: str,
    assigned_grade: int | None,
    created_by_id: int,
) -> dict[str, str | int]:
    if role not in ("admin", "superadmin"):
        raise ValueError("Role must be admin or superadmin.")
    if role == "admin" and assigned_grade is None:
        raise ValueError("Assigned class is required for admin accounts.")

    first_name = first_name.strip()
    last_name = last_name.strip()
    email = email.strip()
    if not all([first_name, last_name, email]):
        raise ValueError("First name, last name, and email are required.")

    if session.scalar(select(User.id).where(User.email == email)):
        raise ValueError("Email is already registered.")

    base_username = build_staff_username(first_name, last_name, role, assigned_grade)
    username = allocate_unique_staff_username(session, base_username)
    password = build_staff_password(first_name, last_name)
    full_name = f"{first_name.title()} {last_name.title()}"

    user = User(
        username=username,
        full_name=full_name,
        first_name=first_name,
        last_name=last_name,
        email=email,
        contact_phone=contact_phone.strip() or None,
        password_hash=hash_password(password),
        role=role,
        assigned_grade=int(assigned_grade) if role == "admin" and assigned_grade is not None else None,
        is_active=True,
        created_by_admin_id=created_by_id,
    )
    session.add(user)
    session.flush()
    return {
        "id": user.id,
        "full_name": full_name,
        "username": username,
        "password": password,
    }


def bulk_create_staff_users(
    session,
    rows: list[dict[str, Any]],
    *,
    created_by_id: int,
) -> dict[str, Any]:
    created_accounts: list[dict[str, str]] = []
    row_errors: list[str] = []

    for index, row in enumerate(rows, start=1):
        try:
            first_name = str(row.get("first_name", "")).strip()
            last_name = str(row.get("last_name", "")).strip()
            email = str(row.get("email", "")).strip()
            contact_phone = str(row.get("contact", row.get("contact_phone", ""))).strip()
            role = str(row.get("role", "admin")).strip().lower()
            grade_raw = row.get("assigned_grade", row.get("class_grade", row.get("grade")))
            assigned_grade = int(grade_raw) if grade_raw not in (None, "") else None

            if role == "admin" and assigned_grade is None:
                raise ValueError("assigned_grade is required for admin rows.")

            account = create_staff_user(
                session,
                first_name=first_name,
                last_name=last_name,
                email=email,
                contact_phone=contact_phone,
                role=role,
                assigned_grade=assigned_grade,
                created_by_id=created_by_id,
            )
            created_accounts.append(
                {
                    "full_name": str(account["full_name"]),
                    "username": str(account["username"]),
                    "password": str(account["password"]),
                    "role": role,
                    "assigned_grade": str(assigned_grade) if assigned_grade else "—",
                }
            )
        except ValueError as exc:
            row_errors.append(f"Row {index}: {exc}")

    return {
        "total_rows": len(rows),
        "accounts_created": len(created_accounts),
        "created_accounts": created_accounts,
        "row_errors": row_errors,
    }


def update_staff_user(
    session,
    user_id: int,
    *,
    username: str,
    role: str,
    contact_phone: str,
    editor_id: int,
) -> User:
    user = session.get(User, user_id)
    if not user or user.role not in ("admin", "superadmin"):
        raise ValueError("Staff user not found.")
    if user.id == editor_id and role != user.role:
        raise ValueError("You cannot change your own role.")

    username = username.strip()
    if not username:
        raise ValueError("Username is required.")
    if role not in ("admin", "superadmin"):
        raise ValueError("Role must be admin or superadmin.")

    existing = session.scalar(select(User.id).where(User.username == username, User.id != user_id))
    if existing:
        raise ValueError("Username is already taken.")

    user.username = username
    user.role = role
    user.contact_phone = contact_phone.strip() or None
    if role == "superadmin":
        user.assigned_grade = None
    session.flush()
    return user


def delete_staff_user(session, user_id: int, *, editor_id: int) -> None:
    if user_id == editor_id:
        raise ValueError("You cannot delete your own account.")
    user = session.get(User, user_id)
    if not user or user.role not in ("admin", "superadmin"):
        raise ValueError("Staff user not found.")
    user.is_active = False
    session.flush()

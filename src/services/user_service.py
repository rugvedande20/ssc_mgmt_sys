from __future__ import annotations

import secrets
from typing import Any

from sqlalchemy import func, or_, select

from src.auth.hashing import hash_password
from src.db.models import AcademicRecord, CareerRecommendation, DropoutPrediction, PsychometricAttempt, User
from src.services.staff_credentials import allocate_unique_staff_username, build_staff_username
from src.utils.admin_context import student_grade_scope_filters


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


def grade_has_class_admin(session, grade: int) -> bool:
    return (
        session.scalar(
            select(User.id).where(
                User.role == "admin",
                User.is_active.is_(True),
                User.assigned_grade == int(grade),
            )
        )
        is not None
    )


def enrich_staff_user_payload(session, payload: dict, *, portal: str | None = None) -> dict:
    if portal is not None:
        payload = {**payload, "portal": portal}
    if payload["role"] not in ("admin", "superadmin"):
        return payload
    if payload["role"] == "superadmin" and payload.get("portal") == "users":
        return payload

    grade = payload.get("assigned_grade")
    if payload["role"] == "admin" or (grade is not None and grade_has_class_admin(session, int(grade))):
        payload["cohort_mode"] = "shared"
    else:
        payload["cohort_mode"] = "independent"
    return payload


def _count_students_for_scope(
    session,
    *,
    assigned_grade: int | None,
    created_by_admin_id: int | None = None,
) -> int:
    from src.db.models import StudentProfile

    if created_by_admin_id is not None:
        return (
            session.scalar(
                select(func.count()).select_from(User).where(
                    User.role == "student",
                    User.created_by_admin_id == created_by_admin_id,
                )
            )
            or 0
        )
    if assigned_grade is None:
        return session.scalar(select(func.count()).select_from(User).where(User.role == "student")) or 0
    return (
        session.scalar(
            select(func.count())
            .select_from(User)
            .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
            .where(User.role == "student", *student_grade_scope_filters(session, assigned_grade))
        )
        or 0
    )


def _count_student_linked(
    session,
    model,
    student_fk_column,
    *,
    assigned_grade: int | None,
    created_by_admin_id: int | None = None,
) -> int:
    from src.db.models import StudentProfile

    stmt = (
        select(func.count())
        .select_from(model)
        .join(User, User.id == student_fk_column)
        .where(User.role == "student")
    )
    if created_by_admin_id is not None:
        stmt = stmt.where(User.created_by_admin_id == created_by_admin_id)
    elif assigned_grade is not None:
        stmt = stmt.outerjoin(StudentProfile, StudentProfile.user_id == User.id).where(
            *student_grade_scope_filters(session, assigned_grade)
        )
    return session.scalar(stmt) or 0


def get_dashboard_counts(
    session,
    *,
    assigned_grade: int | None = None,
    created_by_admin_id: int | None = None,
) -> dict:
    total_students = _count_students_for_scope(
        session,
        assigned_grade=assigned_grade,
        created_by_admin_id=created_by_admin_id,
    )

    total_admins = session.scalar(
        select(func.count()).select_from(User).where(User.role.in_(("admin", "superadmin")), User.is_active.is_(True))
    ) or 0

    if assigned_grade is not None or created_by_admin_id is not None:
        scope = {"assigned_grade": assigned_grade, "created_by_admin_id": created_by_admin_id}
        total_predictions = _count_student_linked(
            session, DropoutPrediction, DropoutPrediction.student_id, **scope
        )
        total_assessments = _count_student_linked(
            session, PsychometricAttempt, PsychometricAttempt.student_id, **scope
        )
        total_recommendations = _count_student_linked(
            session, CareerRecommendation, CareerRecommendation.student_id, **scope
        )
        academic_records = _count_student_linked(
            session, AcademicRecord, AcademicRecord.student_id, **scope
        )
    else:
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


def _admin_activity_status(*, is_active: bool, students: int, academic_records: int) -> str:
    if not is_active:
        return "Inactive"
    if students == 0:
        return "No students"
    if academic_records == 0:
        return "Awaiting data"
    return "Active"


def list_admin_status_dashboard(session, *, include_inactive: bool = True) -> dict[str, Any]:
    from config.school_context import format_class

    filters = [User.role == "admin"]
    if not include_inactive:
        filters.append(User.is_active.is_(True))

    admins = session.scalars(select(User).where(*filters).order_by(User.full_name.asc())).all()
    rows: list[dict[str, Any]] = []

    for admin in admins:
        grade = int(admin.assigned_grade) if admin.assigned_grade is not None else None
        scope = {"assigned_grade": grade} if grade is not None else {}
        students = _count_students_for_scope(session, **scope)
        academic_records = _count_student_linked(
            session, AcademicRecord, AcademicRecord.student_id, **scope
        )
        predictions = _count_student_linked(
            session, DropoutPrediction, DropoutPrediction.student_id, **scope
        )
        assessments = _count_student_linked(
            session, PsychometricAttempt, PsychometricAttempt.student_id, **scope
        )
        rows.append(
            {
                "admin_name": admin.full_name,
                "username": admin.username,
                "assigned_class": format_class(admin.assigned_grade) if admin.assigned_grade else "—",
                "account_status": "Active" if admin.is_active else "Inactive",
                "activity_status": _admin_activity_status(
                    is_active=admin.is_active,
                    students=students,
                    academic_records=academic_records,
                ),
                "students": students,
                "academic_records": academic_records,
                "predictions": predictions,
                "assessments": assessments,
            }
        )

    active_rows = [row for row in rows if row["account_status"] == "Active"]
    unique_students = (
        session.scalar(select(func.count()).select_from(User).where(User.role == "student")) or 0
    )
    unique_records = session.scalar(select(func.count()).select_from(AcademicRecord)) or 0
    return {
        "summary": {
            "total_admins": len(rows),
            "active_admins": len(active_rows),
            "inactive_admins": len(rows) - len(active_rows),
            "total_students": unique_students,
            "total_academic_records": unique_records,
            "admins_with_students": sum(1 for row in active_rows if row["students"] > 0),
            "admins_awaiting_data": sum(
                1 for row in active_rows if row["students"] > 0 and row["academic_records"] == 0
            ),
        },
        "admins": rows,
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
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
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
    if assigned_grade is None:
        raise ValueError("Assigned class is required for admin and superadmin accounts.")

    first_name = first_name.strip()
    last_name = last_name.strip()
    email = email.strip()
    if not all([first_name, last_name, email]):
        raise ValueError("First name, last name, and email are required.")

    if session.scalar(select(User.id).where(User.email == email)):
        raise ValueError("Email is already registered.")

    base_username = build_staff_username(first_name, last_name, role, assigned_grade)
    username = allocate_unique_staff_username(session, base_username)
    initial_password = secrets.token_urlsafe(16)
    full_name = f"{first_name.title()} {last_name.title()}"

    user = User(
        username=username,
        full_name=full_name,
        first_name=first_name,
        last_name=last_name,
        email=email,
        contact_phone=contact_phone.strip(),
        password_hash=hash_password(initial_password),
        role=role,
        assigned_grade=int(assigned_grade),
        is_active=True,
        created_by_admin_id=created_by_id,
    )
    session.add(user)
    session.flush()
    return {
        "id": user.id,
        "full_name": full_name,
        "username": username,
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

            if assigned_grade is None:
                raise ValueError("assigned_grade is required for each row.")

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

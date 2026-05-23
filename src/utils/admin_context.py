from __future__ import annotations

from sqlalchemy import and_, or_, select

from config.school_context import format_class
from src.db.models import StudentProfile, User


def is_staff_admin_portal(user: dict | None) -> bool:
    if not user:
        return False
    if user["role"] == "admin":
        return True
    return user["role"] == "superadmin" and user.get("portal") == "admin"


def is_superadmin_user_management(user: dict | None) -> bool:
    return bool(user and user["role"] == "superadmin" and user.get("portal") == "users")


def assigned_grade_for_user(user: dict | None) -> int | None:
    if not user or not is_staff_admin_portal(user):
        return None
    grade = user.get("assigned_grade")
    return int(grade) if grade is not None else None


def is_independent_cohort(user: dict | None) -> bool:
    return bool(user and user.get("cohort_mode") == "independent")


def staff_ids_for_grade(session, grade: int) -> list[int]:
    return list(
        session.scalars(
            select(User.id).where(
                User.role.in_(("admin", "superadmin")),
                User.is_active.is_(True),
                User.assigned_grade == int(grade),
            )
        ).all()
        or []
    )


def student_grade_scope_filters(session, assigned_grade: int) -> list:
    """Match students in a class cohort, including imports missing class_grade on profile."""
    grade = int(assigned_grade)
    staff_ids = staff_ids_for_grade(session, grade)
    in_grade = StudentProfile.semester == grade
    if not staff_ids:
        return [in_grade]
    unassigned = or_(StudentProfile.semester.is_(None), StudentProfile.id.is_(None))
    return [or_(in_grade, and_(unassigned, User.created_by_admin_id.in_(staff_ids)))]


def student_scope_for_user(user: dict | None) -> dict[str, int]:
    """Returns kwargs for student/data queries: shared class cohort or independent owner."""
    if not is_staff_admin_portal(user):
        return {}
    if is_independent_cohort(user):
        return {"created_by_admin_id": int(user["id"])}
    grade = assigned_grade_for_user(user)
    if grade is not None:
        return {"assigned_grade": grade}
    return {}


def grade_scope_label(user: dict | None) -> str:
    grade = assigned_grade_for_user(user)
    if grade is None:
        return ""
    return format_class(grade)


def grade_default_index(user: dict | None, grade_options: list[int]) -> int:
    grade = assigned_grade_for_user(user)
    if grade is not None and grade in grade_options:
        return grade_options.index(grade)
    return 0


def admin_page_subtitle(base: str, user: dict | None) -> str:
    label = grade_scope_label(user)
    if not label:
        return base
    if is_independent_cohort(user):
        return f"{base} · Independent {label} workspace (no class admin linked yet)"
    return f"{base} · Shared {label} cohort (all admins for this class)"

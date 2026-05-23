from __future__ import annotations

from config.school_context import format_class


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


def student_owner_id(user: dict | None) -> int | None:
    """Staff accounts only see students they created."""
    if is_staff_admin_portal(user):
        return int(user["id"])
    return None


def admin_page_subtitle(base: str, user: dict | None) -> str:
    label = grade_scope_label(user)
    if not label:
        return base
    return f"{base} · Scoped to {label}"

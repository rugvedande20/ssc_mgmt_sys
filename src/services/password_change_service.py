from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import load_only

from src.auth.hashing import hash_password, verify_password
from src.db import models as _db_models  # noqa: F401 — register all ORM relationships
from src.db.models import User


def change_password(session, user_id: int, old_password: str, new_password: str) -> None:
    old_password = old_password.strip()
    new_password = new_password.strip()
    if not old_password:
        raise ValueError("Enter your current password.")
    if len(new_password) < 8:
        raise ValueError("New password must be at least 8 characters.")
    if old_password == new_password:
        raise ValueError("New password must be different from your current password.")

    user = session.scalar(
        select(User)
        .where(User.id == user_id)
        .options(load_only(User.id, User.password_hash, User.is_active))
    )
    if not user or not user.is_active:
        raise ValueError("Account not found.")

    if not verify_password(old_password, user.password_hash):
        raise ValueError("Current password is incorrect.")

    user.password_hash = hash_password(new_password)
    session.flush()


def admin_reset_student_password(
    session,
    student_id: int,
    new_password: str,
    *,
    assigned_grade: int | None = None,
    created_by_admin_id: int | None = None,
) -> str:
    """Set a student's password without the old password (admin recovery flow)."""
    from src.services.student_service import get_student_in_admin_scope

    new_password = new_password.strip()
    if len(new_password) < 8:
        raise ValueError("New password must be at least 8 characters.")

    student = get_student_in_admin_scope(
        session,
        student_id,
        assigned_grade=assigned_grade,
        created_by_admin_id=created_by_admin_id,
    )
    if not student:
        raise ValueError("Student not found or outside your class cohort.")

    student.password_hash = hash_password(new_password)
    session.flush()
    return new_password


def superadmin_reset_staff_password(session, staff_id: int, new_password: str) -> str:
    """Set an admin/superadmin password without the old password (superadmin recovery flow)."""
    new_password = new_password.strip()
    if len(new_password) < 8:
        raise ValueError("New password must be at least 8 characters.")

    user = session.scalar(
        select(User)
        .where(User.id == staff_id, User.role.in_(("admin", "superadmin")), User.is_active.is_(True))
        .options(load_only(User.id, User.password_hash, User.is_active, User.role))
    )
    if not user:
        raise ValueError("Staff account not found.")

    user.password_hash = hash_password(new_password)
    session.flush()
    return new_password

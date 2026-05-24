from __future__ import annotations

import re

from sqlalchemy import select

from src.db.models import User


def _letters_only(value: str) -> str:
    return re.sub(r"[^a-zA-Z]", "", value.strip().lower())


def build_staff_username(first_name: str, last_name: str, role: str, assigned_grade: int | None) -> str:
    prefix = build_name_prefix(first_name, last_name)
    if role == "superadmin":
        if assigned_grade is not None:
            return f"{prefix}_superadmin{int(assigned_grade)}"
        return f"{prefix}_superadmin"
    grade = int(assigned_grade) if assigned_grade is not None else 6
    return f"{prefix}_admin{grade}"


def build_name_prefix(first_name: str, last_name: str) -> str:
    first = _letters_only(first_name)[:3]
    last = _letters_only(last_name)[:3]
    return f"{first}{last}" if first and last else (first or last or "usr")


def build_staff_password(first_name: str, last_name: str) -> str:
    return f"{build_name_prefix(first_name, last_name)}@123"


def build_staff_role_password(first_name: str, last_name: str, role: str) -> str:
    prefix = build_name_prefix(first_name, last_name)
    if role == "superadmin":
        return f"{prefix}superadmin@123"
    return f"{prefix}admin@123"


def resolve_staff_name_parts(*, first_name: str | None, last_name: str | None, full_name: str) -> tuple[str, str]:
    first = str(first_name or "").strip()
    last = str(last_name or "").strip()
    if first and last:
        return first, last
    parts = [part for part in str(full_name or "").strip().split() if part]
    if len(parts) >= 2:
        return parts[0], parts[-1]
    if parts:
        return parts[0], parts[0]
    return "user", "user"


def default_staff_password(*, first_name: str | None, last_name: str | None, full_name: str) -> str:
    first, last = resolve_staff_name_parts(
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
    )
    return build_staff_password(first, last)


def default_staff_role_password(
    *,
    first_name: str | None,
    last_name: str | None,
    full_name: str,
    role: str,
) -> str:
    first, last = resolve_staff_name_parts(
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
    )
    return build_staff_role_password(first, last, role)


def allocate_unique_staff_username(session, base_username: str) -> str:
    candidate = base_username
    suffix = 2
    while session.scalar(select(User.id).where(User.username == candidate)):
        candidate = f"{base_username}{suffix}"
        suffix += 1
    return candidate

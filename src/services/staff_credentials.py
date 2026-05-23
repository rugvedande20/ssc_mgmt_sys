from __future__ import annotations

import re

from sqlalchemy import select

from src.db.models import User


def _letters_only(value: str) -> str:
    return re.sub(r"[^a-zA-Z]", "", value.strip().lower())


def build_staff_username(first_name: str, last_name: str, role: str, assigned_grade: int | None) -> str:
    prefix = build_name_prefix(first_name, last_name)
    if role == "superadmin":
        return f"{prefix}_superadmin"
    grade = int(assigned_grade) if assigned_grade is not None else 6
    return f"{prefix}_admin{grade}"


def build_name_prefix(first_name: str, last_name: str) -> str:
    first = _letters_only(first_name)[:3]
    last = _letters_only(last_name)[:3]
    return f"{first}{last}" if first and last else (first or last or "usr")


def build_staff_password(first_name: str, last_name: str) -> str:
    return f"{build_name_prefix(first_name, last_name)}@123"


def allocate_unique_staff_username(session, base_username: str) -> str:
    candidate = base_username
    suffix = 2
    while session.scalar(select(User.id).where(User.username == candidate)):
        candidate = f"{base_username}{suffix}"
        suffix += 1
    return candidate

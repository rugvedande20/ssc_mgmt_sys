from __future__ import annotations

import re

from sqlalchemy import select

from src.db.models import User


def _letters_only(value: str) -> str:
    return re.sub(r"[^a-zA-Z]", "", value.strip().lower())


def normalize_student_slug(value: object) -> str:
    slug = str(value or "").strip().lower().replace("-", "_")
    if slug in {"", "nan", "none", "student_username"}:
        return ""
    return slug


def import_row_identity_key(row: dict) -> str:
    """Stable per-row key for bulk import (one account per CSV student_username)."""
    slug = normalize_student_slug(row.get("student_username"))
    if slug:
        return slug
    first, last, _ = resolve_student_name(row)
    return f"{_letters_only(first_name)}_{_letters_only(last_name)}"


def login_username_base_for_import(row: dict, first_name: str, last_name: str) -> str:
    """Prefer full CSV slug as login base so distinct rows do not collide on 3+3 letters."""
    slug = normalize_student_slug(row.get("student_username"))
    if slug:
        base = re.sub(r"[^a-z0-9_]", "", slug)[:40]
        if len(base) >= 3:
            return base
    return build_login_username(first_name, last_name)


def build_login_username(first_name: str, last_name: str) -> str:
    first = _letters_only(first_name)
    last = _letters_only(last_name)
    username = f"{first[:3]}{last[:3]}"
    return username if len(username) >= 2 else f"{first[:1]}{last[:1]}stu"


def build_login_password(username: str) -> str:
    return f"{username}@123"


def normalize_full_name_key(full_name: str) -> str:
    """Case-insensitive key for duplicate-name checks."""
    return " ".join(str(full_name or "").strip().lower().split())


def resolve_student_name(row: dict) -> tuple[str, str, str]:
    raw_first = row.get("first_name")
    raw_last = row.get("last_name")
    if raw_first not in (None, "") and raw_last not in (None, ""):
        first = str(raw_first).strip()
        last = str(raw_last).strip()
    else:
        slug = str(row.get("student_username", "")).strip().replace("-", "_")
        if not slug or slug.lower() in {"nan", "none"}:
            full = str(row.get("full_name") or row.get("student_name") or "").strip()
            parts = [part for part in full.replace(",", " ").split() if part]
            if len(parts) < 2:
                raise ValueError(
                    "Each row needs student_username (firstname_lastname) or first_name + last_name."
                )
            first, last = parts[0], parts[-1]
        else:
            parts = [part for part in slug.split("_") if part]
            if not parts:
                raise ValueError("student_username must be like firstname_lastname (e.g. aarav_patil).")
            first = parts[0]
            last = parts[-1] if len(parts) > 1 else parts[0]
    full_name = f"{first.title()} {last.title()}"
    return first, last, full_name


def allocate_unique_username(session, base_username: str) -> str:
    candidate = base_username
    suffix = 2
    while session.scalar(select(User.id).where(User.username == candidate)):
        candidate = f"{base_username}{suffix}"
        suffix += 1
    return candidate


def build_student_email(username: str) -> str:
    return f"{username}@students.local"

"""Resolve and format who performed an auditable action."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import User

ACTIVITY_BY_UNKNOWN = "—"


def actor_display_name(user: User | None) -> str:
    if not user:
        return ACTIVITY_BY_UNKNOWN
    return (user.full_name or user.username or "").strip() or ACTIVITY_BY_UNKNOWN


def resolve_actor_name(session: Session, user_id: int | None) -> str:
    if not user_id:
        return ACTIVITY_BY_UNKNOWN
    user = session.get(User, user_id)
    return actor_display_name(user)


def actor_names_for_ids(session: Session, user_ids: set[int]) -> dict[int, str]:
    ids = {uid for uid in user_ids if uid}
    if not ids:
        return {}
    rows = session.execute(select(User.id, User.full_name, User.username).where(User.id.in_(ids))).all()
    return {row.id: (row.full_name or row.username or ACTIVITY_BY_UNKNOWN) for row in rows}


def activity_by_for_student_attempt(session: Session, student_id: int) -> str:
    return resolve_actor_name(session, student_id)


def format_activity_meta(
    *,
    at: str | None = None,
    at_label: str = "Recorded at",
    by: str | None = None,
) -> str:
    parts: list[str] = []
    if at:
        parts.append(f"{at_label}: {at}")
    if by and by != ACTIVITY_BY_UNKNOWN:
        parts.append(f"Activity by: {by}")
    elif by == ACTIVITY_BY_UNKNOWN:
        parts.append("Activity by: —")
    return " · ".join(parts)


def attach_activity_by(
    rows: list[dict[str, Any]],
    *,
    session: Session,
    actor_id_key: str,
    target_key: str = "activity_by",
) -> list[dict[str, Any]]:
    ids = {int(row[actor_id_key]) for row in rows if row.get(actor_id_key)}
    names = actor_names_for_ids(session, ids)
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        actor_id = item.get(actor_id_key)
        item[target_key] = names.get(int(actor_id), ACTIVITY_BY_UNKNOWN) if actor_id else ACTIVITY_BY_UNKNOWN
        out.append(item)
    return out

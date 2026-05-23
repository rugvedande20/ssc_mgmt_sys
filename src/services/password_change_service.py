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

from sqlalchemy import select

from src.auth.hashing import verify_password
from src.db.models import User


def authenticate_user(session, username: str, password: str) -> User | None:
    user = session.scalar(select(User).where(User.username == username, User.is_active.is_(True)))
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

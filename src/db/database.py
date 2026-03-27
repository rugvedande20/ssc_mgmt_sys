from contextlib import contextmanager
from typing import Iterator

import streamlit as st
from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from config.settings import settings


Base = declarative_base()
_DATABASE_MODE = "unknown"


def _build_engine(database_url: str):
    return create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )


@st.cache_resource(show_spinner=False)
def get_engine():
    global _DATABASE_MODE
    engine = _build_engine(settings.database_url)
    try:
        with engine.connect() as connection:
            with connection.begin():
                connection.execute(text("CREATE TABLE IF NOT EXISTS __healthcheck__ (id INTEGER)"))
                connection.execute(text("DROP TABLE __healthcheck__"))
        _DATABASE_MODE = "file"
        return engine
    except OperationalError:
        fallback_engine = _build_engine("sqlite+pysqlite:///:memory:")
        _DATABASE_MODE = "memory"
        return fallback_engine


@st.cache_resource(show_spinner=False)
def get_session_factory():
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)


@contextmanager
def get_db_session() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_database_mode() -> str:
    return _DATABASE_MODE

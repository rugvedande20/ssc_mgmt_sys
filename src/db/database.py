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
        fallback_engine = _build_engine("sqlite:///:memory:")
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


def _table_exists(connection, table: str) -> bool:
    row = connection.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table"),
        {"table": table},
    ).first()
    return row is not None


def _column_exists(connection, table: str, column: str) -> bool:
    if not _table_exists(connection, table):
        return False
    rows = connection.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(row[1] == column for row in rows)


def _add_column_if_missing(connection, table: str, column: str, definition: str) -> None:
    if not _column_exists(connection, table, column):
        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))


def apply_schema_patches(engine) -> None:
    """Add columns introduced after first deploy (SQLite has no automatic migrations)."""
    ddl_patches = [
        """CREATE TABLE IF NOT EXISTS career_guidance_snapshots (
            id INTEGER PRIMARY KEY,
            student_id INTEGER NOT NULL,
            student_class INTEGER,
            phase VARCHAR(32) NOT NULL,
            summary TEXT NOT NULL,
            report_json TEXT NOT NULL,
            labour_horizon_years INTEGER NOT NULL DEFAULT 5,
            generated_at DATETIME NOT NULL,
            FOREIGN KEY(student_id) REFERENCES users(id)
        )""",
        """CREATE TABLE IF NOT EXISTS password_reset_otps (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            otp_hash VARCHAR(255) NOT NULL,
            expires_at DATETIME NOT NULL,
            created_at DATETIME NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""",
    ]
    column_patches: list[tuple[str, str, str]] = [
        ("users", "created_by_admin_id", "INTEGER REFERENCES users(id)"),
        ("career_recommendations", "guidance_snapshot_id", "INTEGER REFERENCES career_guidance_snapshots(id)"),
        ("users", "first_name", "VARCHAR(60)"),
        ("users", "last_name", "VARCHAR(60)"),
        ("users", "contact_phone", "VARCHAR(30)"),
        ("users", "assigned_grade", "INTEGER"),
        ("academic_records", "recorded_by_user_id", "INTEGER REFERENCES users(id)"),
        ("dropout_predictions", "predicted_by_user_id", "INTEGER REFERENCES users(id)"),
        ("student_profiles", "updated_by_user_id", "INTEGER REFERENCES users(id)"),
        ("career_guidance_snapshots", "generated_by_user_id", "INTEGER REFERENCES users(id)"),
        ("intervention_logs", "intervention_type", "VARCHAR(80) DEFAULT 'One-on-one counseling'"),
        ("intervention_logs", "module", "VARCHAR(120)"),
        ("intervention_logs", "priority", "VARCHAR(20) DEFAULT 'Medium'"),
        ("intervention_logs", "intensity", "VARCHAR(20) DEFAULT 'Medium'"),
        ("intervention_logs", "risk_level_at_time", "VARCHAR(20)"),
        ("intervention_logs", "risk_score_at_time", "FLOAT"),
        ("intervention_logs", "status", "VARCHAR(20) DEFAULT 'completed'"),
        ("intervention_logs", "scheduled_at", "DATETIME"),
        ("intervention_logs", "completed_at", "DATETIME"),
        ("intervention_logs", "dropout_prediction_id", "INTEGER REFERENCES dropout_predictions(id)"),
    ]
    with engine.connect() as connection:
        with connection.begin():
            for statement in ddl_patches:
                connection.execute(text(statement))
            for table, column, definition in column_patches:
                _add_column_if_missing(connection, table, column, definition)

from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import desc, func, or_, select

from src.auth.hashing import hash_password
from src.db.models import AcademicRecord, StudentProfile, User


PROFILE_DEFAULTS = {
    "age": None,
    "gender": "",
    "department": "",
    "semester": None,
    "family_income_band": "",
    "parental_education": "",
    "travel_distance_km": None,
    "internet_access": "",
    "interests_summary": "",
    "strengths_summary": "",
}


def get_student_profile(session, user_id: int) -> StudentProfile | None:
    return session.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))


def upsert_student_profile(session, user_id: int, profile_data: dict[str, Any]) -> StudentProfile:
    profile = get_student_profile(session, user_id)
    if not profile:
        profile = StudentProfile(user_id=user_id)
        session.add(profile)

    for field_name, default_value in PROFILE_DEFAULTS.items():
        raw_value = profile_data.get(field_name, default_value)
        value = default_value if raw_value == "" else raw_value
        setattr(profile, field_name, value)

    session.flush()
    return profile


def username_or_email_exists(session, username: str, email: str) -> bool:
    existing = session.scalar(
        select(User.id).where(or_(User.username == username.strip(), User.email == email.strip().lower()))
    )
    return existing is not None


def create_student_user(
    session,
    *,
    username: str,
    full_name: str,
    email: str,
    password: str,
    profile_data: dict[str, Any],
) -> User:
    username = username.strip()
    email = email.strip().lower()
    if username_or_email_exists(session, username, email):
        raise ValueError("A user with this username or email already exists.")

    student = User(
        username=username,
        full_name=full_name.strip(),
        email=email,
        password_hash=hash_password(password),
        role="student",
        is_active=True,
    )
    session.add(student)
    session.flush()
    upsert_student_profile(session, student.id, profile_data)
    return student


def list_students(session, search_term: str = "", limit: int = 100) -> list[dict[str, Any]]:
    query = (
        select(
            User.id,
            User.full_name,
            User.username,
            User.email,
            StudentProfile.department,
            StudentProfile.semester,
        )
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(User.role == "student")
        .order_by(User.full_name.asc())
        .limit(limit)
    )

    search_term = search_term.strip()
    if search_term:
        search_pattern = f"%{search_term}%"
        query = (
            select(
                User.id,
                User.full_name,
                User.username,
                User.email,
                StudentProfile.department,
                StudentProfile.semester,
            )
            .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
            .where(
                User.role == "student",
                or_(
                    User.full_name.ilike(search_pattern),
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                ),
            )
            .order_by(User.full_name.asc())
            .limit(limit)
        )

    rows = session.execute(query).all()
    return [
        {
            "id": row.id,
            "full_name": row.full_name,
            "username": row.username,
            "email": row.email,
            "department": row.department or "-",
            "semester": row.semester or "-",
        }
        for row in rows
    ]


def list_student_options(session) -> list[tuple[int, str]]:
    rows = session.execute(
        select(User.id, User.full_name).where(User.role == "student").order_by(User.full_name.asc())
    ).all()
    return [(row.id, row.full_name) for row in rows]


def add_academic_record(session, student_id: int, record_data: dict[str, Any]) -> AcademicRecord:
    record = AcademicRecord(
        student_id=student_id,
        attendance_percentage=record_data.get("attendance_percentage"),
        cgpa=record_data.get("cgpa"),
        internal_marks=record_data.get("internal_marks"),
        backlog_count=record_data.get("backlog_count"),
        fee_pending=record_data.get("fee_pending"),
        scholarship_status=record_data.get("scholarship_status"),
        extracurricular_participation=record_data.get("extracurricular_participation"),
        disciplinary_issues=record_data.get("disciplinary_issues"),
        engagement_score=record_data.get("engagement_score"),
        stress_level=record_data.get("stress_level"),
    )
    session.add(record)
    session.flush()
    return record


def list_recent_academic_records(session, limit: int = 50) -> list[dict[str, Any]]:
    rows = session.execute(
        select(
            User.full_name,
            AcademicRecord.attendance_percentage,
            AcademicRecord.cgpa,
            AcademicRecord.backlog_count,
            AcademicRecord.recorded_at,
        )
        .join(AcademicRecord, AcademicRecord.student_id == User.id)
        .order_by(desc(AcademicRecord.recorded_at))
        .limit(limit)
    ).all()
    return [
        {
            "student_name": row.full_name,
            "attendance_percentage": row.attendance_percentage,
            "cgpa": row.cgpa,
            "backlog_count": row.backlog_count,
            "recorded_at": row.recorded_at.strftime("%Y-%m-%d %H:%M"),
        }
        for row in rows
    ]


def list_students_with_latest_records(session) -> list[dict[str, Any]]:
    latest_record_subquery = (
        select(
            AcademicRecord.student_id,
            AcademicRecord.id,
            func.row_number()
            .over(partition_by=AcademicRecord.student_id, order_by=AcademicRecord.recorded_at.desc())
            .label("record_rank"),
        )
        .subquery()
    )

    rows = session.execute(
        select(
            User.full_name,
            User.username,
            StudentProfile.department,
            StudentProfile.semester,
            AcademicRecord.attendance_percentage,
            AcademicRecord.cgpa,
            AcademicRecord.backlog_count,
            AcademicRecord.recorded_at,
        )
        .join(latest_record_subquery, latest_record_subquery.c.student_id == User.id)
        .join(AcademicRecord, AcademicRecord.id == latest_record_subquery.c.id)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(User.role == "student", latest_record_subquery.c.record_rank == 1)
        .order_by(User.full_name.asc())
    ).all()

    return [
        {
            "student_name": row.full_name,
            "username": row.username,
            "department": row.department or "-",
            "semester": row.semester or "-",
            "attendance_percentage": row.attendance_percentage,
            "cgpa": row.cgpa,
            "backlog_count": row.backlog_count,
            "recorded_at": row.recorded_at.strftime("%Y-%m-%d %H:%M"),
        }
        for row in rows
    ]


def academic_record_summary(session) -> dict[str, int]:
    return {
        "students_with_records": session.scalar(
            select(func.count(func.distinct(AcademicRecord.student_id))).select_from(AcademicRecord)
        )
        or 0,
        "total_records": session.scalar(select(func.count()).select_from(AcademicRecord)) or 0,
    }


def bulk_insert_academic_records(session, csv_frame: pd.DataFrame) -> int:
    required_columns = {
        "student_username",
        "attendance_percentage",
        "cgpa",
        "internal_marks",
        "backlog_count",
        "fee_pending",
        "scholarship_status",
        "extracurricular_participation",
        "disciplinary_issues",
        "engagement_score",
        "stress_level",
    }
    missing_columns = required_columns.difference(csv_frame.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing_columns))}")

    user_rows = session.execute(select(User.id, User.username).where(User.role == "student")).all()
    username_to_id = {row.username: row.id for row in user_rows}
    inserted_count = 0

    for row in csv_frame.to_dict(orient="records"):
        student_id = username_to_id.get(str(row["student_username"]).strip())
        if not student_id:
            continue
        add_academic_record(
            session,
            student_id=student_id,
            record_data={
                "attendance_percentage": _to_optional_float(row.get("attendance_percentage")),
                "cgpa": _to_optional_float(row.get("cgpa")),
                "internal_marks": _to_optional_float(row.get("internal_marks")),
                "backlog_count": _to_optional_int(row.get("backlog_count")),
                "fee_pending": _to_optional_string(row.get("fee_pending")),
                "scholarship_status": _to_optional_string(row.get("scholarship_status")),
                "extracurricular_participation": _to_optional_string(row.get("extracurricular_participation")),
                "disciplinary_issues": _to_optional_int(row.get("disciplinary_issues")),
                "engagement_score": _to_optional_float(row.get("engagement_score")),
                "stress_level": _to_optional_float(row.get("stress_level")),
            },
        )
        inserted_count += 1

    return inserted_count


def _to_optional_float(value: Any) -> float | None:
    if value in ("", None) or pd.isna(value):
        return None
    return float(value)


def _to_optional_int(value: Any) -> int | None:
    if value in ("", None) or pd.isna(value):
        return None
    return int(value)


def _to_optional_string(value: Any) -> str | None:
    if value in ("", None) or pd.isna(value):
        return None
    return str(value).strip()

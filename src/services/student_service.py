from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import desc, func, or_, select

from src.auth.hashing import hash_password
from src.services.student_credentials import (
    allocate_unique_username,
    build_login_password,
    build_login_username,
    build_student_email,
    resolve_student_name,
)
from config.school_context import (
    ACADEMIC_CSV_ALIASES,
    ACADEMIC_DB_COLUMNS,
    DB_TO_SCHOOL_CSV_HEADER,
    SCHOOL_ACADEMIC_CSV_COLUMNS,
)
from src.db.models import AcademicRecord, CareerRecommendation, DropoutPrediction, PsychometricAttempt, StudentProfile, User


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


def get_student_profile_payload(session, user_id: int) -> dict[str, Any] | None:
    profile = get_student_profile(session, user_id)
    if not profile:
        return None
    return {
        "age": profile.age,
        "gender": profile.gender or "",
        "department": profile.department or "",
        "semester": profile.semester,
        "family_income_band": profile.family_income_band or "",
        "parental_education": profile.parental_education or "",
        "travel_distance_km": profile.travel_distance_km,
        "internet_access": profile.internet_access or "",
        "interests_summary": profile.interests_summary or "",
        "strengths_summary": profile.strengths_summary or "",
    }


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
    created_by_admin_id: int | None = None,
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
        created_by_admin_id=created_by_admin_id,
    )
    session.add(student)
    session.flush()
    upsert_student_profile(session, student.id, profile_data)
    return student


def list_students(
    session,
    search_term: str = "",
    limit: int = 100,
    admin_user_id: int | None = None,
) -> list[dict[str, Any]]:
    filters = [User.role == "student"]
    if admin_user_id is not None:
        filters.append(User.created_by_admin_id == admin_user_id)

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
        .where(*filters)
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
                *filters,
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
            "school": row.department or "-",
            "class": row.semester if row.semester is not None else "-",
        }
        for row in rows
    ]


def list_student_options(session, admin_user_id: int | None = None) -> list[tuple[int, str]]:
    filters = [User.role == "student"]
    if admin_user_id is not None:
        filters.append(User.created_by_admin_id == admin_user_id)
    rows = session.execute(
        select(User.id, User.full_name).where(*filters).order_by(User.full_name.asc())
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
            "overall_marks_pct": row.cgpa,
            "subjects_below_passing": row.backlog_count,
            "recorded_at": row.recorded_at.strftime("%Y-%m-%d %H:%M"),
        }
        for row in rows
    ]


def normalize_academic_csv_frame(csv_frame: pd.DataFrame) -> pd.DataFrame:
    column_map: dict[str, str] = {}
    for column in csv_frame.columns:
        normalized = str(column).strip().lower()
        if normalized in ACADEMIC_CSV_ALIASES:
            column_map[column] = ACADEMIC_CSV_ALIASES[normalized]
        else:
            column_map[column] = normalized
    return csv_frame.rename(columns=column_map)


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
            "school": row.department or "-",
            "class": row.semester if row.semester is not None else "-",
            "attendance_percentage": row.attendance_percentage,
            "overall_marks_pct": row.cgpa,
            "subjects_below_passing": row.backlog_count,
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


# Preferred upload headers for Class 6–10 (see config.school_context)
ACADEMIC_CSV_COLUMNS = SCHOOL_ACADEMIC_CSV_COLUMNS


def get_student_dashboard_payload(session, user_id: int) -> dict[str, Any]:
    profile = get_student_profile_payload(session, user_id)
    latest_assessment_row = session.scalar(
        select(PsychometricAttempt)
        .where(PsychometricAttempt.student_id == user_id)
        .order_by(desc(PsychometricAttempt.submitted_at))
    )
    recommendation_rows = session.execute(
        select(CareerRecommendation)
        .where(CareerRecommendation.student_id == user_id)
        .order_by(CareerRecommendation.match_score.desc())
        .limit(3)
    ).scalars()

    latest_assessment = None
    if latest_assessment_row:
        latest_assessment = {
            "summary": latest_assessment_row.summary,
            "top_codes": latest_assessment_row.top_codes,
        }

    recommendations = [
        {
            "career_name": row.career_name,
            "match_score": row.match_score,
            "rationale": row.rationale,
            "skill_gap": row.skill_gap,
            "certifications": row.certifications,
        }
        for row in recommendation_rows
    ]

    return {
        "profile": profile,
        "latest_assessment": latest_assessment,
        "recommendations": recommendations,
    }


def get_student_overview(session, student_id: int) -> dict[str, Any] | None:
    user = session.scalar(select(User).where(User.id == student_id, User.role == "student"))
    if not user:
        return None

    profile = get_student_profile_payload(session, student_id)
    latest_record = session.scalar(
        select(AcademicRecord)
        .where(AcademicRecord.student_id == student_id)
        .order_by(desc(AcademicRecord.recorded_at))
    )
    latest_prediction = session.scalar(
        select(DropoutPrediction)
        .where(DropoutPrediction.student_id == student_id)
        .order_by(desc(DropoutPrediction.predicted_at))
    )
    latest_attempt = session.scalar(
        select(PsychometricAttempt)
        .where(PsychometricAttempt.student_id == student_id)
        .order_by(desc(PsychometricAttempt.submitted_at))
    )
    recommendation_count = (
        session.scalar(
            select(func.count())
            .select_from(CareerRecommendation)
            .where(CareerRecommendation.student_id == student_id)
        )
        or 0
    )

    return {
        "id": user.id,
        "full_name": user.full_name,
        "username": user.username,
        "email": user.email,
        "profile": profile,
        "latest_academic": None
        if not latest_record
        else {
            "attendance_percentage": latest_record.attendance_percentage,
            "overall_marks_pct": latest_record.cgpa,
            "latest_term_score_pct": latest_record.internal_marks,
            "subjects_below_passing": latest_record.backlog_count,
            "engagement_score": latest_record.engagement_score,
            "stress_level": latest_record.stress_level,
            "recorded_at": latest_record.recorded_at.strftime("%Y-%m-%d %H:%M"),
        },
        "latest_prediction": None
        if not latest_prediction
        else {
            "risk_score": round(latest_prediction.risk_score * 100, 1),
            "risk_level": latest_prediction.risk_level,
            "top_factors": latest_prediction.top_factors,
            "predicted_at": latest_prediction.predicted_at.strftime("%Y-%m-%d %H:%M"),
        },
        "latest_psychometric": None
        if not latest_attempt
        else {
            "top_codes": latest_attempt.top_codes,
            "summary": latest_attempt.summary,
            "submitted_at": latest_attempt.submitted_at.strftime("%Y-%m-%d %H:%M"),
        },
        "recommendation_count": recommendation_count,
    }


def _academic_record_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
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
    }


def _optional_profile_fields_from_row(row: dict[str, Any]) -> dict[str, Any]:
    profile: dict[str, Any] = {}
    school_name = row.get("school_name")
    if school_name not in (None, ""):
        profile["department"] = str(school_name).strip()
    class_grade = row.get("class_grade") or row.get("semester")
    if class_grade not in (None, ""):
        try:
            profile["semester"] = int(class_grade)
        except (TypeError, ValueError):
            pass
    return profile


def bulk_import_students_from_csv(
    session,
    csv_frame: pd.DataFrame,
    admin_user_id: int,
) -> dict[str, Any]:
    """Create student accounts (if needed) and import academic rows for the logged-in admin."""
    from src.utils.file_upload import prepare_import_dataframe

    csv_frame = prepare_import_dataframe(csv_frame)
    total_rows = len(csv_frame)
    if total_rows == 0:
        raise ValueError("The file has no data rows to import.")

    raw_rows = csv_frame.to_dict(orient="records")
    normalized = normalize_academic_csv_frame(csv_frame.copy())

    required_columns = set(ACADEMIC_DB_COLUMNS)
    missing_columns = required_columns.difference(normalized.columns)
    if missing_columns:
        friendly_missing = [DB_TO_SCHOOL_CSV_HEADER.get(col, col) for col in sorted(missing_columns)]
        raise ValueError(f"Missing required columns: {', '.join(friendly_missing)}")

    login_to_student_id = {
        row.username: row.id
        for row in session.execute(select(User.username, User.id).where(User.role == "student")).all()
    }
    base_username_to_student_id: dict[str, int] = {}

    created_accounts: list[dict[str, str]] = []
    existing_accounts_used: list[str] = []
    records_imported = 0
    row_errors: list[str] = []

    for index, norm_row in enumerate(normalized.to_dict(orient="records")):
        raw_row = raw_rows[index]
        merged_row = {**raw_row, **norm_row}
        try:
            first, last, full_name = resolve_student_name(merged_row)
            base_username = build_login_username(first, last)
            student_id = base_username_to_student_id.get(base_username)
            if not student_id:
                student_id = login_to_student_id.get(base_username)

            if not student_id:
                login_username = allocate_unique_username(session, base_username)
                password = build_login_password(login_username)
                email = build_student_email(login_username)
                if username_or_email_exists(session, login_username, email):
                    email = f"{login_username}.{admin_user_id}@students.local"
                profile_data = _optional_profile_fields_from_row(merged_row)
                student = create_student_user(
                    session,
                    username=login_username,
                    full_name=full_name,
                    email=email,
                    password=password,
                    profile_data=profile_data,
                    created_by_admin_id=admin_user_id,
                )
                student_id = student.id
                login_to_student_id[login_username] = student_id
                base_username_to_student_id[base_username] = student_id
                created_accounts.append(
                    {
                        "full_name": full_name,
                        "username": login_username,
                        "password": password,
                        "csv_label": str(merged_row.get("student_username", "")),
                    }
                )
            else:
                base_username_to_student_id[base_username] = student_id
                existing_accounts_used.append(base_username)
                if profile_fields := _optional_profile_fields_from_row(merged_row):
                    upsert_student_profile(session, student_id, profile_fields)

            add_academic_record(session, student_id, _academic_record_from_row(norm_row))
            records_imported += 1
        except Exception as exc:
            label = str(merged_row.get("student_username", f"row {index + 2}"))
            row_errors.append(f"{label}: {exc}")

    return {
        "total_rows": total_rows,
        "records_imported": records_imported,
        "students_created": len(created_accounts),
        "created_accounts": created_accounts,
        "existing_accounts_used": existing_accounts_used,
        "row_errors": row_errors,
    }


def bulk_insert_academic_records(session, csv_frame: pd.DataFrame) -> dict[str, Any]:
    csv_frame = normalize_academic_csv_frame(csv_frame.copy())
    required_columns = set(ACADEMIC_DB_COLUMNS)
    missing_columns = required_columns.difference(csv_frame.columns)
    if missing_columns:
        friendly_missing = [DB_TO_SCHOOL_CSV_HEADER.get(col, col) for col in sorted(missing_columns)]
        raise ValueError(f"Missing required columns: {', '.join(friendly_missing)}")

    user_rows = session.execute(select(User.id, User.username).where(User.role == "student")).all()
    username_to_id = {row.username: row.id for row in user_rows}
    inserted_count = 0
    skipped_usernames: list[str] = []

    for row in csv_frame.to_dict(orient="records"):
        username = str(row["student_username"]).strip()
        student_id = username_to_id.get(username)
        if not student_id:
            skipped_usernames.append(username)
            continue
        add_academic_record(session, student_id=student_id, record_data=_academic_record_from_row(row))
        inserted_count += 1

    return {
        "inserted": inserted_count,
        "skipped": len(skipped_usernames),
        "skipped_usernames": skipped_usernames,
    }


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

from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import aliased

from src.auth.hashing import hash_password
from src.services.student_credentials import (
    allocate_unique_username,
    build_login_password,
    build_student_email,
    import_row_identity_key,
    login_username_base_for_import,
    normalize_full_name_key,
    normalize_student_slug,
    resolve_student_name,
)
from src.utils.admin_context import student_grade_scope_filters
from config.school_context import (
    ACADEMIC_CSV_ALIASES,
    ACADEMIC_DB_COLUMNS,
    ACADEMIC_RECORD_DB_COLUMNS,
    DB_TO_SCHOOL_CSV_HEADER,
    SCHOOL_ACADEMIC_CSV_COLUMNS,
    format_class,
)


def _format_class_label(grade: int | None) -> str:
    if grade is None:
        return "—"
    return format_class(int(grade))
from src.utils.activity import ACTIVITY_BY_UNKNOWN, resolve_actor_name
from src.utils.datetime_ist import format_datetime_ist, now_ist
from src.db.models import (
    AcademicRecord,
    CareerGuidanceSnapshot,
    CareerRecommendation,
    DropoutPrediction,
    PsychometricAttempt,
    StudentProfile,
    User,
)
from src.services.intervention_service import list_interventions_for_student, suggested_priority_intensity


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
        "updated_at": format_datetime_ist(profile.updated_at),
        "activity_by": resolve_actor_name(session, profile.updated_by_user_id)
        if profile.updated_by_user_id
        else ACTIVITY_BY_UNKNOWN,
    }


def upsert_student_profile(
    session,
    user_id: int,
    profile_data: dict[str, Any],
    *,
    updated_by_user_id: int | None = None,
) -> StudentProfile:
    profile = get_student_profile(session, user_id)
    if not profile:
        profile = StudentProfile(user_id=user_id)
        session.add(profile)

    if updated_by_user_id is not None:
        profile.updated_by_user_id = updated_by_user_id

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
    upsert_student_profile(
        session,
        student.id,
        profile_data,
        updated_by_user_id=created_by_admin_id,
    )
    return student


def get_student_in_admin_scope(
    session,
    student_id: int,
    *,
    assigned_grade: int | None = None,
    created_by_admin_id: int | None = None,
) -> User | None:
    """Return the student if they exist and fall within the admin's cohort scope."""
    filters = [User.id == student_id, User.role == "student", User.is_active.is_(True)]
    if created_by_admin_id is not None:
        filters.append(User.created_by_admin_id == created_by_admin_id)
    elif assigned_grade is not None:
        filters.extend(student_grade_scope_filters(session, assigned_grade))

    return session.scalar(select(User).where(*filters))


def list_students(
    session,
    search_term: str = "",
    limit: int = 100,
    assigned_grade: int | None = None,
    created_by_admin_id: int | None = None,
) -> list[dict[str, Any]]:
    filters = [User.role == "student"]
    if created_by_admin_id is not None:
        filters.append(User.created_by_admin_id == created_by_admin_id)
    elif assigned_grade is not None:
        filters.extend(student_grade_scope_filters(session, assigned_grade))

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
            "class": _format_class_label(row.semester),
        }
        for row in rows
    ]


def list_student_options(
    session,
    assigned_grade: int | None = None,
    created_by_admin_id: int | None = None,
) -> list[tuple[int, str]]:
    filters = [User.role == "student"]
    if created_by_admin_id is not None:
        rows = session.execute(
            select(User.id, User.full_name)
            .where(*filters, User.created_by_admin_id == created_by_admin_id)
            .order_by(User.full_name.asc())
        ).all()
        return [(row.id, row.full_name) for row in rows]
    if assigned_grade is not None:
        query = (
            select(User.id, User.full_name)
            .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
            .where(*filters, *student_grade_scope_filters(session, assigned_grade))
            .order_by(User.full_name.asc())
        )
        rows = session.execute(query).all()
        return [(row.id, row.full_name) for row in rows]
    rows = session.execute(
        select(User.id, User.full_name).where(*filters).order_by(User.full_name.asc())
    ).all()
    return [(row.id, row.full_name) for row in rows]


def add_academic_record(
    session,
    student_id: int,
    record_data: dict[str, Any],
    *,
    recorded_by_user_id: int | None = None,
) -> AcademicRecord:
    record = AcademicRecord(
        student_id=student_id,
        recorded_by_user_id=recorded_by_user_id,
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


def list_recent_academic_records(
    session,
    limit: int = 50,
    assigned_grade: int | None = None,
    created_by_admin_id: int | None = None,
) -> list[dict[str, Any]]:
    Actor = aliased(User)
    stmt = (
        select(
            User.full_name,
            AcademicRecord.attendance_percentage,
            AcademicRecord.cgpa,
            AcademicRecord.backlog_count,
            AcademicRecord.recorded_at,
            Actor.full_name.label("actor_full_name"),
            Actor.username.label("actor_username"),
        )
        .join(AcademicRecord, AcademicRecord.student_id == User.id)
        .outerjoin(Actor, Actor.id == AcademicRecord.recorded_by_user_id)
        .where(User.role == "student")
    )
    if created_by_admin_id is not None:
        stmt = stmt.where(User.created_by_admin_id == created_by_admin_id)
    elif assigned_grade is not None:
        stmt = stmt.outerjoin(StudentProfile, StudentProfile.user_id == User.id).where(
            *student_grade_scope_filters(session, assigned_grade)
        )
    rows = session.execute(stmt.order_by(desc(AcademicRecord.recorded_at)).limit(limit)).all()
    return [
        {
            "student_name": row.full_name,
            "attendance_percentage": row.attendance_percentage,
            "overall_marks_pct": row.cgpa,
            "subjects_below_passing": row.backlog_count,
            "recorded_at": format_datetime_ist(row.recorded_at),
            "activity_by": row.actor_full_name or row.actor_username or ACTIVITY_BY_UNKNOWN,
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
            "class": _format_class_label(row.semester),
            "attendance_percentage": row.attendance_percentage,
            "overall_marks_pct": row.cgpa,
            "subjects_below_passing": row.backlog_count,
            "recorded_at": format_datetime_ist(row.recorded_at),
        }
        for row in rows
    ]


def academic_record_summary(
    session,
    assigned_grade: int | None = None,
    created_by_admin_id: int | None = None,
) -> dict[str, int]:
    if assigned_grade is None and created_by_admin_id is None:
        return {
            "students_with_records": session.scalar(
                select(func.count(func.distinct(AcademicRecord.student_id))).select_from(AcademicRecord)
            )
            or 0,
            "total_records": session.scalar(select(func.count()).select_from(AcademicRecord)) or 0,
        }

    if created_by_admin_id is not None:
        students_with_records = (
            session.scalar(
                select(func.count(func.distinct(AcademicRecord.student_id)))
                .select_from(AcademicRecord)
                .join(User, User.id == AcademicRecord.student_id)
                .where(User.created_by_admin_id == created_by_admin_id)
            )
            or 0
        )
        total_records = (
            session.scalar(
                select(func.count())
                .select_from(AcademicRecord)
                .join(User, User.id == AcademicRecord.student_id)
                .where(User.created_by_admin_id == created_by_admin_id)
            )
            or 0
        )
    else:
        grade_filters = student_grade_scope_filters(session, assigned_grade)
        students_with_records = (
            session.scalar(
                select(func.count(func.distinct(AcademicRecord.student_id)))
                .select_from(AcademicRecord)
                .join(User, User.id == AcademicRecord.student_id)
                .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
                .where(*grade_filters)
            )
            or 0
        )
        total_records = (
            session.scalar(
                select(func.count())
                .select_from(AcademicRecord)
                .join(User, User.id == AcademicRecord.student_id)
                .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
                .where(*grade_filters)
            )
            or 0
        )
    return {
        "students_with_records": students_with_records,
        "total_records": total_records,
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
    from src.services.career_recommendation_service import get_student_career_payload

    career_payload = get_student_career_payload(session, user_id)

    latest_assessment = None
    if latest_assessment_row:
        latest_assessment = {
            "summary": latest_assessment_row.summary,
            "top_codes": latest_assessment_row.top_codes,
        }

    recommendations = career_payload["recommendations"][:5]

    return {
        "profile": profile,
        "latest_assessment": latest_assessment,
        "recommendations": recommendations,
        "career_guidance": career_payload,
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
            "recorded_at": format_datetime_ist(latest_record.recorded_at),
            "activity_by": resolve_actor_name(session, latest_record.recorded_by_user_id),
        },
        "latest_prediction": None
        if not latest_prediction
        else {
            "risk_score": round(latest_prediction.risk_score * 100, 1),
            "risk_level": latest_prediction.risk_level,
            "top_factors": latest_prediction.top_factors,
            "predicted_at": format_datetime_ist(latest_prediction.predicted_at),
            "activity_by": resolve_actor_name(session, latest_prediction.predicted_by_user_id),
        },
        "latest_psychometric": None
        if not latest_attempt
        else {
            "top_codes": latest_attempt.top_codes,
            "summary": latest_attempt.summary,
            "submitted_at": format_datetime_ist(latest_attempt.submitted_at),
            "activity_by": user.full_name or user.username,
        },
        "recommendation_count": recommendation_count,
        "guidance_history_count": session.scalar(
            select(func.count())
            .select_from(CareerGuidanceSnapshot)
            .where(CareerGuidanceSnapshot.student_id == student_id)
        )
        or 0,
        "interventions": list_interventions_for_student(session, student_id),
        "intervention_suggested": suggested_priority_intensity(
            latest_prediction.risk_level if latest_prediction else None
        ),
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


def _optional_profile_fields_from_row(
    row: dict[str, Any],
    *,
    default_grade: int | None = None,
) -> dict[str, Any]:
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
    elif default_grade is not None:
        profile["semester"] = int(default_grade)
    return profile


def _get_or_create_student_for_import(
    session,
    row: dict[str, Any],
    admin_user_id: int,
    login_to_student_id: dict[str, int],
    import_batch_cache: dict[str, int],
    *,
    default_grade: int | None = None,
) -> tuple[int, dict[str, str] | None]:
    """Return student id and credential payload when a new account is created."""
    first, last, full_name = resolve_student_name(row)
    csv_slug = normalize_student_slug(row.get("student_username"))
    import_key = import_row_identity_key(row)
    login_base = login_username_base_for_import(row, first, last)

    student_id = import_batch_cache.get(import_key)
    if not student_id and csv_slug:
        student_id = login_to_student_id.get(csv_slug)
    if not student_id:
        student_id = login_to_student_id.get(login_base)

    profile_kwargs = {"default_grade": default_grade}

    if student_id:
        import_batch_cache[import_key] = student_id
        if csv_slug:
            import_batch_cache[csv_slug] = student_id
        if profile_fields := _optional_profile_fields_from_row(row, **profile_kwargs):
            upsert_student_profile(session, student_id, profile_fields)
        return student_id, None

    login_username = allocate_unique_username(session, login_base)
    password = build_login_password(login_username)
    email = build_student_email(login_username)
    if username_or_email_exists(session, login_username, email):
        email = f"{login_username}.{admin_user_id}@students.local"

    profile_data = _optional_profile_fields_from_row(row, **profile_kwargs)
    student = create_student_user(
        session,
        username=login_username,
        full_name=full_name,
        email=email,
        password=password,
        profile_data=profile_data,
        created_by_admin_id=admin_user_id,
    )
    if not profile_data:
        upsert_student_profile(session, student.id, {})

    student_id = student.id
    login_to_student_id[login_username] = student_id
    import_batch_cache[import_key] = student_id
    if csv_slug:
        import_batch_cache[csv_slug] = student_id
        login_to_student_id[csv_slug] = student_id

    credentials = {
        "full_name": full_name,
        "username": login_username,
        "password": password,
        "csv_label": csv_slug or f"{first}_{last}",
    }
    return student_id, credentials


def _find_student_id_by_full_name(session, name_key: str) -> int | None:
    rows = session.execute(select(User.id, User.full_name).where(User.role == "student")).all()
    for user_id, full_name in rows:
        if normalize_full_name_key(full_name) == name_key:
            return user_id
    return None


def _import_row_matches_existing_student(
    merged_row: dict[str, Any],
    login_to_student_id: dict[str, int],
    import_batch_cache: dict[str, int],
) -> bool:
    first, last, _ = resolve_student_name(merged_row)
    import_key = import_row_identity_key(merged_row)
    csv_slug = normalize_student_slug(merged_row.get("student_username"))
    login_base = login_username_base_for_import(merged_row, first, last)
    if import_batch_cache.get(import_key):
        return True
    if csv_slug and login_to_student_id.get(csv_slug):
        return True
    return bool(login_to_student_id.get(login_base))


def bulk_import_students_from_csv(
    session,
    csv_frame: pd.DataFrame,
    admin_user_id: int,
) -> dict[str, Any]:
    """Create a student account for every row, then save academic data (linked to admin)."""
    from src.utils.file_upload import prepare_import_dataframe

    prepared = prepare_import_dataframe(csv_frame)
    total_rows = len(prepared)
    if total_rows == 0:
        raise ValueError("The file has no data rows to import.")

    normalized = normalize_academic_csv_frame(prepared.copy())
    required_columns = set(ACADEMIC_RECORD_DB_COLUMNS)
    missing_columns = required_columns.difference(normalized.columns)
    if missing_columns:
        friendly_missing = [DB_TO_SCHOOL_CSV_HEADER.get(col, col) for col in sorted(missing_columns)]
        raise ValueError(f"Missing required columns: {', '.join(friendly_missing)}")

    admin = session.get(User, admin_user_id)
    default_grade = int(admin.assigned_grade) if admin and admin.assigned_grade is not None else None

    login_to_student_id = {
        row.username: row.id
        for row in session.execute(select(User.username, User.id).where(User.role == "student")).all()
    }
    import_batch_cache: dict[str, int] = {}

    created_accounts: list[dict[str, str]] = []
    existing_accounts_used: list[str] = []
    skipped_duplicate_names: list[str] = []
    names_seen_in_file: set[str] = set()
    records_imported = 0
    row_errors: list[str] = []

    prepared_rows = prepared.to_dict(orient="records")
    normalized_rows = normalized.to_dict(orient="records")

    for index in range(total_rows):
        merged_row = {**prepared_rows[index], **normalized_rows[index]}
        label = str(merged_row.get("student_username") or f"row {index + 2}")
        try:
            _, _, full_name = resolve_student_name(merged_row)
            name_key = normalize_full_name_key(full_name)

            if name_key in names_seen_in_file:
                skipped_duplicate_names.append(
                    f"{label}: duplicate name «{full_name}» — only the first row in the file is "
                    "imported; create the others manually under Student Management."
                )
                continue

            if not _import_row_matches_existing_student(
                merged_row, login_to_student_id, import_batch_cache
            ):
                existing_id = _find_student_id_by_full_name(session, name_key)
                if existing_id is not None:
                    skipped_duplicate_names.append(
                        f"{label}: a student named «{full_name}» already exists — skipped to avoid "
                        "duplicate accounts; add academic data manually or use their existing login slug."
                    )
                    continue

            student_id, credentials = _get_or_create_student_for_import(
                session,
                merged_row,
                admin_user_id,
                login_to_student_id,
                import_batch_cache,
                default_grade=default_grade,
            )
            if credentials:
                created_accounts.append(credentials)
            else:
                existing_accounts_used.append(label)

            add_academic_record(
                session,
                student_id,
                _academic_record_from_row(normalized_rows[index]),
                recorded_by_user_id=admin_user_id,
            )
            names_seen_in_file.add(name_key)
            records_imported += 1
        except Exception as exc:
            row_errors.append(f"{label}: {exc}")

    session.flush()
    imported_at = format_datetime_ist(now_ist())
    activity_by = (
        (admin.full_name or admin.username)
        if admin
        else resolve_actor_name(session, admin_user_id)
    )
    return {
        "total_rows": total_rows,
        "records_imported": records_imported,
        "students_created": len(created_accounts),
        "created_accounts": created_accounts,
        "existing_accounts_used": existing_accounts_used,
        "skipped_duplicate_names": skipped_duplicate_names,
        "row_errors": row_errors,
        "imported_at": imported_at,
        "activity_by": activity_by,
    }


def bulk_insert_academic_records(session, csv_frame: pd.DataFrame, admin_user_id: int) -> dict[str, Any]:
    """Legacy name — always creates student accounts via bulk_import_students_from_csv."""
    result = bulk_import_students_from_csv(session, csv_frame, admin_user_id=admin_user_id)
    return {
        "inserted": result["records_imported"],
        "skipped": len(result["row_errors"]),
        "skipped_usernames": result["row_errors"],
        **result,
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

from __future__ import annotations

from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import aliased

from config.school_context import income_band_for_dropout_model
from src.db.models import AcademicRecord, DropoutPrediction, StudentProfile, User
from src.utils.activity import ACTIVITY_BY_UNKNOWN
from src.utils.admin_context import student_grade_scope_filters
from src.utils.datetime_ist import format_datetime_ist

EXCLUDED_STUDENT_NAME = "Rahul Verma"


def train_dropout_model() -> dict:
    from src.ml.train_dropout import train_and_save_dropout_model

    return train_and_save_dropout_model()


def get_dropout_model_status() -> dict[str, Any]:
    from src.ml.predict_dropout import load_model_bundle, model_exists

    if not model_exists():
        return {"available": False}

    _, metadata = load_model_bundle()
    return {"available": True, **metadata}


def build_prediction_candidates(session) -> list[dict[str, Any]]:
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
        select(User, StudentProfile, AcademicRecord)
        .join(latest_record_subquery, latest_record_subquery.c.student_id == User.id)
        .join(AcademicRecord, AcademicRecord.id == latest_record_subquery.c.id)
        .outerjoin(StudentProfile, StudentProfile.user_id == User.id)
        .where(
            User.role == "student",
            latest_record_subquery.c.record_rank == 1,
            User.full_name != EXCLUDED_STUDENT_NAME,
        )
        .order_by(User.full_name.asc())
    ).all()

    candidates = []
    for user, profile, record in rows:
        candidates.append(
            {
                "student_id": user.id,
                "student_name": user.full_name,
                "department": profile.department if profile else None,
                "attendance_percentage": record.attendance_percentage,
                "cgpa": record.cgpa,
                "internal_marks": record.internal_marks,
                "backlog_count": record.backlog_count,
                "fee_pending": record.fee_pending,
                "scholarship_status": record.scholarship_status,
                "extracurricular_participation": record.extracurricular_participation,
                "disciplinary_issues": record.disciplinary_issues,
                "engagement_score": record.engagement_score,
                "stress_level": record.stress_level,
                "age": profile.age if profile else None,
                "semester": profile.semester if profile else None,
                "family_income_band": profile.family_income_band if profile else None,
                "parental_education": profile.parental_education if profile else None,
                "travel_distance_km": profile.travel_distance_km if profile else None,
                "internet_access": profile.internet_access if profile else None,
                "latest_recorded_at": record.recorded_at,
            }
        )
    return candidates


def run_predictions_for_latest_records(
    session,
    *,
    predicted_by_user_id: int | None = None,
) -> list[dict[str, Any]]:
    from src.ml.predict_dropout import predict_dropout_batch

    candidates = build_prediction_candidates(session)
    if not candidates:
        return []
    feature_keys = {
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
        "age",
        "semester",
        "family_income_band",
        "parental_education",
        "travel_distance_km",
        "internet_access",
        "department",
    }
    prediction_inputs = []
    for candidate in candidates:
        row = {key: candidate[key] for key in feature_keys if key in candidate}
        row["family_income_band"] = income_band_for_dropout_model(candidate.get("family_income_band"))
        prediction_inputs.append(row)
    predictions = predict_dropout_batch(prediction_inputs)
    results = []
    for candidate, prediction in zip(candidates, predictions):
        explanation = build_explanation(candidate, prediction["risk_level"])
        prediction_row = DropoutPrediction(
            student_id=candidate["student_id"],
            risk_score=prediction["risk_score"],
            risk_level=prediction["risk_level"],
            top_factors=explanation,
            predicted_by_user_id=predicted_by_user_id,
        )
        session.add(prediction_row)
        results.append(
            {
                "student_name": candidate["student_name"],
                "school_or_stream": candidate["department"] or "-",
                "risk_score": round(prediction["risk_score"] * 100, 1),
                "risk_level": prediction["risk_level"],
                "top_factors": explanation,
                "recorded_at": format_datetime_ist(candidate["latest_recorded_at"]),
            }
        )
    session.flush()
    return results


def list_recent_predictions(session, limit: int = 50) -> list[dict[str, Any]]:
    Actor = aliased(User)
    rows = session.execute(
        select(
            User.full_name,
            User.username,
            DropoutPrediction.risk_score,
            DropoutPrediction.risk_level,
            DropoutPrediction.top_factors,
            DropoutPrediction.predicted_at,
            Actor.full_name.label("actor_full_name"),
            Actor.username.label("actor_username"),
        )
        .join(DropoutPrediction, DropoutPrediction.student_id == User.id)
        .outerjoin(Actor, Actor.id == DropoutPrediction.predicted_by_user_id)
        .order_by(desc(DropoutPrediction.predicted_at))
        .limit(limit)
    ).all()
    return [
        {
            "student_name": row.full_name,
            "username": row.username,
            "risk_score": round(row.risk_score * 100, 1),
            "risk_level": row.risk_level,
            "top_factors": row.top_factors,
            "predicted_at": format_datetime_ist(row.predicted_at),
            "activity_by": row.actor_full_name or row.actor_username or ACTIVITY_BY_UNKNOWN,
        }
        for row in rows
    ]


def list_latest_predictions_per_student(
    session,
    limit: int = 100,
    assigned_grade: int | None = None,
    created_by_admin_id: int | None = None,
) -> list[dict[str, Any]]:
    latest_prediction_subquery = (
        select(
            DropoutPrediction.student_id,
            DropoutPrediction.id,
            func.row_number()
            .over(partition_by=DropoutPrediction.student_id, order_by=DropoutPrediction.predicted_at.desc())
            .label("prediction_rank"),
        )
        .subquery()
    )

    Actor = aliased(User)
    stmt = (
        select(
            User.id,
            User.full_name,
            User.username,
            DropoutPrediction.risk_score,
            DropoutPrediction.risk_level,
            DropoutPrediction.top_factors,
            DropoutPrediction.predicted_at,
            Actor.full_name.label("actor_full_name"),
            Actor.username.label("actor_username"),
        )
        .join(latest_prediction_subquery, latest_prediction_subquery.c.student_id == User.id)
        .join(DropoutPrediction, DropoutPrediction.id == latest_prediction_subquery.c.id)
        .outerjoin(Actor, Actor.id == DropoutPrediction.predicted_by_user_id)
        .where(
            User.role == "student",
            latest_prediction_subquery.c.prediction_rank == 1,
            User.full_name != EXCLUDED_STUDENT_NAME,
        )
    )
    if created_by_admin_id is not None:
        stmt = stmt.where(User.created_by_admin_id == created_by_admin_id)
    elif assigned_grade is not None:
        stmt = stmt.outerjoin(StudentProfile, StudentProfile.user_id == User.id).where(
            *student_grade_scope_filters(session, assigned_grade)
        )
    rows = session.execute(stmt.order_by(desc(DropoutPrediction.risk_score)).limit(limit)).all()

    return [
        {
            "student_id": row.id,
            "student_name": row.full_name,
            "username": row.username,
            "risk_score": round(row.risk_score * 100, 1),
            "risk_level": row.risk_level,
            "top_factors": row.top_factors,
            "predicted_at": format_datetime_ist(row.predicted_at),
            "activity_by": row.actor_full_name or row.actor_username or ACTIVITY_BY_UNKNOWN,
        }
        for row in rows
    ]


def build_explanation(candidate: dict[str, Any], risk_level: str) -> str:
    factors: list[str] = []
    if (candidate.get("attendance_percentage") or 0) < 70:
        factors.append("low attendance")
    if (candidate.get("cgpa") or 0) < 50:
        factors.append("low overall marks")
    if (candidate.get("backlog_count") or 0) >= 2:
        factors.append("multiple subjects below passing level")
    if candidate.get("fee_pending") == "Yes":
        factors.append("pending fees")
    if (candidate.get("engagement_score") or 10) < 5.0:
        factors.append("low engagement")
    if (candidate.get("stress_level") or 0) > 7.0:
        factors.append("high stress")
    if candidate.get("internet_access") in {"No", "Limited"}:
        factors.append("limited internet access")

    if not factors:
        if risk_level == "Low":
            return "Steady attendance, acceptable marks, and healthy engagement lower the risk of leaving school early."
        return "Mixed school indicators suggest moderate risk, though no single severe trigger stands out."
    return "Key factors: " + ", ".join(factors[:4]) + "."

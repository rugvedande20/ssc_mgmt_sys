from __future__ import annotations

from typing import Any

from sqlalchemy import desc, func, select

from src.db.models import AcademicRecord, DropoutPrediction, StudentProfile, User


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
        .where(User.role == "student", latest_record_subquery.c.record_rank == 1)
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


def run_predictions_for_latest_records(session) -> list[dict[str, Any]]:
    from src.ml.predict_dropout import predict_dropout_batch

    candidates = build_prediction_candidates(session)
    if not candidates:
        return []
    prediction_inputs = [
        {
            key: value
            for key, value in candidate.items()
            if key
            in {
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
        }
        for candidate in candidates
    ]
    predictions = predict_dropout_batch(prediction_inputs)
    results = []
    for candidate, prediction in zip(candidates, predictions):
        explanation = build_explanation(candidate, prediction["risk_level"])
        prediction_row = DropoutPrediction(
            student_id=candidate["student_id"],
            risk_score=prediction["risk_score"],
            risk_level=prediction["risk_level"],
            top_factors=explanation,
        )
        session.add(prediction_row)
        results.append(
            {
                "student_name": candidate["student_name"],
                "school_or_stream": candidate["department"] or "-",
                "risk_score": round(prediction["risk_score"] * 100, 1),
                "risk_level": prediction["risk_level"],
                "top_factors": explanation,
                "recorded_at": candidate["latest_recorded_at"].strftime("%Y-%m-%d %H:%M"),
            }
        )
    session.flush()
    return results


def list_recent_predictions(session, limit: int = 50) -> list[dict[str, Any]]:
    rows = session.execute(
        select(User.full_name, User.username, DropoutPrediction.risk_score, DropoutPrediction.risk_level, DropoutPrediction.top_factors, DropoutPrediction.predicted_at)
        .join(DropoutPrediction, DropoutPrediction.student_id == User.id)
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
            "predicted_at": row.predicted_at.strftime("%Y-%m-%d %H:%M"),
        }
        for row in rows
    ]


def list_latest_predictions_per_student(session, limit: int = 100) -> list[dict[str, Any]]:
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

    rows = session.execute(
        select(
            User.id,
            User.full_name,
            User.username,
            DropoutPrediction.risk_score,
            DropoutPrediction.risk_level,
            DropoutPrediction.top_factors,
            DropoutPrediction.predicted_at,
        )
        .join(latest_prediction_subquery, latest_prediction_subquery.c.student_id == User.id)
        .join(DropoutPrediction, DropoutPrediction.id == latest_prediction_subquery.c.id)
        .where(User.role == "student", latest_prediction_subquery.c.prediction_rank == 1)
        .order_by(desc(DropoutPrediction.risk_score))
        .limit(limit)
    ).all()

    return [
        {
            "student_id": row.id,
            "student_name": row.full_name,
            "username": row.username,
            "risk_score": round(row.risk_score * 100, 1),
            "risk_level": row.risk_level,
            "top_factors": row.top_factors,
            "predicted_at": row.predicted_at.strftime("%Y-%m-%d %H:%M"),
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

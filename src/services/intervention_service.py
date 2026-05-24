from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import aliased

from config.constants import INTERVENTION_PRIORITIES, INTERVENTION_STATUSES
from src.db.models import DropoutPrediction, InterventionLog, StudentProfile, User
from src.utils.activity import ACTIVITY_BY_UNKNOWN, resolve_actor_name
from src.utils.admin_context import student_grade_scope_filters
from src.utils.datetime_ist import format_datetime_ist, now_ist

RISK_TO_INTERVENTION: dict[str, dict[str, str]] = {
    "High": {"priority": "High", "intensity": "High"},
    "Medium": {"priority": "Medium", "intensity": "Medium"},
    "Low": {"priority": "Low", "intensity": "Low"},
}


def suggested_priority_intensity(risk_level: str | None) -> dict[str, str]:
    return RISK_TO_INTERVENTION.get(risk_level or "", {"priority": "Medium", "intensity": "Medium"})


def _latest_prediction(session, student_id: int) -> DropoutPrediction | None:
    return session.scalar(
        select(DropoutPrediction)
        .where(DropoutPrediction.student_id == student_id)
        .order_by(desc(DropoutPrediction.predicted_at))
    )


def _intervention_row(
    row: InterventionLog,
    *,
    student_name: str | None = None,
    student_username: str | None = None,
    admin_name: str | None = None,
) -> dict[str, Any]:
    return {
        "id": row.id,
        "student_id": row.student_id,
        "student_name": student_name,
        "student_username": student_username,
        "intervention_type": row.intervention_type,
        "module": row.module,
        "priority": row.priority,
        "intensity": row.intensity,
        "risk_level_at_time": row.risk_level_at_time,
        "risk_score_at_time": round(row.risk_score_at_time * 100, 1) if row.risk_score_at_time is not None else None,
        "status": row.status,
        "action_taken": row.action_taken,
        "note": row.note,
        "scheduled_at": format_datetime_ist(row.scheduled_at) if row.scheduled_at else None,
        "completed_at": format_datetime_ist(row.completed_at) if row.completed_at else None,
        "created_at": format_datetime_ist(row.created_at),
        "activity_by": admin_name or ACTIVITY_BY_UNKNOWN,
    }


def create_intervention_log(
    session,
    *,
    student_id: int,
    admin_user_id: int,
    note: str,
    action_taken: str,
    intervention_type: str = "One-on-one counseling",
    module: str | None = None,
    priority: str = "Medium",
    intensity: str = "Medium",
    status: str = "completed",
    scheduled_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> InterventionLog:
    if priority not in INTERVENTION_PRIORITIES:
        raise ValueError(f"Priority must be one of {INTERVENTION_PRIORITIES}.")
    if intensity not in INTERVENTION_PRIORITIES:
        raise ValueError(f"Intensity must be one of {INTERVENTION_PRIORITIES}.")
    if status not in INTERVENTION_STATUSES:
        raise ValueError(f"Status must be one of {INTERVENTION_STATUSES}.")

    prediction = _latest_prediction(session, student_id)
    row = InterventionLog(
        student_id=student_id,
        admin_user_id=admin_user_id,
        note=note.strip(),
        action_taken=action_taken.strip(),
        intervention_type=intervention_type,
        module=module,
        priority=priority,
        intensity=intensity,
        risk_level_at_time=prediction.risk_level if prediction else None,
        risk_score_at_time=prediction.risk_score if prediction else None,
        dropout_prediction_id=prediction.id if prediction else None,
        status=status,
        scheduled_at=scheduled_at,
        completed_at=completed_at or (now_ist() if status == "completed" else None),
    )
    session.add(row)
    session.flush()
    return row


def schedule_intervention(
    session,
    *,
    student_id: int,
    admin_user_id: int,
    scheduled_at: datetime,
    intervention_type: str = "One-on-one counseling",
    module: str | None = None,
    priority: str | None = None,
    intensity: str | None = None,
    note: str = "",
) -> InterventionLog:
    prediction = _latest_prediction(session, student_id)
    defaults = suggested_priority_intensity(prediction.risk_level if prediction else None)
    return create_intervention_log(
        session,
        student_id=student_id,
        admin_user_id=admin_user_id,
        note=note.strip() or "Session scheduled — details to be added after the meeting.",
        action_taken="Scheduled",
        intervention_type=intervention_type,
        module=module,
        priority=priority or defaults["priority"],
        intensity=intensity or defaults["intensity"],
        status="scheduled",
        scheduled_at=scheduled_at,
        completed_at=None,
    )


def complete_scheduled_intervention(
    session,
    intervention_id: int,
    *,
    note: str,
    action_taken: str,
) -> InterventionLog:
    row = session.get(InterventionLog, intervention_id)
    if not row:
        raise ValueError("Intervention not found.")
    if row.status != "scheduled":
        raise ValueError("Only scheduled interventions can be completed.")
    row.note = note.strip()
    row.action_taken = action_taken.strip()
    row.status = "completed"
    row.completed_at = now_ist()
    session.flush()
    return row


def cancel_intervention(session, intervention_id: int) -> InterventionLog:
    row = session.get(InterventionLog, intervention_id)
    if not row:
        raise ValueError("Intervention not found.")
    if row.status != "scheduled":
        raise ValueError("Only scheduled interventions can be cancelled.")
    row.status = "cancelled"
    session.flush()
    return row


def list_interventions_for_student(session, student_id: int, *, limit: int = 50) -> list[dict[str, Any]]:
    Admin = aliased(User)
    rows = session.execute(
        select(InterventionLog, Admin.full_name, Admin.username)
        .outerjoin(Admin, Admin.id == InterventionLog.admin_user_id)
        .where(InterventionLog.student_id == student_id)
        .order_by(desc(InterventionLog.created_at))
        .limit(limit)
    ).all()
    return [
        _intervention_row(
            log,
            admin_name=admin_name or admin_username or None,
        )
        for log, admin_name, admin_username in rows
    ]


def _scope_student_ids_stmt(session, *, assigned_grade: int | None = None, created_by_admin_id: int | None = None):
    stmt = select(User.id).where(User.role == "student")
    if created_by_admin_id is not None:
        stmt = stmt.where(User.created_by_admin_id == created_by_admin_id)
    elif assigned_grade is not None:
        stmt = stmt.outerjoin(StudentProfile, StudentProfile.user_id == User.id).where(
            *student_grade_scope_filters(session, assigned_grade)
        )
    return stmt


def list_interventions_for_scope(
    session,
    *,
    assigned_grade: int | None = None,
    created_by_admin_id: int | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    scoped_ids = _scope_student_ids_stmt(
        session,
        assigned_grade=assigned_grade,
        created_by_admin_id=created_by_admin_id,
    ).subquery()

    Student = aliased(User)
    Admin = aliased(User)
    stmt = (
        select(InterventionLog, Student.full_name, Student.username, Admin.full_name, Admin.username)
        .join(Student, Student.id == InterventionLog.student_id)
        .outerjoin(Admin, Admin.id == InterventionLog.admin_user_id)
        .where(InterventionLog.student_id.in_(select(scoped_ids.c.id)))
        .order_by(desc(InterventionLog.created_at))
        .limit(limit)
    )
    if status:
        stmt = stmt.where(InterventionLog.status == status)

    rows = session.execute(stmt).all()
    return [
        _intervention_row(
            log,
            student_name=student_name,
            student_username=student_username,
            admin_name=admin_name or admin_username or None,
        )
        for log, student_name, student_username, admin_name, admin_username in rows
    ]


def list_at_risk_students_for_intervention(
    session,
    *,
    assigned_grade: int | None = None,
    created_by_admin_id: int | None = None,
    risk_levels: tuple[str, ...] = ("High", "Medium"),
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Students with latest prediction in given risk bands, ordered High first."""
    from src.services.dropout_service import list_latest_predictions_per_student

    predictions = list_latest_predictions_per_student(
        session,
        limit=limit,
        assigned_grade=assigned_grade,
        created_by_admin_id=created_by_admin_id,
    )
    level_set = set(risk_levels)
    filtered = [row for row in predictions if row.get("risk_level") in level_set]

    student_ids = [row["student_id"] for row in filtered]
    if not student_ids:
        return []

    scheduled_counts = dict(
        session.execute(
            select(InterventionLog.student_id, func.count())
            .where(
                InterventionLog.student_id.in_(student_ids),
                InterventionLog.status == "scheduled",
            )
            .group_by(InterventionLog.student_id)
        ).all()
    )
    completed_counts = dict(
        session.execute(
            select(InterventionLog.student_id, func.count())
            .where(
                InterventionLog.student_id.in_(student_ids),
                InterventionLog.status == "completed",
            )
            .group_by(InterventionLog.student_id)
        ).all()
    )

    result = []
    for row in filtered:
        sid = row["student_id"]
        defaults = suggested_priority_intensity(row.get("risk_level"))
        result.append(
            {
                **row,
                "suggested_priority": defaults["priority"],
                "suggested_intensity": defaults["intensity"],
                "scheduled_count": scheduled_counts.get(sid, 0),
                "completed_count": completed_counts.get(sid, 0),
            }
        )
    return result


def get_intervention_summary_for_scope(
    session,
    *,
    assigned_grade: int | None = None,
    created_by_admin_id: int | None = None,
) -> dict[str, int]:
    scoped_ids = _scope_student_ids_stmt(
        session,
        assigned_grade=assigned_grade,
        created_by_admin_id=created_by_admin_id,
    ).subquery()

    base = select(func.count()).select_from(InterventionLog).where(
        InterventionLog.student_id.in_(select(scoped_ids.c.id))
    )
    return {
        "scheduled": session.scalar(base.where(InterventionLog.status == "scheduled")) or 0,
        "completed": session.scalar(base.where(InterventionLog.status == "completed")) or 0,
        "cancelled": session.scalar(base.where(InterventionLog.status == "cancelled")) or 0,
    }


def get_student_interventions_payload(session, student_id: int) -> dict[str, Any]:
    prediction = _latest_prediction(session, student_id)
    interventions = list_interventions_for_student(session, student_id)
    scheduled = [row for row in interventions if row["status"] == "scheduled"]
    completed = [row for row in interventions if row["status"] == "completed"]

    latest_prediction = None
    if prediction:
        latest_prediction = {
            "risk_score": round(prediction.risk_score * 100, 1),
            "risk_level": prediction.risk_level,
            "top_factors": prediction.top_factors,
            "predicted_at": format_datetime_ist(prediction.predicted_at),
        }

    return {
        "latest_prediction": latest_prediction,
        "suggested": suggested_priority_intensity(prediction.risk_level if prediction else None),
        "scheduled": scheduled,
        "completed": completed,
        "all": interventions,
    }

from __future__ import annotations

import json

from src.utils.datetime_ist import format_datetime_ist, now_ist
from typing import Any

from sqlalchemy import desc, func, select

from config.constants import RIASEC_TYPES, TARGET_GRADE_MAX
from src.db.models import AcademicRecord, CareerGuidanceSnapshot, CareerRecommendation, PsychometricAttempt
from src.ml.career_matcher import build_class_10_report, match_careers_for_student
from src.services.student_service import get_student_profile_payload
from src.utils.activity import ACTIVITY_BY_UNKNOWN, resolve_actor_name


def _parse_riasec_scores(raw: str) -> dict[str, float]:
    try:
        payload = json.loads(raw)
        return {key: float(payload.get(key, 0)) for key in RIASEC_TYPES}
    except (json.JSONDecodeError, TypeError, ValueError):
        return {key: 0.0 for key in RIASEC_TYPES}


def _academic_payload(record: AcademicRecord | None) -> dict[str, Any] | None:
    if not record:
        return None
    return {
        "attendance_percentage": record.attendance_percentage,
        "overall_marks_pct": record.cgpa,
        "latest_term_score_pct": record.internal_marks,
        "subjects_below_passing": record.backlog_count,
        "engagement_score": record.engagement_score,
        "stress_level": record.stress_level,
        "cgpa": record.cgpa,
        "backlog_count": record.backlog_count,
    }


def _academic_trend(session, student_id: int) -> dict[str, Any]:
    rows = session.execute(
        select(AcademicRecord)
        .where(AcademicRecord.student_id == student_id)
        .order_by(desc(AcademicRecord.recorded_at))
        .limit(6)
    ).scalars().all()
    if len(rows) < 2:
        return {}
    marks = [r.cgpa for r in rows if r.cgpa is not None]
    attendance = [r.attendance_percentage for r in rows if r.attendance_percentage is not None]
    trend: dict[str, Any] = {}
    if len(marks) >= 2:
        trend["marks_trend"] = round(float(marks[0]) - float(marks[-1]), 2)
    if len(attendance) >= 2:
        trend["attendance_trend"] = round(float(attendance[0]) - float(attendance[-1]), 2)
    return trend


def get_latest_guidance_snapshot(session, student_id: int) -> CareerGuidanceSnapshot | None:
    return session.scalar(
        select(CareerGuidanceSnapshot)
        .where(CareerGuidanceSnapshot.student_id == student_id)
        .order_by(desc(CareerGuidanceSnapshot.generated_at))
    )


def list_guidance_history(session, student_id: int, limit: int = 8) -> list[dict[str, Any]]:
    rows = session.execute(
        select(CareerGuidanceSnapshot)
        .where(CareerGuidanceSnapshot.student_id == student_id)
        .order_by(desc(CareerGuidanceSnapshot.generated_at))
        .limit(limit)
    ).scalars().all()
    return [
        {
            "id": row.id,
            "phase": row.phase,
            "student_class": row.student_class,
            "summary": row.summary,
            "generated_at": format_datetime_ist(row.generated_at),
            "activity_by": resolve_actor_name(session, row.generated_by_user_id)
            if row.generated_by_user_id
            else ACTIVITY_BY_UNKNOWN,
        }
        for row in rows
    ]


def get_recommendations_for_snapshot(
    session, student_id: int, snapshot_id: int | None
) -> list[dict[str, Any]]:
    filters = [CareerRecommendation.student_id == student_id]
    if snapshot_id is not None:
        filters.append(CareerRecommendation.guidance_snapshot_id == snapshot_id)
    rows = session.execute(
        select(CareerRecommendation)
        .where(*filters)
        .order_by(CareerRecommendation.match_score.desc())
    ).scalars().all()
    if not rows and snapshot_id is not None:
        rows = session.execute(
            select(CareerRecommendation)
            .where(CareerRecommendation.student_id == student_id)
            .order_by(CareerRecommendation.match_score.desc())
            .limit(5)
        ).scalars().all()
    return [
        {
            "career_name": row.career_name,
            "match_score": row.match_score,
            "rationale": row.rationale,
            "skill_gap": row.skill_gap,
            "roadmap": row.roadmap,
            "certifications": row.certifications,
            "generated_at": format_datetime_ist(row.generated_at),
        }
        for row in rows
    ]


def generate_career_guidance(
    session,
    student_id: int,
    *,
    generated_by_user_id: int | None = None,
) -> dict[str, Any]:
    actor_id = generated_by_user_id if generated_by_user_id is not None else student_id
    profile = get_student_profile_payload(session, student_id)
    student_class = int(profile.get("semester")) if profile and profile.get("semester") else None

    latest_attempt = session.scalar(
        select(PsychometricAttempt)
        .where(PsychometricAttempt.student_id == student_id)
        .order_by(desc(PsychometricAttempt.submitted_at))
    )
    if not latest_attempt:
        raise ValueError("Student must complete the Interest Assessment before career guidance can be generated.")

    latest_record = session.scalar(
        select(AcademicRecord)
        .where(AcademicRecord.student_id == student_id)
        .order_by(desc(AcademicRecord.recorded_at))
    )

    psychometric_count = (
        session.scalar(
            select(func.count())
            .select_from(PsychometricAttempt)
            .where(PsychometricAttempt.student_id == student_id)
        )
        or 0
    )
    academic_count = (
        session.scalar(
            select(func.count()).select_from(AcademicRecord).where(AcademicRecord.student_id == student_id)
        )
        or 0
    )

    riasec_scores = _parse_riasec_scores(latest_attempt.riasec_scores)
    top_codes = [code.strip() for code in latest_attempt.top_codes.split(",") if code.strip()]

    matches, meta = match_careers_for_student(
        riasec_scores=riasec_scores,
        top_codes=top_codes,
        latest_academic=_academic_payload(latest_record),
        academic_trend=_academic_trend(session, student_id),
        profile=profile,
        student_class=student_class,
        limit=5,
    )

    is_class_10 = student_class is not None and student_class >= TARGET_GRADE_MAX
    phase = "class_10_report" if is_class_10 else "yearly_guidance"

    report: dict[str, Any] = {
        "phase": phase,
        "meta": meta,
        "top_matches": [{"career_name": m["career_name"], "match_score": m["match_score"]} for m in matches],
    }
    if is_class_10:
        report["class_10"] = build_class_10_report(
            profile=profile,
            matches=matches,
            meta=meta,
            academic_history_count=academic_count,
            psychometric_count=psychometric_count,
        )

    top_name = matches[0]["career_name"] if matches else "pathways"
    summary = (
        f"Future-oriented guidance for Class {student_class}: top match {top_name} "
        f"using interest assessment, academic history, and 5-year labour outlook."
        if student_class
        else f"Future-oriented guidance: top match {top_name} from interests, academics, and labour outlook."
    )

    snapshot = CareerGuidanceSnapshot(
        student_id=student_id,
        student_class=student_class,
        phase=phase,
        summary=summary,
        report_json=json.dumps(report),
        labour_horizon_years=int(meta.get("horizon_years", 5)),
        generated_at=now_ist(),
        generated_by_user_id=actor_id,
    )
    session.add(snapshot)
    session.flush()

    for match in matches:
        session.add(
            CareerRecommendation(
                student_id=student_id,
                guidance_snapshot_id=snapshot.id,
                career_name=match["career_name"],
                match_score=match["match_score"],
                rationale=match["rationale"],
                skill_gap=match["skill_gap"],
                roadmap=match["roadmap"],
                certifications=match["certifications"],
                generated_at=now_ist(),
            )
        )
    session.flush()

    return {
        "snapshot_id": snapshot.id,
        "phase": phase,
        "summary": summary,
        "report": report,
        "recommendations": get_recommendations_for_snapshot(session, student_id, snapshot.id),
        "generated_at": format_datetime_ist(snapshot.generated_at),
        "activity_by": resolve_actor_name(session, actor_id),
    }


def get_student_career_payload(session, student_id: int) -> dict[str, Any]:
    snapshot = get_latest_guidance_snapshot(session, student_id)
    recommendations = get_recommendations_for_snapshot(
        session, student_id, snapshot.id if snapshot else None
    )
    report = {}
    if snapshot:
        try:
            report = json.loads(snapshot.report_json)
        except json.JSONDecodeError:
            report = {}
    return {
        "snapshot": None
        if not snapshot
        else {
            "id": snapshot.id,
            "phase": snapshot.phase,
            "student_class": snapshot.student_class,
            "summary": snapshot.summary,
            "generated_at": format_datetime_ist(snapshot.generated_at),
            "activity_by": resolve_actor_name(session, snapshot.generated_by_user_id)
            if snapshot.generated_by_user_id
            else ACTIVITY_BY_UNKNOWN,
            "report": report,
        },
        "recommendations": recommendations,
        "history": list_guidance_history(session, student_id),
    }

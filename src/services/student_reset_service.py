"""Destructive maintenance: remove all student accounts and related data."""

from __future__ import annotations

from sqlalchemy import delete, func, select

from src.db.models import (
    AcademicRecord,
    CareerGuidanceSnapshot,
    CareerRecommendation,
    DropoutPrediction,
    InterventionLog,
    PasswordResetOtp,
    PsychometricAttempt,
    StudentProfile,
    User,
)

CLEAR_STUDENTS_CONFIRM_PHRASE = "CLEAR ALL STUDENTS"


def count_student_data(session) -> dict[str, int]:
    student_ids_subq = select(User.id).where(User.role == "student").scalar_subquery()
    return {
        "students": session.scalar(select(func.count()).select_from(User).where(User.role == "student")) or 0,
        "profiles": session.scalar(select(func.count()).select_from(StudentProfile)) or 0,
        "academic_records": session.scalar(select(func.count()).select_from(AcademicRecord)) or 0,
        "predictions": session.scalar(select(func.count()).select_from(DropoutPrediction)) or 0,
        "assessments": session.scalar(select(func.count()).select_from(PsychometricAttempt)) or 0,
        "career_snapshots": session.scalar(select(func.count()).select_from(CareerGuidanceSnapshot)) or 0,
        "career_recommendations": session.scalar(select(func.count()).select_from(CareerRecommendation)) or 0,
        "interventions": session.scalar(select(func.count()).select_from(InterventionLog)) or 0,
        "student_otps": session.scalar(
            select(func.count()).select_from(PasswordResetOtp).where(PasswordResetOtp.user_id.in_(student_ids_subq))
        )
        or 0,
    }


def clear_all_student_data(session) -> dict[str, int]:
    """
    Delete every student user and all linked records. Staff accounts are not modified.
  Returns counts of rows removed per table (approximate for bulk deletes).
    """
    before = count_student_data(session)
    if before["students"] == 0:
        return {**before, "removed_students": 0}

    student_ids = list(session.scalars(select(User.id).where(User.role == "student")).all())

    session.execute(delete(InterventionLog).where(InterventionLog.student_id.in_(student_ids)))
    session.execute(delete(CareerRecommendation).where(CareerRecommendation.student_id.in_(student_ids)))
    session.execute(delete(CareerGuidanceSnapshot).where(CareerGuidanceSnapshot.student_id.in_(student_ids)))
    session.execute(delete(PsychometricAttempt).where(PsychometricAttempt.student_id.in_(student_ids)))
    session.execute(delete(DropoutPrediction).where(DropoutPrediction.student_id.in_(student_ids)))
    session.execute(delete(AcademicRecord).where(AcademicRecord.student_id.in_(student_ids)))
    session.execute(delete(StudentProfile).where(StudentProfile.user_id.in_(student_ids)))
    session.execute(delete(PasswordResetOtp).where(PasswordResetOtp.user_id.in_(student_ids)))
    session.execute(delete(User).where(User.role == "student"))
    session.flush()

    return {
        **before,
        "removed_students": before["students"],
    }

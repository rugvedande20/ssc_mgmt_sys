from sqlalchemy import delete, select

from src.auth.hashing import hash_password
from src.db.models import (
    AcademicRecord,
    CareerGuidanceSnapshot,
    CareerRecommendation,
    DropoutPrediction,
    InterventionLog,
    PsychometricAttempt,
    StudentProfile,
    User,
)

LEGACY_DEMO_STUDENT_NAME = "Rahul Verma"


def remove_legacy_demo_student(session) -> None:
    user = session.scalar(
        select(User).where(User.role == "student", User.full_name == LEGACY_DEMO_STUDENT_NAME)
    )
    if not user:
        return

    student_id = user.id
    session.execute(delete(InterventionLog).where(InterventionLog.student_id == student_id))
    session.execute(delete(CareerRecommendation).where(CareerRecommendation.student_id == student_id))
    session.execute(delete(CareerGuidanceSnapshot).where(CareerGuidanceSnapshot.student_id == student_id))
    session.execute(delete(PsychometricAttempt).where(PsychometricAttempt.student_id == student_id))
    session.execute(delete(DropoutPrediction).where(DropoutPrediction.student_id == student_id))
    session.execute(delete(AcademicRecord).where(AcademicRecord.student_id == student_id))
    session.execute(delete(StudentProfile).where(StudentProfile.user_id == student_id))
    session.execute(delete(User).where(User.id == student_id))


def seed_demo_data(session) -> None:
    remove_legacy_demo_student(session)

    existing_admin = session.scalar(select(User).where(User.username == "admin"))
    if existing_admin:
        return

    admin = User(
        username="admin",
        full_name="Ananya Sharma",
        email="admin@demo.edu",
        password_hash=hash_password("Admin@123"),
        role="admin",
        is_active=True,
    )
    session.add(admin)

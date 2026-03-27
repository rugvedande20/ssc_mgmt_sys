from sqlalchemy import func, select

from src.db.models import AcademicRecord, CareerRecommendation, DropoutPrediction, PsychometricAttempt, User


def build_user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
    }


def get_dashboard_counts(session) -> dict:
    total_students = session.scalar(select(func.count()).select_from(User).where(User.role == "student")) or 0
    total_admins = session.scalar(select(func.count()).select_from(User).where(User.role == "admin")) or 0
    total_predictions = session.scalar(select(func.count()).select_from(DropoutPrediction)) or 0
    total_assessments = session.scalar(select(func.count()).select_from(PsychometricAttempt)) or 0
    total_recommendations = session.scalar(select(func.count()).select_from(CareerRecommendation)) or 0
    academic_records = session.scalar(select(func.count()).select_from(AcademicRecord)) or 0
    return {
        "total_students": total_students,
        "total_admins": total_admins,
        "total_predictions": total_predictions,
        "total_assessments": total_assessments,
        "total_recommendations": total_recommendations,
        "academic_records": academic_records,
    }

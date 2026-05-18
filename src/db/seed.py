import json

from sqlalchemy import select

from src.auth.hashing import hash_password
from src.db.models import AcademicRecord, CareerRecommendation, DropoutPrediction, PsychometricAttempt, StudentProfile, User


def seed_demo_data(session) -> None:
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
    student = User(
        username="student1",
        full_name="Rahul Verma",
        email="student1@demo.edu",
        password_hash=hash_password("Student@123"),
        role="student",
        is_active=True,
    )
    session.add_all([admin, student])
    session.flush()

    session.add(
        StudentProfile(
            user_id=student.id,
            age=14,
            gender="Male",
            department="Ryan International School (CBSE)",
            semester=8,
            family_income_band="Middle",
            parental_education="Graduate",
            travel_distance_km=4.0,
            internet_access="Yes",
            interests_summary="Science club, coding, cricket, and quiz competitions.",
            strengths_summary="Strong in Maths and Science; curious and consistent with homework.",
        )
    )

    session.add(
        AcademicRecord(
            student_id=student.id,
            attendance_percentage=88.0,
            cgpa=74.0,
            internal_marks=74.0,
            backlog_count=0,
            fee_pending="No",
            scholarship_status="No",
            extracurricular_participation="Yes",
            disciplinary_issues=0,
            engagement_score=7.8,
            stress_level=4.0,
        )
    )

    session.add(
        DropoutPrediction(
            student_id=student.id,
            risk_score=0.16,
            risk_level="Low",
            top_factors="Good attendance, no subjects below passing level, and steady participation in class.",
        )
    )

    session.add(
        PsychometricAttempt(
            student_id=student.id,
            riasec_scores=json.dumps(
                {
                    "Realistic": 14,
                    "Investigative": 24,
                    "Artistic": 12,
                    "Social": 18,
                    "Enterprising": 17,
                    "Conventional": 13,
                }
            ),
            top_codes="Investigative, Social, Enterprising",
            summary="You are drawn toward analytical subjects, teamwork, and activities where you can learn and help others.",
        )
    )

    session.add_all(
        [
            CareerRecommendation(
                student_id=student.id,
                career_name="App & Game Creator",
                match_score=86.0,
                rationale="Strong logical interests and curiosity about technology suit creative digital careers you can explore early.",
                skill_gap=json.dumps(["Block-based coding", "Logical thinking", "English communication"]),
                roadmap="Class 6–8: Scratch or block coding clubs. Class 9–10: strengthen Maths, join school computer club, build a small science or coding project.",
                certifications=json.dumps(
                    ["Code.org / Scratch certificates", "School computer club modules", "Local science fair participation"]
                ),
            ),
            CareerRecommendation(
                student_id=student.id,
                career_name="Doctor / Nurse (explore health sciences)",
                match_score=80.0,
                rationale="Investigative and social interests fit caring professions—worth exploring through science subjects and awareness activities.",
                skill_gap=json.dumps(["Biology basics", "Study habits", "Curiosity about the human body"]),
                roadmap="Do well in Science, join health awareness camps or science exhibitions, and read about how hospitals and research labs work.",
                certifications=json.dumps(["Science Olympiad foundation (school level)", "First-aid awareness workshops"]),
            ),
        ]
    )

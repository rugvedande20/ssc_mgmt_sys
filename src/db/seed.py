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
            age=20,
            gender="Male",
            department="Computer Science",
            semester=6,
            family_income_band="Middle",
            parental_education="Graduate",
            travel_distance_km=7.5,
            internet_access="Yes",
            interests_summary="Interested in analytics, coding, and problem solving.",
            strengths_summary="Consistent learner with strong logical reasoning.",
        )
    )

    session.add(
        AcademicRecord(
            student_id=student.id,
            attendance_percentage=84.0,
            cgpa=8.1,
            internal_marks=76.0,
            backlog_count=0,
            fee_pending="No",
            scholarship_status="No",
            extracurricular_participation="Yes",
            disciplinary_issues=0,
            engagement_score=7.9,
            stress_level=4.1,
        )
    )

    session.add(
        DropoutPrediction(
            student_id=student.id,
            risk_score=0.18,
            risk_level="Low",
            top_factors="Stable attendance, no backlogs, and healthy academic consistency.",
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
            summary="You are drawn toward analytical work with meaningful problem solving and collaborative impact.",
        )
    )

    session.add_all(
        [
            CareerRecommendation(
                student_id=student.id,
                career_name="Data Analyst",
                match_score=88.0,
                rationale="Strong analytical interest, consistent academics, and a good fit for data-driven roles.",
                skill_gap=json.dumps(["Advanced SQL", "Dashboard storytelling", "Statistics practice"]),
                roadmap="Month 1-2: strengthen SQL and Excel. Month 3-4: build dashboard projects. Month 5-6: learn Python analytics stack and publish portfolio work.",
                certifications=json.dumps(
                    ["Google Data Analytics", "Microsoft Power BI Data Analyst", "IBM Data Science Fundamentals"]
                ),
            ),
            CareerRecommendation(
                student_id=student.id,
                career_name="Business Intelligence Analyst",
                match_score=82.0,
                rationale="Balanced investigative and enterprising traits align with insight generation and business reporting.",
                skill_gap=json.dumps(["Power BI", "Business metrics", "Stakeholder communication"]),
                roadmap="Build KPI dashboards, practice data storytelling, and complete one business case project each month.",
                certifications=json.dumps(["PL-300 Power BI", "Tableau Desktop Specialist"]),
            ),
        ]
    )

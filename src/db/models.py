from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base
from src.utils.datetime_ist import now_ist


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String(60), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(60), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    assigned_grade: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_ist, nullable=False)
    created_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    student_profile: Mapped["StudentProfile"] = relationship(back_populates="user", uselist=False)
    academic_records: Mapped[list["AcademicRecord"]] = relationship(back_populates="student")
    dropout_predictions: Mapped[list["DropoutPrediction"]] = relationship(back_populates="student")
    psychometric_attempts: Mapped[list["PsychometricAttempt"]] = relationship(back_populates="student")
    career_recommendations: Mapped[list["CareerRecommendation"]] = relationship(back_populates="student")
    career_guidance_snapshots: Mapped[list["CareerGuidanceSnapshot"]] = relationship(back_populates="student")
    intervention_logs: Mapped[list["InterventionLog"]] = relationship(
        back_populates="student",
        foreign_keys="InterventionLog.student_id",
    )
    admin_actions: Mapped[list["InterventionLog"]] = relationship(
        foreign_keys="InterventionLog.admin_user_id",
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    age: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str | None] = mapped_column(String(20))
    department: Mapped[str | None] = mapped_column(String(100))
    semester: Mapped[int | None] = mapped_column(Integer)
    family_income_band: Mapped[str | None] = mapped_column(String(50))
    parental_education: Mapped[str | None] = mapped_column(String(100))
    travel_distance_km: Mapped[float | None] = mapped_column(Float)
    internet_access: Mapped[str | None] = mapped_column(String(20))
    interests_summary: Mapped[str | None] = mapped_column(Text)
    strengths_summary: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_ist, onupdate=now_ist, nullable=False
    )

    user: Mapped[User] = relationship(back_populates="student_profile")


class AcademicRecord(Base):
    __tablename__ = "academic_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    attendance_percentage: Mapped[float | None] = mapped_column(Float)
    cgpa: Mapped[float | None] = mapped_column(Float)
    internal_marks: Mapped[float | None] = mapped_column(Float)
    backlog_count: Mapped[int | None] = mapped_column(Integer)
    fee_pending: Mapped[str | None] = mapped_column(String(20))
    scholarship_status: Mapped[str | None] = mapped_column(String(20))
    extracurricular_participation: Mapped[str | None] = mapped_column(String(20))
    disciplinary_issues: Mapped[int | None] = mapped_column(Integer)
    engagement_score: Mapped[float | None] = mapped_column(Float)
    stress_level: Mapped[float | None] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=now_ist, nullable=False)

    student: Mapped[User] = relationship(back_populates="academic_records")


class DropoutPrediction(Base):
    __tablename__ = "dropout_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    top_factors: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_at: Mapped[datetime] = mapped_column(DateTime, default=now_ist, nullable=False)

    student: Mapped[User] = relationship(back_populates="dropout_predictions")


class PsychometricAttempt(Base):
    __tablename__ = "psychometric_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=now_ist, nullable=False)
    riasec_scores: Mapped[str] = mapped_column(Text, nullable=False)
    top_codes: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    student: Mapped[User] = relationship(back_populates="psychometric_attempts")


class CareerGuidanceSnapshot(Base):
    __tablename__ = "career_guidance_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    student_class: Mapped[int | None] = mapped_column(Integer)
    phase: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    report_json: Mapped[str] = mapped_column(Text, nullable=False)
    labour_horizon_years: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=now_ist, nullable=False)

    student: Mapped[User] = relationship(back_populates="career_guidance_snapshots")
    recommendations: Mapped[list["CareerRecommendation"]] = relationship(back_populates="guidance_snapshot")


class CareerRecommendation(Base):
    __tablename__ = "career_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    guidance_snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("career_guidance_snapshots.id"), nullable=True, index=True
    )
    career_name: Mapped[str] = mapped_column(String(120), nullable=False)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    skill_gap: Mapped[str] = mapped_column(Text, nullable=False)
    roadmap: Mapped[str] = mapped_column(Text, nullable=False)
    certifications: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=now_ist, nullable=False)

    student: Mapped[User] = relationship(back_populates="career_recommendations")
    guidance_snapshot: Mapped["CareerGuidanceSnapshot | None"] = relationship(
        back_populates="recommendations"
    )


class InterventionLog(Base):
    __tablename__ = "intervention_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    admin_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    action_taken: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_ist, nullable=False)

    student: Mapped[User] = relationship(foreign_keys=[student_id], back_populates="intervention_logs")

"""Labels and options for Class 6–10 (upper primary / secondary) students."""

APP_TAGLINE = (
    "Dropout risk insights for school teachers and early career exploration for Class 6–10 students."
)

FUTURE_GRADE_MIN = 11
FUTURE_GRADE_MAX = 12
FUTURE_SCOPE_NOTE = "Class 11–12 (stream selection and board exams) is planned for a future release."

SCHOOL_GRADES = tuple(range(6, 11))

GRADE_LABELS = {grade: f"Class {grade}" for grade in SCHOOL_GRADES}

SCHOOL_BOARDS = ("", "CBSE", "ICSE", "State Board", "IB", "Other")

# DB column name -> admin/student-facing label
# Annual household income (stored as display label in DB)
FAMILY_INCOME_BRACKETS: tuple[str, ...] = (
    "",
    "Below ₹2 lakh per year",
    "₹2–5 lakh per year",
    "₹5–10 lakh per year",
    "₹10–20 lakh per year",
    "Above ₹20 lakh per year",
)

# Map stored bracket → dropout model training categories (Low / Middle / …)
INCOME_BRACKET_TO_MODEL_BAND: dict[str, str] = {
    "Below ₹2 lakh per year": "Low",
    "₹2–5 lakh per year": "Middle",
    "₹5–10 lakh per year": "Middle",
    "₹10–20 lakh per year": "Upper Middle",
    "Above ₹20 lakh per year": "High",
    "Low": "Low",
    "Middle": "Middle",
    "Upper Middle": "Upper Middle",
    "High": "High",
}


def income_band_for_dropout_model(stored_value: str | None) -> str:
    if not stored_value:
        return "Middle"
    return INCOME_BRACKET_TO_MODEL_BAND.get(stored_value.strip(), "Middle")


PROFILE_FIELD_LABELS = {
    "age": "Age",
    "gender": "Gender",
    "department": "School name",
    "semester": "Class",
    "family_income_band": "Family annual income",
    "parental_education": "Parent / guardian education",
    "travel_distance_km": "Distance from school (km)",
    "internet_access": "Internet access at home",
    "interests_summary": "Interests and hobbies",
    "strengths_summary": "Strengths and achievements",
}

# Fields students must complete before assessment / career features unlock
REQUIRED_STUDENT_PROFILE_FIELDS = (
    "age",
    "gender",
    "department",
    "semester",
    "family_income_band",
    "parental_education",
    "travel_distance_km",
    "internet_access",
    "interests_summary",
    "strengths_summary",
)

ACADEMIC_FIELD_LABELS = {
    "attendance_percentage": "Attendance (%)",
    "cgpa": "Overall marks (%)",
    "internal_marks": "Latest term / unit test score (%)",
    "backlog_count": "Subjects below passing level",
    "fee_pending": "School fee pending",
    "scholarship_status": "Scholarship / fee concession",
    "extracurricular_participation": "Extracurricular activities",
    "disciplinary_issues": "Disciplinary incidents (this term)",
    "engagement_score": "Class participation (1–10)",
    "stress_level": "Stress level (1–10)",
}

# Canonical Class 6–10 CSV headers (used in template download and upload instructions)
SCHOOL_ACADEMIC_CSV_COLUMNS = [
    "student_username",
    "attendance_pct",
    "overall_marks_pct",
    "latest_term_test_pct",
    "subjects_below_passing",
    "school_fee_pending",
    "scholarship_or_concession",
    "extracurricular_activities",
    "disciplinary_incidents",
    "class_participation_score",
    "stress_level",
]

# Human-readable descriptions for each CSV column (shown in UI)
SCHOOL_ACADEMIC_CSV_COLUMN_HELP = {
    "student_username": "Firstname_lastname slug (e.g. aarav_patil) — used to generate login: first 3 + last 3 letters, password adds @123",
    "attendance_pct": "Attendance percentage (0–100)",
    "overall_marks_pct": "Overall marks / aggregate percentage (0–100)",
    "latest_term_test_pct": "Latest term or unit test score (0–100)",
    "subjects_below_passing": "Number of subjects below passing marks",
    "school_fee_pending": "Yes or No",
    "scholarship_or_concession": "Yes or No",
    "extracurricular_activities": "Yes or No (sports, clubs, NCC, etc.)",
    "disciplinary_incidents": "Count this term (0 if none)",
    "class_participation_score": "Participation in class (1–10)",
    "stress_level": "Self-reported or teacher-rated stress (1–10)",
}

# Optional columns (not required): first_name, last_name, school_name, class_grade (6–10)

# Maps any accepted CSV header (lowercase) -> internal DB column on academic_records
ACADEMIC_CSV_ALIASES: dict[str, str] = {
    # Primary school-friendly headers
    "student_username": "student_username",
    "attendance_pct": "attendance_percentage",
    "overall_marks_pct": "cgpa",
    "latest_term_test_pct": "internal_marks",
    "subjects_below_passing": "backlog_count",
    "school_fee_pending": "fee_pending",
    "scholarship_or_concession": "scholarship_status",
    "extracurricular_activities": "extracurricular_participation",
    "disciplinary_incidents": "disciplinary_issues",
    "class_participation_score": "engagement_score",
    "stress_level": "stress_level",
    # Common alternates
    "overall_percentage": "cgpa",
    "overall_marks_percentage": "cgpa",
    "term_exam_score": "internal_marks",
    "latest_test_score": "internal_marks",
    "failed_subjects": "backlog_count",
    "class_grade": "semester",
    "grade": "semester",
    "firstname": "first_name",
    "first_name": "first_name",
    "fname": "first_name",
    "lastname": "last_name",
    "last_name": "last_name",
    "lname": "last_name",
    "school": "school_name",
    "school_name": "school_name",
    # Legacy internal names (still accepted)
    "attendance_percentage": "attendance_percentage",
    "cgpa": "cgpa",
    "internal_marks": "internal_marks",
    "backlog_count": "backlog_count",
    "fee_pending": "fee_pending",
    "scholarship_status": "scholarship_status",
    "extracurricular_participation": "extracurricular_participation",
    "disciplinary_issues": "disciplinary_issues",
    "engagement_score": "engagement_score",
}

# Academic fields stored per import row (identity columns validated separately)
ACADEMIC_RECORD_DB_COLUMNS = [
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
]

# Backward-compatible alias used in import validation
ACADEMIC_DB_COLUMNS = ACADEMIC_RECORD_DB_COLUMNS

# DB column -> preferred school CSV header (for error messages)
DB_TO_SCHOOL_CSV_HEADER = {v: k for k, v in ACADEMIC_CSV_ALIASES.items() if k in SCHOOL_ACADEMIC_CSV_COLUMNS}


# Per-student academic upload (no username column — tied to selected student)
SCHOOL_STUDENT_ACADEMIC_COLUMNS = [
    "attendance_pct",
    "overall_marks_pct",
    "latest_term_test_pct",
    "subjects_below_passing",
    "school_fee_pending",
    "scholarship_or_concession",
    "extracurricular_activities",
    "disciplinary_incidents",
    "class_participation_score",
    "stress_level",
]


def build_student_academic_template_rows() -> list[dict[str, object]]:
    return [
        {
            "attendance_pct": 88.0,
            "overall_marks_pct": 74.0,
            "latest_term_test_pct": 72.0,
            "subjects_below_passing": 0,
            "school_fee_pending": "No",
            "scholarship_or_concession": "No",
            "extracurricular_activities": "Yes",
            "disciplinary_incidents": 0,
            "class_participation_score": 7.8,
            "stress_level": 4.0,
        }
    ]


def build_academic_csv_template_rows() -> list[dict[str, object]]:
    return [
        {
            "student_username": "aarav_patil",
            "class_grade": 6,
            "attendance_pct": 88.0,
            "overall_marks_pct": 74.0,
            "latest_term_test_pct": 72.0,
            "subjects_below_passing": 0,
            "school_fee_pending": "No",
            "scholarship_or_concession": "No",
            "extracurricular_activities": "Yes",
            "disciplinary_incidents": 0,
            "class_participation_score": 7.8,
            "stress_level": 4.0,
        },
        {
            "student_username": "priya_sharma",
            "class_grade": 6,
            "attendance_pct": 91.0,
            "overall_marks_pct": 78.0,
            "latest_term_test_pct": 76.0,
            "subjects_below_passing": 0,
            "school_fee_pending": "No",
            "scholarship_or_concession": "Yes",
            "extracurricular_activities": "Yes",
            "disciplinary_incidents": 0,
            "class_participation_score": 8.2,
            "stress_level": 3.5,
        },
    ]

# Used as categorical ML feature (school focus / inclination, not senior streams)
SCHOOL_FOCUS_AREAS_FOR_ML = (
    "General academics",
    "Science & Maths club",
    "Languages & reading",
    "Sports & leadership",
    "Arts & creativity",
    "Computers & digital skills",
)


def format_class(grade: int | None) -> str:
    if grade is None:
        return "—"
    return GRADE_LABELS.get(int(grade), f"Class {grade}")


def is_supported_grade(grade: int | None) -> bool:
    if grade is None:
        return False
    return int(grade) in SCHOOL_GRADES

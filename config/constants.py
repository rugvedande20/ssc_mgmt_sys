ROLES = {
    "student": "student",
    "admin": "admin",
    "superadmin": "superadmin",
}

STAFF_ROLES = ("admin", "superadmin")

RISK_LEVELS = ("Low", "Medium", "High")

INTERVENTION_PRIORITIES = ("Low", "Medium", "High")
INTERVENTION_INTENSITIES = ("Low", "Medium", "High")
INTERVENTION_STATUSES = ("scheduled", "completed", "cancelled")

INTERVENTION_TYPES = (
    "One-on-one counseling",
    "Group session",
    "Parent meeting",
    "Academic support",
    "Mental health referral",
    "Follow-up check-in",
)

INTERVENTION_MODULES = (
    "Academic resilience",
    "Attendance coaching",
    "Stress management",
    "Family engagement",
    "Financial aid support",
    "Social integration",
    "Career guidance follow-up",
)

RIASEC_TYPES = (
    "Realistic",
    "Investigative",
    "Artistic",
    "Social",
    "Enterprising",
    "Conventional",
)

# Target learners: Class 6–10 (Class 11–12 = future scope)
TARGET_GRADE_MIN = 6
TARGET_GRADE_MAX = 10

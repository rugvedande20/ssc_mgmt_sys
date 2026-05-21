import json

from config.school_context import PROFILE_FIELD_LABELS, REQUIRED_STUDENT_PROFILE_FIELDS

PROFILE_COMPLETENESS_FIELDS = REQUIRED_STUDENT_PROFILE_FIELDS

MIN_TEXT_FIELD_CHARS = 10


def _field_is_filled(profile: dict, field_name: str) -> bool:
    value = profile.get(field_name)
    if field_name in {"age", "semester"}:
        return value is not None
    if field_name == "travel_distance_km":
        return value is not None
    if field_name in {"interests_summary", "strengths_summary"}:
        return bool(str(value or "").strip()) and len(str(value).strip()) >= MIN_TEXT_FIELD_CHARS
    return value not in (None, "")


def profile_completeness_percent(profile: dict | None) -> int:
    if not profile:
        return 0
    filled = sum(1 for field_name in PROFILE_COMPLETENESS_FIELDS if _field_is_filled(profile, field_name))
    return round(100 * filled / len(PROFILE_COMPLETENESS_FIELDS))


def is_student_profile_complete(profile: dict | None) -> bool:
    if not profile:
        return False
    return all(_field_is_filled(profile, field_name) for field_name in PROFILE_COMPLETENESS_FIELDS)


def get_missing_profile_fields(profile: dict | None) -> list[str]:
    if not profile:
        return [PROFILE_FIELD_LABELS[field] for field in PROFILE_COMPLETENESS_FIELDS]
    return [
        PROFILE_FIELD_LABELS[field]
        for field in PROFILE_COMPLETENESS_FIELDS
        if not _field_is_filled(profile, field)
    ]


def validate_student_profile_data(profile_data: dict) -> list[str]:
    errors: list[str] = []
    profile_view = {
        "age": profile_data.get("age"),
        "gender": profile_data.get("gender") or "",
        "department": profile_data.get("department") or "",
        "semester": profile_data.get("semester"),
        "family_income_band": profile_data.get("family_income_band") or "",
        "parental_education": profile_data.get("parental_education") or "",
        "travel_distance_km": profile_data.get("travel_distance_km"),
        "internet_access": profile_data.get("internet_access") or "",
        "interests_summary": profile_data.get("interests_summary") or "",
        "strengths_summary": profile_data.get("strengths_summary") or "",
    }
    for field_name in PROFILE_COMPLETENESS_FIELDS:
        if not _field_is_filled(profile_view, field_name):
            label = PROFILE_FIELD_LABELS[field_name]
            if field_name in {"interests_summary", "strengths_summary"}:
                errors.append(f"{label} (at least {MIN_TEXT_FIELD_CHARS} characters)")
            else:
                errors.append(label)
    return errors


def parse_json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []

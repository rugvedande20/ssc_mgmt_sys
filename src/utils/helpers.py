import json

PROFILE_COMPLETENESS_FIELDS = (
    "department",
    "semester",
    "family_income_band",
    "internet_access",
    "interests_summary",
    "strengths_summary",
)


def profile_completeness_percent(profile: dict | None) -> int:
    if not profile:
        return 0
    filled = sum(
        1
        for field_name in PROFILE_COMPLETENESS_FIELDS
        if profile.get(field_name) not in (None, "")
    )
    return round(100 * filled / len(PROFILE_COMPLETENESS_FIELDS))


def parse_json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []

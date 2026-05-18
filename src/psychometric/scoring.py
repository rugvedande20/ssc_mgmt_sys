from __future__ import annotations

import json

from config.constants import RIASEC_TYPES


CATEGORY_DESCRIPTIONS = {
    "Realistic": "hands-on, practical, systems-oriented work",
    "Investigative": "analysis, research, and problem solving",
    "Artistic": "creative expression and original thinking",
    "Social": "helping, mentoring, and people-centered work",
    "Enterprising": "leadership, persuasion, and initiative",
    "Conventional": "structure, organization, and dependable execution",
}


def score_riasec_responses(responses: dict[str, int], question_bank: list[dict]) -> dict:
    scores = {category: 0 for category in RIASEC_TYPES}
    for question in question_bank:
        question_id = question["id"]
        category = question["category"]
        scores[category] += int(responses.get(question_id, 0))
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_codes = [category for category, _ in ranked[:3]]
    summary = build_summary(top_codes, scores)
    return {
        "scores": scores,
        "top_codes": top_codes,
        "summary": summary,
    }


def build_summary(top_codes: list[str], scores: dict[str, int]) -> str:
    if not top_codes:
        return "Assessment data is not available yet."
    primary = top_codes[0]
    secondary = top_codes[1] if len(top_codes) > 1 else None
    tertiary = top_codes[2] if len(top_codes) > 2 else None

    parts = [f"Your strongest interest pattern is {primary.lower()}, which points toward {CATEGORY_DESCRIPTIONS[primary]}."]
    if secondary:
        parts.append(
            f"You also show strong alignment with {secondary.lower()}, suggesting comfort with {CATEGORY_DESCRIPTIONS[secondary]}."
        )
    if tertiary:
        parts.append(f"A supporting signal appears in {tertiary.lower()}, adding depth to your profile.")

    highest_score = scores[primary]
    if highest_score >= 21:
        parts.append("This is a strong and stable preference pattern rather than a weak directional signal.")
    else:
        parts.append("Your profile is still fairly balanced, so several future pathways (streams, subjects, and careers) may suit you.")
    return " ".join(parts)


def format_scores_json(scores: dict[str, int]) -> str:
    return json.dumps(scores)

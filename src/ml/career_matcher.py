from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from config.constants import RIASEC_TYPES
from config.settings import settings


def _career_data_dir() -> Path:
    return settings.data_dir / "career"


def load_labor_outlook() -> dict[str, Any]:
    path = _career_data_dir() / "labor_outlook.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_career_catalog() -> list[dict[str, Any]]:
    path = _career_data_dir() / "career_catalog.json"
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload.get("careers", [])


def _riasec_vector(profile: dict[str, float]) -> np.ndarray:
    return np.array([float(profile.get(category, 0.0)) for category in RIASEC_TYPES], dtype=float)


def _normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    values = [max(float(scores.get(category, 0)), 0.0) for category in RIASEC_TYPES]
    total = sum(values)
    if total <= 0:
        return {category: 1.0 / len(RIASEC_TYPES) for category in RIASEC_TYPES}
    return {category: value / total for category, value in zip(RIASEC_TYPES, values)}


def _sector_growth_map(outlook: dict[str, Any]) -> dict[str, float]:
    return {sector["id"]: float(sector.get("growth_rate", 0.5)) for sector in outlook.get("sectors", [])}


def _academic_readiness(academic: dict[str, Any] | None, career: dict[str, Any]) -> float:
    if not academic:
        return 0.55
    marks = academic.get("overall_marks_pct") or academic.get("cgpa")
    attendance = academic.get("attendance_percentage")
    engagement = academic.get("engagement_score")
    below_passing = academic.get("subjects_below_passing") or academic.get("backlog_count") or 0

    marks_score = 0.5
    if marks is not None:
        min_marks = float(career.get("min_marks_pct", 60))
        marks_score = min(1.0, float(marks) / max(min_marks, 1))

    attendance_score = 0.5
    if attendance is not None:
        min_att = float(career.get("min_attendance_pct", 75))
        attendance_score = min(1.0, float(attendance) / max(min_att, 1))

    engagement_score = 0.6
    if engagement is not None:
        engagement_score = min(1.0, float(engagement) / 10.0)

    penalty = min(0.25, int(below_passing) * 0.08)
    return max(0.0, min(1.0, 0.45 * marks_score + 0.35 * attendance_score + 0.2 * engagement_score - penalty))


def _labour_outlook_boost(career: dict[str, Any], sector_growth: dict[str, float]) -> float:
    sectors = career.get("sectors") or []
    if not sectors:
        return 0.5
    rates = [sector_growth.get(sector_id, 0.5) for sector_id in sectors]
    return sum(rates) / len(rates)


def _build_rationale(
    career: dict[str, Any],
    top_codes: list[str],
    outlook_sectors: list[dict[str, Any]],
    match_score: float,
) -> str:
    sector_names = [
        sector["name"]
        for sector in outlook_sectors
        if sector["id"] in (career.get("sectors") or [])
    ]
    interest_bit = (
        f"Your interest pattern ({', '.join(top_codes[:3])}) aligns with this pathway."
        if top_codes
        else "Your profile shows workable fit for this pathway."
    )
    matched_sector = next(
        (s for s in outlook_sectors if s["id"] in (career.get("sectors") or [])),
        outlook_sectors[0] if outlook_sectors else None,
    )
    rising_roles = (matched_sector or {}).get("rising_roles") or []
    labour_bit = (
        f"Labour outlook (next 5 years): {', '.join(sector_names[:2])} is projected to grow — "
        f"roles like {', '.join(rising_roles[:2])} are rising."
        if sector_names
        else "Future job demand in related sectors is steady to rising over the next five years."
    )
    return f"{interest_bit} {labour_bit} Overall future-fit score: {match_score:.0f}%."


def match_careers_for_student(
    *,
    riasec_scores: dict[str, float],
    top_codes: list[str],
    latest_academic: dict[str, Any] | None,
    academic_trend: dict[str, Any] | None,
    profile: dict[str, Any] | None,
    student_class: int | None,
    limit: int = 5,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    catalog = load_career_catalog()
    outlook = load_labor_outlook()
    sector_growth = _sector_growth_map(outlook)

    student_vec = _riasec_vector(_normalize_scores(riasec_scores))
    academic = latest_academic or {}
    if academic_trend:
        academic = {**academic, **academic_trend}

    rising_sectors = sorted(
        outlook.get("sectors", []),
        key=lambda item: float(item.get("growth_rate", 0)),
        reverse=True,
    )[:4]

    matches: list[dict[str, Any]] = []
    for career in catalog:
        career_vec = _riasec_vector(career.get("riasec_profile", {}))
        interest_sim = float(cosine_similarity(student_vec.reshape(1, -1), career_vec.reshape(1, -1))[0][0])
        labour_boost = _labour_outlook_boost(career, sector_growth)
        academic_fit = _academic_readiness(academic, career)

        # Weighted future-oriented score (interest + labour projection + academics)
        raw = 0.48 * interest_sim + 0.32 * labour_boost + 0.2 * academic_fit
        match_pct = round(max(0.0, min(100.0, raw * 100)), 1)

        matches.append(
            {
                "career_id": career["id"],
                "career_name": career["name"],
                "match_score": match_pct,
                "rationale": _build_rationale(career, top_codes, rising_sectors, match_pct),
                "skill_gap": json.dumps(career.get("skills", [])),
                "roadmap": career.get("roadmap", ""),
                "certifications": json.dumps(career.get("certifications", [])),
                "sectors": career.get("sectors", []),
                "interest_similarity": round(interest_sim, 3),
                "labour_boost": round(labour_boost, 3),
                "academic_fit": round(academic_fit, 3),
            }
        )

    matches.sort(key=lambda item: item["match_score"], reverse=True)
    top_matches = matches[:limit]

    meta = {
        "rising_sectors": [
            {"id": s["id"], "name": s["name"], "growth_rate": s.get("growth_rate")}
            for s in rising_sectors
        ],
        "horizon_years": outlook.get("horizon_years", 5),
        "student_class": student_class,
        "records_used": {
            "has_academic": bool(latest_academic),
            "has_profile": bool(profile),
            "psychometric_codes": top_codes,
        },
    }
    return top_matches, meta


def build_class_10_report(
    *,
    profile: dict[str, Any] | None,
    matches: list[dict[str, Any]],
    meta: dict[str, Any],
    academic_history_count: int,
    psychometric_count: int,
) -> dict[str, Any]:
    top = matches[0] if matches else None
    marks = None
    if profile:
        pass
    stream_hints = []
    if top:
        sectors = top.get("sectors") or []
        if "digital_tech" in sectors or "infrastructure" in sectors:
            stream_hints.append(
                {
                    "stream": "Science (PCM/PCB)",
                    "reason": "Strong match with analytical/STEM futures and rising tech/health roles.",
                }
            )
        if "business_finance" in sectors:
            stream_hints.append(
                {
                    "stream": "Commerce",
                    "reason": "Aligns with finance, business, and entrepreneurship pathways.",
                }
            )
        if "creative_media" in sectors:
            stream_hints.append(
                {
                    "stream": "Arts / Humanities with skill electives",
                    "reason": "Supports creative, media, and communication careers.",
                }
            )
    if not stream_hints:
        stream_hints.append(
            {
                "stream": "Explore with counsellor",
                "reason": "Complete more assessments and term records for a sharper stream call.",
            }
        )

    return {
        "title": "Class 10 transition report",
        "summary": (
            f"Based on {psychometric_count} interest assessment(s), "
            f"{academic_history_count} academic snapshot(s), and 5-year labour projections."
        ),
        "top_career": top["career_name"] if top else None,
        "stream_recommendations": stream_hints[:3],
        "next_steps": [
            "Discuss top 3 pathways with parents and school counsellor.",
            "Choose Class 11–12 stream aligned with strongest match and marks.",
            "Plan skill-building activities from the roadmap sections below.",
        ],
        "labour_outlook": meta.get("rising_sectors", []),
    }

from __future__ import annotations

import json

from sqlalchemy import desc, select

from src.db.models import PsychometricAttempt
from src.utils.datetime_ist import format_datetime_ist
from src.psychometric.questions import QUESTION_BANK
from src.psychometric.scoring import format_scores_json, score_riasec_responses


def get_question_bank() -> list[dict]:
    return QUESTION_BANK


def save_psychometric_attempt(session, student_id: int, responses: dict[str, int]) -> PsychometricAttempt:
    scoring_result = score_riasec_responses(responses, QUESTION_BANK)
    attempt = PsychometricAttempt(
        student_id=student_id,
        riasec_scores=format_scores_json(scoring_result["scores"]),
        top_codes=", ".join(scoring_result["top_codes"]),
        summary=scoring_result["summary"],
    )
    session.add(attempt)
    session.flush()
    return attempt


def get_latest_attempt(session, student_id: int) -> PsychometricAttempt | None:
    return session.scalar(
        select(PsychometricAttempt)
        .where(PsychometricAttempt.student_id == student_id)
        .order_by(desc(PsychometricAttempt.submitted_at))
    )


def list_recent_attempts(session, student_id: int, limit: int = 5) -> list[dict]:
    rows = session.execute(
        select(PsychometricAttempt)
        .where(PsychometricAttempt.student_id == student_id)
        .order_by(desc(PsychometricAttempt.submitted_at))
        .limit(limit)
    ).scalars()
    attempts = []
    for row in rows:
        attempts.append(
            {
                "submitted_at": format_datetime_ist(row.submitted_at),
                "top_codes": row.top_codes,
                "summary": row.summary,
            }
        )
    return attempts


def parse_score_map(attempt: PsychometricAttempt | None) -> dict[str, int]:
    if not attempt:
        return {}
    return json.loads(attempt.riasec_scores)


def get_latest_attempt_payload(session, student_id: int) -> dict | None:
    attempt = get_latest_attempt(session, student_id)
    if not attempt:
        return None
    return {
        "submitted_at": format_datetime_ist(attempt.submitted_at),
        "top_codes": attempt.top_codes,
        "summary": attempt.summary,
        "score_map": json.loads(attempt.riasec_scores),
    }

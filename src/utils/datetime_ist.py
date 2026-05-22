"""India Standard Time (IST) helpers for storage and display."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# Standard display formats (always IST)
FMT_DATETIME = "%Y-%m-%d %H:%M IST"
FMT_DATE = "%d %b %Y"
FMT_DATE_LONG = "%b %d, %Y"


def now_ist() -> datetime:
    """Naive datetime in IST for SQLite columns."""
    return datetime.now(IST).replace(tzinfo=None)


def format_datetime_ist(value: datetime | None, fmt: str = FMT_DATETIME) -> str:
    if value is None:
        return "—"
    return value.strftime(fmt)


def format_date_ist(value: datetime | None, fmt: str = FMT_DATE_LONG) -> str:
    if value is None:
        return "—"
    return value.strftime(fmt)


def parse_display_datetime(value: str) -> datetime | None:
    """Parse UI datetime strings (with or without IST suffix)."""
    cleaned = (value or "").replace(" IST", "").strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None

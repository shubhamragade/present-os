from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import pytz
from dateparser.search import search_dates


def parse_time(text: str, timezone: str) -> Optional[Dict[str, Any]]:
    """
    Time extraction ONLY.

    Responsibilities:
    - Detect a datetime from natural language
    - Return structured time metadata
    - NEVER modify or clean semantic text
    - NEVER infer task titles

    Returns:
    {
        "start": ISO datetime,
        "end": ISO datetime,
        "matched_text": str
    }
    """

    if not text or not timezone:
        return None

    try:
        tz = pytz.timezone(timezone)
    except Exception:
        tz = pytz.UTC

    results = search_dates(
        text,
        settings={
            "RETURN_AS_TIMEZONE_AWARE": True,
            "TIMEZONE": tz.zone,
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.now(tz),
        },
    )

    if not results:
        return None

    matched_text, parsed_dt = results[0]

    if not parsed_dt:
        return None

    if parsed_dt.tzinfo is None:
        parsed_dt = tz.localize(parsed_dt)

    start = parsed_dt
    end = start + timedelta(minutes=30)  # default block

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "matched_text": matched_text,
    }

from __future__ import annotations

import logging
from datetime import datetime
from collections import defaultdict
from typing import Dict, Any, List

from app.graph.state import PresentOSState
from app.integrations.notion_client import NotionClient

logger = logging.getLogger("presentos.report_agent")


# ---------------------------------------------------------
# Node entry point
# ---------------------------------------------------------
def run_report_node(state: PresentOSState) -> PresentOSState:
    """
    Report Agent (PDF-compliant)

    ROLE:
    - Aggregate XP history
    - Produce weekly & monthly reports
    - NEVER mutate tasks/calendar/xp
    - READ-ONLY Notion access

    Output is consumed by frontend directly.
    """

    logger.info("ReportAgent started")

    notion = NotionClient.from_env()

    try:
        xp_entries = notion.get_xp_entries(page_size=200)
    except Exception as e:
        logger.exception("Failed to fetch XP entries")
        state.add_agent_output(
            "report_agent",
            {"status": "error", "error": str(e)},
            score=0.0,
        )
        return state

    if not xp_entries:
        state.add_agent_output(
            "report_agent",
            {"status": "empty", "message": "No XP data available"},
            score=0.2,
        )
        return state

    report = _build_xp_report(xp_entries)

    state.add_agent_output(
        "report_agent",
        {
            "action": "xp_report_generated",
            "report": report,
        },
        score=0.9,
    )

    logger.info("ReportAgent completed successfully")
    return state


# ---------------------------------------------------------
# Core aggregation logic (pure, deterministic)
# ---------------------------------------------------------
def _build_xp_report(xp_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate XP entries into:
    - Weekly summary
    - Monthly summary
    - PAEI totals
    - Category breakdown
    """

    now = datetime.utcnow()
    current_week = int(now.strftime("%V"))
    current_month = now.month

    weekly_total = 0
    monthly_total = 0

    paei_totals = defaultdict(int)
    category_totals = defaultdict(int)
    bonus_total = 0
    base_total = 0

    weekly_entries = []
    monthly_entries = []

    for page in xp_entries:
        props = page.get("properties", {})

        amount = _num(props, "Amount")
        paei = _select(props, "PAEI")
        category = _select(props, "XP Category")
        bonus = _num(props, "XP Bonus")
        week = _num(props, "Week Number")
        month = _num(props, "Month Number")

        # Global totals
        base_total += amount
        bonus_total += bonus or 0

        if paei:
            paei_totals[paei] += amount

        if category:
            category_totals[category] += amount

        # Weekly
        if week == current_week:
            weekly_total += amount
            weekly_entries.append(amount)

        # Monthly
        if month == current_month:
            monthly_total += amount
            monthly_entries.append(amount)

    return {
        "generated_at": now.isoformat(),
        "current_week": current_week,
        "current_month": current_month,
        "weekly": {
            "total_xp": weekly_total,
            "entries": len(weekly_entries),
        },
        "monthly": {
            "total_xp": monthly_total,
            "entries": len(monthly_entries),
        },
        "paei_breakdown": dict(paei_totals),
        "xp_category_breakdown": dict(category_totals),
        "base_xp": base_total,
        "bonus_xp": bonus_total,
        "overall_xp": base_total + bonus_total,
    }


# ---------------------------------------------------------
# Property helpers (safe Notion reads)
# ---------------------------------------------------------
def _num(props: Dict[str, Any], key: str) -> int:
    try:
        return int(props.get(key, {}).get("number") or 0)
    except Exception:
        return 0


def _select(props: Dict[str, Any], key: str) -> str | None:
    try:
        return props.get(key, {}).get("select", {}).get("name")
    except Exception:
        return None

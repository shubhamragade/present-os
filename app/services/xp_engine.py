"""
XP Engine for Present OS.

ROLE:
- Central authority for XP calculation
- Deterministic, testable, and PAEI-aware
- Used ONLY by xp_agent
"""

from __future__ import annotations
from typing import Dict, Optional


# ---------------------------------------------------------
# Configuration (single source of truth)
# ---------------------------------------------------------

BASE_XP_BY_ACTION: Dict[str, int] = {
    "task_complete": 5,
    "meeting_complete": 3,
    "deep_work_block": 8,
    "habit_streak": 10,
    "reflection": 4,
    "report_viewed": 2,
}

PAEI_MULTIPLIER: Dict[str, float] = {
    "P": 1.2,
    "A": 1.0,
    "E": 1.3,
    "I": 1.1,
}

DIFFICULTY_BONUS: Dict[str, int] = {
    "easy": 0,
    "medium": 2,
    "hard": 5,
}

MAX_DURATION_BONUS = 5
DURATION_UNIT_MINUTES = 30


# ---------------------------------------------------------
# Public API
# ---------------------------------------------------------

def calculate_xp(
    *,
    action_type: str,
    paei: str,
    difficulty: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    priority: Optional[str] = None,
    paei_distribution: Optional[Dict[str, float]] = None,
    recovery_score: Optional[int] = None,
) -> Dict[str, object]:
    """
    Calculate XP for a completed action.
    """

    if action_type not in BASE_XP_BY_ACTION:
        raise ValueError(f"Unknown action_type: {action_type}")

    paei = paei.upper()
    if paei not in PAEI_MULTIPLIER:
        raise ValueError(f"Invalid PAEI value: {paei}")

    base_xp = BASE_XP_BY_ACTION[action_type]
    xp = int(round(base_xp * PAEI_MULTIPLIER[paei]))

    bonus = 0

    if difficulty:
        bonus += DIFFICULTY_BONUS.get(difficulty, 0)

    if duration_minutes and duration_minutes > 0:
        bonus += min(duration_minutes // DURATION_UNIT_MINUTES, MAX_DURATION_BONUS)

    if priority == "high":
        bonus += 1
    elif priority == "low":
        bonus = max(bonus - 1, 0)

    # -------------------------
    # PAEI balance adjustment
    # -------------------------
    balance_multiplier = 1.0
    if paei_distribution:
        dominance = paei_distribution.get(paei, 0)
        if dominance > 0.45:
            balance_multiplier = 0.7
        elif dominance < 0.15:
            balance_multiplier = 1.3

    # -------------------------
    # Recovery awareness
    # -------------------------
    recovery_multiplier = 1.0
    if recovery_score is not None and recovery_score < 40:
        if paei == "P":
            recovery_multiplier = 0.6
        elif paei == "I":
            recovery_multiplier = 1.2

    total_xp = max(
        int(round((xp + bonus) * balance_multiplier * recovery_multiplier)),
        1,
    )

    return {
        "xp": total_xp,
        "category": _infer_category(action_type, paei),
        "bonus": bonus,
        "reason": _build_reason(action_type, paei, difficulty, duration_minutes),
    }


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _infer_category(action_type: str, paei: str) -> str:
    if action_type == "deep_work_block":
        return "deep_work"
    if action_type == "meeting_complete":
        return "collaboration"
    if action_type == "habit_streak":
        return "consistency"
    if action_type == "reflection":
        return "self_awareness"
    return f"{paei.lower()}_execution"


def _build_reason(
    action_type: str,
    paei: str,
    difficulty: Optional[str],
    duration_minutes: Optional[int],
) -> str:
    parts = [action_type.replace("_", " ").title()]
    if difficulty:
        parts.append(f"({difficulty})")
    if duration_minutes:
        parts.append(f"{duration_minutes} min")
    parts.append(f"[PAEI={paei}]")
    return " ".join(parts)

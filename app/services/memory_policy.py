# app/services/memory_policy.py
"""
Memory Write Policy for PresentOS

PDF RULES:
- Memory is written ONLY for durable outcomes
- No raw conversations
- No scheduling noise
- Deterministic rules only
"""

from __future__ import annotations
from typing import Dict, Any


def should_store_memory(event: Dict[str, Any]) -> bool:
    """
    Decide whether an agent output or planned action
    should be persisted to long-term memory.
    """

    action = event.get("action") or event.get("type")

    return action in {
        "task_completed",
        "xp_awarded",
        "quest_completed",
        "focus_session_ended",
    }


def infer_memory_type(event: Dict[str, Any]) -> str:
    """
    Classify memory type for Pinecone metadata.
    """

    action = event.get("action") or event.get("type")

    mapping = {
        "task_completed": "task_outcome",
        "xp_awarded": "performance_pattern",
        "quest_completed": "major_outcome",
        "focus_session_ended": "energy_pattern",
    }

    return mapping.get(action, "generic_outcome")


def build_memory_content(event: Dict[str, Any]) -> str:
    """
    Convert structured event → human-readable memory seed.
    (This will be summarized by RAGService)
    """

    if event.get("action") == "task_completed":
        return f"User completed a task successfully. PAEI={event.get('paei')}"

    if event.get("action") == "xp_awarded":
        return f"User earned XP for productive action. XP={event.get('xp')}"

    if event.get("action") == "quest_completed":
        return f"User completed a major quest: {event.get('name')}"

    if event.get("action") == "focus_session_ended":
        return "User completed a focus session affecting energy patterns"

    return "User achieved a meaningful outcome"

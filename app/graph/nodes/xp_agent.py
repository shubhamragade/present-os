from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from app.services.xp_engine import calculate_xp, BASE_XP_BY_ACTION
from app.integrations.notion_client import NotionClient
from app.graph.state import PresentOSState
from app.utils.instruction_utils import get_instruction

logger = logging.getLogger("presentos.xp_agent")

# 🔑 ACTION NORMALIZATION
ACTION_MAP = {
    "action_complete": "task_complete",
    "task_created": "task_complete",
    "meeting_created": "meeting_complete",
    "focus_started": "deep_work_block",
    "email_sent": "task_complete",  # Changed from communication
    "bill_paid": "task_complete",   # Changed from admin_complete
    "workout_completed": "health_activity",
    "meditation_completed": "mindfulness",
    "report_viewed": "report_viewed",  # ADDED
}

def run_xp_node(
    state: PresentOSState,
    notion: Optional[NotionClient] = None,
) -> PresentOSState:

    if "xp_agent" not in state.activated_agents:
        return state

    # Get instruction with error handling
    try:
        instruction = get_instruction(state, "xp_agent")
    except Exception as e:
        logger.error("Failed to get instruction for XP agent: %s", e)
        return state
    
    if not instruction:
        logger.debug("No instruction for XP agent, skipping")
        return state

    payload = instruction.get("payload", {})
    raw_action = payload.get("action_type")

    if not raw_action:
        logger.warning("XP instruction missing action_type")
        return state

    # -------------------------------------------------
    # 1️⃣ NORMALIZE ACTION
    # -------------------------------------------------
    action_type = ACTION_MAP.get(raw_action, raw_action)

    if action_type not in BASE_XP_BY_ACTION:
        logger.warning("XP skipped: unsupported action_type=%s", raw_action)
        return state

    # -------------------------------------------------
    # 2️⃣ CALCULATE XP (PURE) - FIXED SIGNATURE
    # -------------------------------------------------
    try:
        xp_result = calculate_xp(
            action_type=action_type,
            paei=payload.get("paei", "P"),
            difficulty=payload.get("difficulty"),
            duration_minutes=payload.get("duration_minutes"),
            priority=payload.get("priority"),
            # REMOVED: metadata parameter
            # Add other parameters if your calculate_xp accepts them:
            # paei_distribution=payload.get("paei_distribution"),
            # recovery_score=payload.get("recovery_score"),
        )
    except Exception as e:
        logger.error("XP calculation failed for action_type=%s: %s", action_type, e)
        return state

    # -------------------------------------------------
    # 3️⃣ WRITE XP (MATCHES NotionClient EXACTLY)
    # -------------------------------------------------
    xp_page_id = None
    if notion:
        try:
            page = notion.create_xp(
                amount=xp_result["xp"],
                paei=payload.get("paei"),
                reason=xp_result["reason"],
                xp_category=xp_result.get("category"),
                xp_bonus=xp_result.get("bonus"),
                task_id=payload.get("task_id"),
                map_id=payload.get("map_id"),
                quest_id=payload.get("quest_id"),
                occurred_at=datetime.utcnow(),
            )
            xp_page_id = page.get("id")
            logger.info(
                "XP entry created: action=%s xp=%d page_id=%s",
                action_type, xp_result["xp"], xp_page_id
            )
        except Exception as e:
            logger.exception("XP persistence failed: %s", e)
            # Continue even if persistence fails - XP still calculated

    # -------------------------------------------------
    # 4️⃣ OUTPUT (FOR UI / TESTS)
    # -------------------------------------------------
    # -------------------------------------------------
    # 4️⃣ OUTPUT (FOR UI / TESTS)
    # -------------------------------------------------
    result_data = {
        "status": "success",
        "xp": xp_result["xp"],
        "category": xp_result.get("category"),
        "bonus": xp_result.get("bonus"),
        "reason": xp_result["reason"],
        "xp_page_id": xp_page_id,
        "paei": payload.get("paei"),
        "action_type": action_type,
        "raw_action": raw_action,
    }
        
    # -------------------------------------------------
    # 5️⃣ INJECT FULL SUMMARY (For "Show XP" requests)
    # -------------------------------------------------
    if notion:
        try:
            summary = notion.get_xp_summary()
            state.add_agent_output(agent="xp_agent", result={**result_data, "summary": summary}, score=1.0)
            return state
        except Exception as e:
            logger.warning("Failed to fetch XP summary for agent output: %s", e)

    # Fallback if no notion or failure
    state.add_agent_output(
        agent="xp_agent",
        result=result_data,
        score=0.9 if xp_page_id else 0.5,
    )

    logger.debug("XP agent completed for action: %s", action_type)
    return state
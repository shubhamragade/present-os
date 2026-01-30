# app/graph/nodes/quest_agent.py
"""
Quest Agent for PresentOS (EXECUTION ONLY)

PDF COMPLIANCE:
- Creates Quests explicitly requested by user
- Writes to Notion (system of record)
- NO inference
- NO auto-promotion from tasks
- NO routing
- NO XP
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from app.graph.state import PresentOSState
from app.services.quest_service import QuestService
from app.integrations.notion_client import NotionClient
from app.utils.instruction_utils import get_instruction

logger = logging.getLogger("presentos.quest_agent")


def run_quest_node(
    state: PresentOSState,
    notion: NotionClient,
) -> PresentOSState:
    """
    Expected Parent instructions:
    {
        "intent": "create_quest",
        "payload": {
            "name": str,
            "purpose": str,
            "result": str,
            "category": str,
            "avatar": str,
            "xp_target": int (optional),
            "start_date": iso (optional),
            "end_date": iso (optional)
        }
    }
    """

    # 🔒 REQUIRED ACTIVATION GUARD
    if "quest_agent" not in state.activated_agents:
        return state

    decision = state.parent_decision or {}
    instruction = get_instruction(state, "quest_agent")
    if not instruction:
        return state

    payload = instruction.get("payload", {})

    required_fields = ["name", "purpose", "result"]
    missing = [f for f in required_fields if not payload.get(f)]

    # If fields are missing, try to extract them from the user text using ConversationManager
    if missing:
        logger.info(f"ConversationManager detected missing slots: {missing}")
        
        from app.services.conversation_manager import ConversationManager
        
        # Get user text from state
        user_text = state.input_text or payload.get("text", "")
        
        if user_text:
            conv_mgr = ConversationManager()
            extracted = conv_mgr.extract_quest_fields(user_text)
            
            # Merge extracted fields into payload
            for field in missing:
                if field in extracted and extracted[field]:
                    payload[field] = extracted[field]
                    logger.info(f"Extracted {field}: {extracted[field]}")
            
            # Re-check missing fields
            missing = [f for f in required_fields if not payload.get(f)]
    
    # Add default category if missing
    if not payload.get("category"):
        payload["category"] = "General"
    
    if not payload.get("avatar"):
        payload["avatar"] = "Warrior"

    if missing:
        state.add_agent_output(
            agent="quest_agent",
            result={
                "status": "blocked",
                "reason": "missing_required_fields",
                "missing": missing,
            },
            score=0.0,
        )
        return state

    try:
        service = QuestService(notion)
        quest = service.create_quest(payload)

        state.add_agent_output(
            agent="quest_agent",
            result={
                "status": "quest_created",
                "quest_id": quest.get("id"),
                "name": payload["name"],
                "category": payload["category"],
                "avatar": payload["avatar"],
            },
            score=0.95,
        )
        return state

    except Exception as e:
        logger.exception("QuestAgent failed")
        state.add_agent_output(
            agent="quest_agent",
            result={"status": "error", "error": str(e)},
            score=0.0,
        )
        return state

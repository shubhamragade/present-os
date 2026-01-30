from __future__ import annotations

import logging
from typing import Dict, Any

from app.graph.state import PresentOSState
from app.integrations.notion_client import NotionClient
from app.utils.instruction_utils import get_instruction

logger = logging.getLogger("presentos.task_agent")


def run_task_node(
    state: PresentOSState,
    notion: NotionClient,
) -> PresentOSState:
    """
    Task Agent (PDF compliant + RPM enforcement)

    - Executes ONE task-related instruction
    - Writes tasks to Notion
    - AUTO-LINKS to active Quest/MAP if not specified (RPM compliance)
    - Emits agent output only
    - NEVER routes
    """

    instruction = get_instruction(state, "task_agent")
    if not instruction:
        return state

    intent = instruction.get("intent")
    payload = instruction.get("payload", {})

    if intent != "create_task":
        return state

    # --------------------------------------------------
    # RPM ENFORCEMENT: Auto-link to active Quest/MAP
    # --------------------------------------------------
    quest_id = payload.get("quest_id")
    map_id = payload.get("map_id")
    quest_name = payload.get("quest_name")
    map_name = None
    auto_linked = False
    
    # Auto-link to active Quest if not specified
    if not quest_id:
        try:
            active_quest = notion.get_active_quest()
            if active_quest:
                quest_id = active_quest["id"]
                quest_name = active_quest.get("name", "Active Quest")
                auto_linked = True
                logger.info(f"RPM: Auto-linked task to active Quest: {quest_name}")
            else:
                logger.warning("RPM: No active Quest found. Task created without Quest link.")
        except Exception as e:
            logger.warning(f"RPM: Failed to fetch active Quest: {e}")
    
    # Auto-link to active MAP if not specified
    if not map_id:
        try:
            active_map = notion.get_active_map()
            if active_map:
                map_id = active_map["id"]
                map_name = active_map.get("name", "Active MAP")
                auto_linked = True
                logger.info(f"RPM: Auto-linked task to active MAP: {map_name}")
            else:
                logger.debug("RPM: No active MAP found. Task created without MAP link.")
        except Exception as e:
            logger.warning(f"RPM: Failed to fetch active MAP: {e}")

    # --------------------------------------------------
    # CREATE NOTION PAGE (USING STANDARDIZED HELPER)
    # --------------------------------------------------
    task_properties = {
        "title": payload.get("title", "Untitled Task"),
        "status": "todo",
        "description": payload.get("description"),
        "deadline": payload.get("deadline"),
        "priority": payload.get("priority", "Medium"),
        "paei": payload.get("paei"),
        "energy_level": payload.get("energy_level"),
        "estimated_duration": payload.get("estimated_duration"),
        "google_event_id": payload.get("google_event_id"),
        "quest_id": quest_id,
        "map_id": map_id,
        "source": payload.get("source", "PresentOS")
    }

    res = notion.create_task(task_properties)

    task_id = res.get("id")
    logger.info("Task created in Notion: %s (Quest: %s, MAP: %s)", task_id, quest_name, map_name)

    # --------------------------------------------------
    # AGENT OUTPUT (NO DECISIONS)
    # --------------------------------------------------
    result = {
        "action": "task_created",
        "task_id": task_id,
        "title": payload.get("title"),
        "quest_name": quest_name,
        "quest_id": quest_id,
        "map_id": map_id,
        "auto_linked": auto_linked,
    }
    
    # Add RPM context message if auto-linked
    if auto_linked:
        links = []
        if quest_name:
            links.append(f"Quest: {quest_name}")
        if map_name:
            links.append(f"MAP: {map_name}")
        result["rpm_message"] = f"Auto-linked to {', '.join(links)}"
    
    state.add_agent_output(
        agent="task_agent",
        result=result,
        score=0.95,
    )

    return state

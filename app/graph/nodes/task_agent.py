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
    Task Agent (PDF compliant)

    - Executes ONE task-related instruction
    - Writes tasks to Notion
    - Initializes safe defaults
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
    # BUILD NOTION PROPERTIES (SAFE + EXPLICIT)
    # --------------------------------------------------
    props: Dict[str, Any] = {
        "Name": notion._prop_title(
            payload.get("title", "Untitled Task")
        ),

        # Safe defaults
        "Status": notion._prop_select("To Do"),
        "Auto-Scheduled": notion._prop_checkbox(False),
        "Deep Work Required": notion._prop_checkbox(
            bool(payload.get("deep_work_required", False))
        ),
        "Source": notion._prop_select("PresentOS"),
    }

    # Optional text fields
    if payload.get("description"):
        props["Description"] = notion._prop_text(payload["description"])

    # Deadline
    if payload.get("deadline"):
        props["Deadline"] = notion._prop_date(payload["deadline"])

    # Priority (must match Notion select values)
    if payload.get("priority"):
        props["Priority"] = notion._prop_select(payload["priority"])

    # PAEI
    if payload.get("paei"):
        props["PAEI"] = notion._prop_select(payload["paei"])

    # Energy level (if explicitly provided)
    if payload.get("energy_level"):
        props["Energy Level"] = notion._prop_select(payload["energy_level"])

    # Estimated duration
    if payload.get("estimated_duration"):
        props["Estimated Duration (min)"] = notion._prop_number(
            payload["estimated_duration"]
        )

    # Google calendar linkage
    if payload.get("google_event_id"):
        props["Google Event ID"] = notion._prop_text(
            payload["google_event_id"]
        )

    # Quest / Map relations (ONLY if present)
    if payload.get("quest_id"):
        props["Quest"] = notion._prop_relation([payload["quest_id"]])

    if payload.get("map_id"):
        props["Map"] = notion._prop_relation([payload["map_id"]])

    # --------------------------------------------------
    # CREATE NOTION PAGE
    # --------------------------------------------------
    body = {
        "parent": {"database_id": notion.db_ids["tasks"]},
        "properties": props,
    }

    res = notion._request("POST", "/pages", json_body=body)

    logger.info("Task created in Notion: %s", res.get("id"))

    # --------------------------------------------------
    # AGENT OUTPUT (NO DECISIONS)
    # --------------------------------------------------
    state.add_agent_output(
        agent="task_agent",
        result={
            "action": "task_created",
            "task_id": res.get("id"),
        },
        score=0.95,
    )

    return state

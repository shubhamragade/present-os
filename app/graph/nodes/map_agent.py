# app/graph/nodes/map_agent.py
"""
MAP Agent for PresentOS (PDF-COMPLIANT)

ROLE:
- Create MAPs (Milestones / Strategy nodes)
- MAPs must belong to a Quest
- Writes to Notion only
- NO reasoning
- NO routing
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from app.graph.state import PresentOSState
from app.integrations.notion_client import NotionClient
from app.utils.instruction_utils import get_instruction

logger = logging.getLogger("presentos.map_agent")


def run_map_node(
    state: PresentOSState,
    notion: NotionClient,
) -> PresentOSState:
    """
    Expected Parent instructions:
    {
        "intent": "create_map",
        "payload": {
            "title": str,
            "quest_id": str,
            "priority": "High|Medium|Low",
            "type": "Execution|Planning|Learning"
        }
    }
    """

    # 🔒 ACTIVATION GUARD
    if "map_agent" not in state.activated_agents:
        return state
    instruction = get_instruction(state, "map_agent")
    if not instruction:
        return state

    if instruction.get("intent") != "create_map":
        return state

    payload = instruction.get("payload", {})


    quest_id = payload.get("quest_id")
    title = payload.get("title")

    if not quest_id or not title:
        state.add_agent_output(
            "map_agent",
            {"status": "error", "reason": "missing_required_fields"},
            score=0.0,
        )
        return state

    props: Dict[str, Any] = {
        "Name": notion._prop_title(title),
        "Quest": {"relation": [{"id": quest_id}]},
        "Status": notion._prop_select("In Progress"),
    }

    if payload.get("priority"):
        props["Priority"] = notion._prop_select(payload["priority"])

    if payload.get("type"):
        props["Type"] = notion._prop_select(payload["type"])

    body = {
        "parent": {"database_id": notion.db_ids["maps"]},
        "properties": props,
    }

    try:
        res = notion._request("POST", "/pages", json_body=body)

        state.add_agent_output(
            "map_agent",
            {
                "action": "map_created",
                "map_id": res.get("id"),
                "quest_id": quest_id,
            },
            score=0.95,
        )

    except Exception as e:
        logger.exception("MAPAgent failed")
        state.add_agent_output(
            "map_agent",
            {"status": "error", "error": str(e)},
            score=0.0,
        )

    return state

# app/graph/nodes/contact_agent.py

from __future__ import annotations

import logging
from typing import Dict, Any

from app.graph.state import PresentOSState
from app.integrations.notion_client import NotionClient
from app.utils.instruction_utils import get_instruction

logger = logging.getLogger("presentos.contact_agent")


def run_contact_node(state: PresentOSState) -> PresentOSState:
    """
    Contact Agent (OS-COMPLIANT)

    RESPONSIBILITIES:
    - Lookup contact in Notion (system of record)
    - Emit contact_found / contact_missing
    - NEVER create or update contacts
    - NEVER ask questions
    """
    if "contact_agent" not in state.activated_agents:
        return state
    decision = state.parent_decision or {}
    instruction = get_instruction(state, "contact_agent")
    if not instruction:
        return state

    contact_name = instruction.get("contact_name")
    contact_email = instruction.get("contact_email")


    if not contact_name and not contact_email:
        state.add_agent_output(
            "contact_agent",
            {"status": "ignored", "reason": "no_contact_identifier"},
            score=0.0,
        )
        return state

    notion = NotionClient.from_env()

    try:
        contact = None

        if contact_name:
            contact = notion.find_contact_by_name(contact_name)

        if not contact:
            state.add_agent_output(
                "contact_agent",
                {
                    "status": "contact_missing",
                    "contact_name": contact_name,
                    "contact_email": contact_email,
                },
                score=0.0,
            )
            return state

        state.add_agent_output(
            "contact_agent",
            {
                "status": "contact_found",
                "contact_id": contact["id"],
                "name": contact["name"],
                "email": contact["email"],
                "tone_preference": contact.get("tone_preference"),
                "relationship": contact.get("relationship"),
            },
            score=0.95,
        )
        return state

    except Exception as e:
        logger.exception("ContactAgent failed")
        state.add_agent_output(
            "contact_agent",
            {"status": "error", "error": str(e)},
            score=0.0,
        )
        return state

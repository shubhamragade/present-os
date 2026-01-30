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
    - Add/Update notes and contact details
    - Emit contact_found / contact_updated / contact_missing
    """
    if "contact_agent" not in state.activated_agents:
        return state
        
    instruction = get_instruction(state, "contact_agent")
    if not instruction:
        return state

    intent = instruction.get("intent")
    payload = instruction.get("payload", {})
    
    contact_name = instruction.get("contact_name") or payload.get("name")
    contact_email = instruction.get("contact_email") or payload.get("email")
    note = payload.get("note") or payload.get("text")

    if not contact_name and not contact_email:
        state.add_agent_output(
            "contact_agent",
            {"status": "ignored", "reason": "no_contact_identifier"},
            score=0.0,
        )
        return state

    notion = NotionClient.from_env()

    try:
        # Handle Update/Add Note Intent
        if intent in ["add_note", "update_contact", "create_contact"]:
            logger.info(f"Updating/Creating contact: {contact_name}")
            
            additional = {}
            if note:
                # Get existing contact to append note if desired, or just overwrite
                # For now, we'll overwrite or just set it
                additional["Notes"] = {"rich_text": [{"type": "text", "text": {"content": note}}]}
            
            if payload.get("phone"):
                additional["Phone"] = {"phone_number": payload.get("phone")}
            
            contact = notion.create_or_update_contact(
                name=contact_name,
                email=contact_email,
                additional=additional
            )
            
            state.add_agent_output(
                "contact_agent",
                {
                    "status": "contact_updated",
                    "action": "note_saved" if note else "updated",
                    "contact_id": contact["id"],
                    "name": contact_name,
                    "note": note
                },
                score=1.0,
            )
            return state

        # Default: Lookup
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
                "phone": contact.get("phone"), # Added Phone
                "tone_preference": contact.get("tone_preference"),
                "relationship": contact.get("relationship"),
                "notes": contact.get("notes") # Added this too
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

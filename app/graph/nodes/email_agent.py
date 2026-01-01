
from __future__ import annotations
import logging
from typing import Dict, Any

from app.graph.state import PresentOSState
from app.services.email_triage import triage_email
from app.utils.instruction_utils import get_instruction

logger = logging.getLogger("presentos.email_agent")


def run_email_node(state: PresentOSState) -> PresentOSState:
    """
    Email Agent (PDF-COMPLIANT)
    ROLE:
    - Understand incoming email
    - Decide WHAT is needed (intelligence only)
    - Emit structured signals
    - NEVER route
    - NEVER execute side effects
    """

    decision = state.parent_decision or {}
    instruction = get_instruction(state, "email_agent")
    if not instruction:
        return state

    email = instruction.get("email")

    if not email:
        state.add_agent_output(
            agent="email_agent",
            result={"status": "ignored", "reason": "no_email_payload"},
            score=0.0,
        )
        return state

    try:
        triage = triage_email(email)

        result = {
            "email_id": email.get("id"),
            "thread_id": email.get("thread_id"),
            "from": email.get("from"),
            "subject": email.get("subject"),
            "received_at": email.get("received_at"),

            "actionable": triage["actionable"],
            "category": triage["category"],
            "priority": triage["priority"],
            "paei": triage["paei"],

            "needs_response": triage["needs_response"],
            "needs_calendar": triage["needs_calendar"],
            "needs_task": triage["needs_task"],

            "draft_reply": triage.get("draft_reply"),
            "summary": triage["summary"],
        }

        state.meta.setdefault("email_signals", []).append({
            "needs_task": triage["needs_task"],
            "needs_calendar": triage["needs_calendar"],
            "needs_response": triage["needs_response"],
            "email_context": result,
        })

        state.add_agent_output(
            agent="email_agent",
            result=result,
            score=triage.get("confidence", 0.6),
        )

        return state

    except Exception as e:
        logger.exception("EmailAgent failed")
        state.add_agent_output(
            agent="email_agent",
            result={"status": "error", "error": str(e)},
            score=0.0,
        )
        return state

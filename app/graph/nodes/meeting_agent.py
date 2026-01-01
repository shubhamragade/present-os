from __future__ import annotations

import logging
from typing import Dict, Any, List

from app.graph.state import PresentOSState
from app.services.meeting_analysis import analyze_meeting
from app.utils.instruction_utils import get_instruction

logger = logging.getLogger("presentos.meeting_agent")


def run_meeting_node(state: PresentOSState) -> PresentOSState:
    """
    Meeting Agent (PDF-COMPLIANT)

    ROLE:
    - Process COMPLETED meetings only
    - Consume meeting transcript / summary (e.g. Fireflies)
    - Extract decisions, action items, follow-ups
    - Emit structured intelligence
    - NEVER schedule
    - NEVER create tasks
    - NEVER send emails
    - NEVER route execution
    """

    decision = state.parent_decision or {}
    instruction = get_instruction(state, "meeting_agent")
    if not instruction:
        return state

    meeting = instruction.get("meeting")


    if not meeting:
        state.add_agent_output(
            agent="meeting_agent",
            result={"status": "ignored", "reason": "no_meeting_payload"},
            score=0.0,
        )
        return state

    # Guard: meeting must be completed
    if not meeting.get("completed", False):
        state.add_agent_output(
            agent="meeting_agent",
            result={"status": "ignored", "reason": "meeting_not_completed"},
            score=0.0,
        )
        return state

    try:
        analysis = analyze_meeting(meeting)

        result = {
            "meeting_id": meeting.get("id"),
            "title": meeting.get("title"),
            "started_at": meeting.get("started_at"),
            "ended_at": meeting.get("ended_at"),

            # Extracted intelligence
            "decisions": analysis.get("decisions", []),
            "action_items": analysis.get("action_items", []),
            "follow_ups": analysis.get("follow_ups", []),
            "risks": analysis.get("risks", []),

            # Signals
            "needs_tasks": bool(analysis.get("action_items")),
            "needs_email_followup": bool(analysis.get("follow_ups")),
            "needs_memory": True,

            # Summary
            "summary": analysis.get("summary"),
        }

        state.add_agent_output(
            agent="meeting_agent",
            result=result,
            score=analysis.get("confidence", 0.7),
        )

        return state

    except Exception as e:
        logger.exception("MeetingAgent failed")
        state.add_agent_output(
            agent="meeting_agent",
            result={"status": "error", "error": str(e)},
            score=0.0,
        )
        return state

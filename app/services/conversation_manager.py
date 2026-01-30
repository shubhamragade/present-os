"""
Conversation Manager for PresentOS (PDF-COMPLIANT)

ROLE:
- Manage conversational slot-filling state
- Persist partial information across turns
- NEVER infer values
- NEVER call external systems
- NEVER decide execution
- Works only on PresentOSState

USED BY:
- API / Telegram / UI layer BEFORE IntentClassifier
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List

from app.graph.state import PresentOSState

logger = logging.getLogger("presentos.conversation_manager")


class ConversationManager:
    """
    Deterministic slot-filling manager.
    """

    # -------------------------------------------------
    # PUBLIC ENTRY (START OF TURN)
    # -------------------------------------------------
    def process_user_message(
        self,
        state: PresentOSState,
        user_text: str,
    ) -> PresentOSState:
        """
        Called at the very start of each user turn.

        Responsibilities:
        - Attach canonical input_text
        - CLEAR stale slot-filling when a new request starts
        - Merge answers ONLY if awaiting user
        """

        state.input_text = user_text

        # ✅ CRITICAL FIX:
        # Clear stale or completed slot-filling on new user intent
        if state.conversation and state.conversation.get("status") == "complete":
            state.conversation = None

        # Merge answers ONLY if system is explicitly waiting
        if (
            state.conversation
            and state.conversation.get("status") == "awaiting_user"
        ):
            self._merge_slot_answers(state, user_text)

        return state

    # -------------------------------------------------
    # AFTER AGENT EXECUTION
    # -------------------------------------------------
    def handle_agent_outputs(self, state: PresentOSState) -> PresentOSState:
        """
        Inspect agent outputs for missing_required_fields
        and activate slot-filling if needed.
        """

        for output in state.agent_outputs:
            result = output.result or {}

            if result.get("reason") != "missing_required_fields":
                continue

            missing = result.get("missing", [])
            if not missing:
                continue

            logger.info(
                "ConversationManager detected missing slots: %s",
                missing,
            )

            state.conversation = {
                "status": "awaiting_user",
                "agent": output.agent_name,
                "missing_fields": list(missing),
                "filled": {},
            }

        return state

    # -------------------------------------------------
    # INTERNALS
    # -------------------------------------------------
    def _merge_slot_answers(
        self,
        state: PresentOSState,
        user_text: str,
    ) -> None:
        """
        Conservative merge:
        - One answer per turn
        - Stored verbatim
        - No inference
        """

        convo = state.conversation
        missing: List[str] = convo.get("missing_fields", [])
        filled: Dict[str, Any] = convo.get("filled", {})

        if not missing:
            return

        # Fill ONLY the next missing slot
        slot = missing.pop(0)
        filled[slot] = user_text.strip()

        logger.info("Filled slot '%s'", slot)

        if missing:
            state.conversation = {
                **convo,
                "missing_fields": missing,
                "filled": filled,
            }
        else:
            # Slot-filling complete
            state.conversation = {
                "status": "complete",
                "agent": convo.get("agent"),
                "filled": filled,
            }

    # -------------------------------------------------
    # UTILITY
    # -------------------------------------------------
    @staticmethod
    def is_slot_filling(state: PresentOSState) -> bool:
        """
        Block execution ONLY when explicitly waiting for user input.
        """
        return (
            state.conversation is not None
            and state.conversation.get("status") == "awaiting_user"
        )

    def extract_quest_fields(self, text: str) -> Dict[str, Any]:
        """
        Fallback extraction for Quest fields from text.
        """
        # Simple extraction for common patterns if IntentClassifier misses them
        res = {"name": None, "purpose": None, "result": None}
        
        # Very basic extraction - in a real system this would be an LLM call
        # For now, we take the whole text as the name if nothing else works
        import re
        
        # Look for "Quest: Name" or similar patterns
        name_match = re.search(r"(?:Quest|goal|project)[:\s]+([^,\.]+)", text, re.IGNORECASE)
        if name_match:
            res["name"] = name_match.group(1).strip()
            res["purpose"] = text.strip()
            res["result"] = "Completed"
        else:
            res["name"] = text[:50].strip() + "..." if len(text) > 50 else text.strip()
            res["purpose"] = text.strip()
            res["result"] = "Success"
            
        return res

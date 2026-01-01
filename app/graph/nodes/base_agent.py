# app/graph/nodes/base_agent.py
"""
Base Agent for Present OS.

WHY THIS EXISTS:
- Enforce identical structure across ALL agents
- Prevent graph crashes
- Centralize logging, validation, and safety
- Keep agents dumb and reliable

PDF RULES:
- Agents do ONE thing
- Agents NEVER route
- Agents NEVER access Pinecone
- Agents ONLY mutate state
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional

from app.graph.state import PresentOSState

logger = logging.getLogger("presentos.agent")


class AgentExecutionError(Exception):
    """Raised when an agent fails safely."""


class BaseAgent:
    """
    Abstract base class for all child agents.

    Every agent MUST:
    - inherit from BaseAgent
    - implement `execute()`
    """

    agent_name: str = "base_agent"

    # -----------------------------
    # Entry point (LangGraph-safe)
    # -----------------------------
    def run(self, state: PresentOSState) -> PresentOSState:
        """
        Standard execution wrapper.
        NEVER override this method in child agents.
        """

        logger.info("[%s] started", self.agent_name)

        try:
            instructions = self._extract_instructions(state)

            if not instructions:
                logger.warning("[%s] no instructions provided", self.agent_name)
                return state

            result = self.execute(state, instructions)

            self._record_agent_output(state, result)

            logger.info("[%s] completed successfully", self.agent_name)
            return state

        except Exception as e:
            logger.exception("[%s] failed safely: %s", self.agent_name, e)
            self._record_error(state, str(e))
            return state

    # -----------------------------
    # MUST be implemented
    # -----------------------------
    def execute(
        self,
        state: PresentOSState,
        instructions: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Perform ONE atomic action.

        Must return:
        - dict (agent output), or
        - None
        """
        raise NotImplementedError("Agents must implement execute()")

    # -----------------------------
    # Helpers
    # -----------------------------
    def _extract_instructions(self, state: PresentOSState) -> Dict[str, Any]:
        """
        Read instructions written by ParentNode.
        """
        if not state.parent_decision:
            return {}

        return state.parent_decision.get("instructions", {}) or {}

    def _record_agent_output(
        self,
        state: PresentOSState,
        output: Optional[Dict[str, Any]],
    ) -> None:
        """
        Save agent output into state for downstream visibility.
        """
        if output is None:
            return

        state.add_agent_output(self.agent_name, output)

    def _record_error(self, state: PresentOSState, error: str) -> None:
        """
        Record agent error safely without crashing system.
        """
        state.add_agent_output(
            self.agent_name,
            {
                "error": error,
                "status": "failed",
            },
        )

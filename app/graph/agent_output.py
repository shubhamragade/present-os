# app/graph/agent_output.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class AgentOutput:
    """
    Standard container for agent execution results.

    PDF COMPLIANCE:
    - Holds facts only
    - No reasoning
    - No decisions
    """

    agent_name: str
    result: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None

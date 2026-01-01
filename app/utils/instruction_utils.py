from typing import Dict, Any, Optional, List
from app.graph.state import PresentOSState


def get_instruction(
    state: PresentOSState,
    agent_name: str,
) -> Optional[Dict[str, Any]]:
    """
    Safely extract THIS agent's instruction from ParentNode output.
    """
    decision = state.parent_decision or {}
    instructions: List[Dict[str, Any]] = decision.get("instructions", [])

    if not isinstance(instructions, list):
        return None

    return next(
        (i for i in instructions if i.get("agent") == agent_name),
        None,
    )

from datetime import datetime
from typing import Dict, Any
from app.services.rag_service import RAGService


class MemoryWriter:
    """
    Policy-controlled memory writer.
    ParentAgent ONLY.
    """

    def __init__(self, rag: RAGService):
        self.rag = rag

    def maybe_write(self, decision_context: Dict[str, Any]) -> None:
        confidence = decision_context.get("confidence", 0.0)
        risk = decision_context.get("risk")
        execution_mode = decision_context.get("execution_mode")

        if confidence < 0.75:
            return
        if risk == "high":
            return
        if execution_mode == "ask_user":
            return

        summary = (
            f"User tends to execute actions in '{execution_mode}' mode "
            f"when energy is {decision_context['energy']['capacity']}."
        )

        self.rag.store_memory(
            content=summary,
            memory_type="preference",
            metadata={
                "source": "parent_agent",
                "execution_mode": execution_mode,
                "energy": decision_context["energy"]["capacity"],
            },
        )

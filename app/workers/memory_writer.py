# app/workers/memory_writer.py
"""
Background Memory Writer for PresentOS

RULES:
- Runs AFTER execution
- Reads agent_outputs & planned_actions
- Writes memory via RAGService ONLY
"""

from __future__ import annotations

import logging
from typing import Dict, Any

from app.graph.state import PresentOSState
from app.services.memory_policy import (
    should_store_memory,
    infer_memory_type,
    build_memory_content,
)
from app.services.rag_service import get_rag_service

logger = logging.getLogger("presentos.memory_writer")


def process_memory(state: PresentOSState) -> None:
    """
    Persist durable memories based on execution outcomes.
    """

    rag = get_rag_service()

    events = []

    # Agent outputs
    for out in state.agent_outputs:
        events.append(out.result)

    # Planned actions (XP events, etc.)
    events.extend(state.planned_actions)

    for event in events:
        if not should_store_memory(event):
            continue

        memory_type = infer_memory_type(event)
        content = build_memory_content(event)

        rag.store_memory(
            content=content,
            memory_type=memory_type,
            metadata={
                "paei": event.get("paei"),
                "quest_id": event.get("quest_id"),
                "map_id": event.get("map_id"),
            },
        )

        logger.info("Memory stored: %s", memory_type)

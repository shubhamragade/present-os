# app/services/context_loader.py
"""
Context Loader for PresentOS

ROLE:
- Load active Quest + MAP into state
- READ-ONLY
- No decisions
"""

from __future__ import annotations
from typing import Optional

from app.graph.state import PresentOSState
from app.integrations.notion_client import NotionClient


def load_context(state: PresentOSState, notion: NotionClient) -> PresentOSState:
    """
    Inject Quest and MAP snapshots into state before ParentAgent.
    """

    # Load active quest
    quest = notion.get_active_quest()
    if quest:
        state.quests[quest["id"]] = quest

    # Load highest priority MAP
    map_ = notion.get_active_map()
    if map_:
        state.maps[map_["id"]] = map_

    return state

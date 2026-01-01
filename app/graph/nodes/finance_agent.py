# app/graph/nodes/finance_agent.py
from __future__ import annotations
from typing import Optional
from app.graph.state import PresentOSState
from app.integrations.notion_client import NotionClient

def run_finance_node(state: PresentOSState, notion: Optional[NotionClient] = None) -> PresentOSState:
    """
    Dummy finance agent - returns state unchanged
    
    This is a temporary placeholder since you don't want to implement
    the finance agent right now.
    """
    return state
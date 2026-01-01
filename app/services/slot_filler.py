from typing import Dict, Any
from app.services.slot_schema import QUEST_SLOTS

def get_next_missing_slot(slots: Dict[str, Any]):
    for key, meta in QUEST_SLOTS.items():
        if meta["required"] and not slots.get(key):
            return key, meta
    return None, None

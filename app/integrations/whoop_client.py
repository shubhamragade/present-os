"""
WHOOP Client (Interface + Dummy Implementation)

PDF COMPLIANCE:
- No real WHOOP API calls
- Deterministic local signals
- Swappable with real WHOOP later
- ParentAgent never depends on WHOOP directly
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import random


# ---------------------------------------------------------
# Data Model
# ---------------------------------------------------------
@dataclass
class WhoopSignal:
    recovery_score: float      # 0.0 – 1.0
    strain_score: float        # 0.0 – 1.0
    sleep_score: float         # 0.0 – 1.0
    timestamp: datetime


# ---------------------------------------------------------
# Interface
# ---------------------------------------------------------
class WhoopClient:
    def get_signal(self) -> WhoopSignal:
        raise NotImplementedError


# ---------------------------------------------------------
# Dummy Client (LOCAL ONLY)
# ---------------------------------------------------------
class DummyWhoopClient(WhoopClient):
    """
    Deterministic WHOOP simulator.
    """

    def __init__(self, seed: int | None = None):
        self.random = random.Random(seed)

    def get_signal(self) -> WhoopSignal:
        return WhoopSignal(
            recovery_score=round(self.random.uniform(0.3, 0.9), 2),
            strain_score=round(self.random.uniform(0.2, 0.8), 2),
            sleep_score=round(self.random.uniform(0.4, 0.95), 2),
            timestamp=datetime.utcnow(),
        )

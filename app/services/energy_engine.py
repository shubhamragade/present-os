from dataclasses import dataclass
from typing import Optional
from app.graph.state import PresentOSState

@dataclass
class EnergyResult:
    energy_level: float
    capacity: str            # low | medium | high
    deep_work_recommended: bool
    meeting_tolerance: str   # avoid | limited | normal
    execution_bias: str      # recovery | maintenance | push
    reasoning: str


def compute_energy_from_state(
    *,
    state: PresentOSState,
    urgency: bool = False,
) -> EnergyResult:
    """
    PURE energy evaluation.
    NO PAEI.
    NO intent logic.
    """

    level = state.energy_level or 0.5

    # WHOOP override (if present)
    if state.whoop_recovery_score is not None:
        level = state.whoop_recovery_score

    if urgency:
        level -= 0.1

    level = max(0.0, min(level, 1.0))

    if level < 0.3:
        return EnergyResult(
            energy_level=level,
            capacity="low",
            deep_work_recommended=False,
            meeting_tolerance="avoid",
            execution_bias="recovery",
            reasoning="Low physiological energy",
        )

    if level < 0.6:
        return EnergyResult(
            energy_level=level,
            capacity="medium",
            deep_work_recommended=False,
            meeting_tolerance="limited",
            execution_bias="maintenance",
            reasoning="Moderate energy",
        )

    return EnergyResult(
        energy_level=level,
        capacity="high",
        deep_work_recommended=True,
        meeting_tolerance="normal",
        execution_bias="push",
        reasoning="High energy state",
    )

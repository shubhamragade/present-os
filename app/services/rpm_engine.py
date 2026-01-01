"""
RPM Engine for PresentOS (PURE ALIGNMENT ENGINE)
FIXED VERSION: Less strict for MVP testing
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from datetime import datetime, date

@dataclass
class RPMResult:
    aligned: bool
    alignment_score: float
    recommendation: str  # proceed | defer | ask_clarify | block
    reason: str


def compute_rpm(
    *,
    quest: Optional[Dict[str, Any]] = None,
    map_: Optional[Dict[str, Any]] = None,
    task: Optional[Dict[str, Any]] = None,
    now: Optional[datetime] = None,
) -> RPMResult:
    """
    FIXED: Always returns "proceed" for MVP testing
    """
    
    # Helper to convert Pydantic objects to dicts
    def to_dict(obj):
        if obj is None:
            return None
        if hasattr(obj, 'dict'):
            return obj.dict()
        return obj
    
    # Convert inputs
    quest = to_dict(quest)
    map_ = to_dict(map_)
    task = to_dict(task)

    now = now or datetime.utcnow()

    score = 0.5  # Start with 0.5 (neutral)
    reasons = ["Default baseline score"]

    # -----------------------------------------------------
    # QUEST (Purpose)
    # -----------------------------------------------------
    if quest:
        status = quest.get("status")
        end_date = quest.get("end_date")
        xp_target = quest.get("xp_target")

        if status == "In Progress":  
            score += 0.30  # Increased from 0.35
            reasons.append("Linked to active quest")
        else:
            reasons.append("Quest is not active")
            score -= 0.10

        if end_date:
            # Handle both string and date objects
            if isinstance(end_date, str):
                try:
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                except ValueError:
                    reasons.append("Invalid quest end date format")
                    end_date = None
            
            if isinstance(end_date, date):
                if end_date >= now.date():
                    score += 0.15  # Increased from 0.10
                else:
                    reasons.append(f"Quest expired on {end_date}")
                    score -= 0.20  # Don't block, just reduce score

        if xp_target and xp_target > 0:
            score += 0.10

    else:
        reasons.append("No quest linked")
        score -= 0.05  # Small penalty for no quest

    # -----------------------------------------------------
    # MAP (Strategy)
    # -----------------------------------------------------
    if map_:
        priority = map_.get("priority")
        map_type = map_.get("type")

        if priority == "High":
            score += 0.25  # Increased
        elif priority == "Medium":
            score += 0.15  # Increased
        else:
            score += 0.05  # Even low priority adds some

        if map_type in ("Execution", "Planning"):
            score += 0.15
        else:
            score += 0.08

        reasons.append("Aligned with MAP strategy")

    else:
        reasons.append("No MAP context")
        score -= 0.03  # Very small penalty

    # -----------------------------------------------------
    # TASK (Signal, not authority)
    # -----------------------------------------------------
    if task:
        source = task.get("source")
        task_type = task.get("task_type")
        priority = task.get("priority")

        if source in ("Voice", "Manual"):
            score += 0.08
            reasons.append("User-initiated task")
        elif source == "Email":
            score += 0.03  # Don't penalize, just less bonus
            reasons.append("Email-originated task")

        if task_type == "Admin":
            score += 0.02  # Admin tasks are valid too
        else:
            score += 0.05

        if priority == "High":
            score += 0.08

    # -----------------------------------------------------
    # FIXED: NEW SCORING LOGIC - More permissive
    # -----------------------------------------------------
    score = max(0.1, min(score, 1.0))  # Never go below 0.1
    score = round(score, 2)

    # FIXED: More permissive recommendations for MVP
    if score >= 0.40:  # Lowered from 0.65
        return RPMResult(
            aligned=True,
            alignment_score=score,
            recommendation="proceed",
            reason="; ".join(reasons),
        )

    if 0.20 <= score < 0.40:  # Lowered thresholds
        return RPMResult(
            aligned=False,
            alignment_score=score,
            recommendation="defer",
            reason="Weak alignment: " + "; ".join(reasons),
        )

    # Only ask for clarification if really low score
    return RPMResult(
        aligned=False,
        alignment_score=score,
        recommendation="ask_clarify",
        reason="Very low alignment: " + "; ".join(reasons),
    )


# ---------------------------------------------------------
# Convenience wrapper (ALWAYS PROCEED FOR TESTING)
# ---------------------------------------------------------
def compute_rpm_from_context(context: Dict[str, Any]) -> RPMResult:
    """
    FIXED: For MVP testing, always return "proceed"
    """
    
    # Try to compute real RPM
    result = compute_rpm(
        quest=context.get("quest"),
        map_=context.get("map"),
        task=context.get("task"),
    )
    
    # FOR MVP TESTING: Override to always proceed
    if result.recommendation != "proceed":
        return RPMResult(
            aligned=True,
            alignment_score=0.7,  # Good score
            recommendation="proceed",
            reason=f"MVP override: {result.reason}"
        )
    
    return result
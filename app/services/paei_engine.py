"""
PAEI Decision Engine for PresentOS (PDF-COMPLIANT)

PDF REQUIREMENTS MET:
- Computes which PAEI role should execute
- Provides concrete execution guidance  
- Determines XP awards based on context
- Considers WHOOP recovery, team morale, deadlines
- Returns actionable decisions, not just scores
"""

from __future__ import annotations
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
from enum import Enum


class PAEIRole(str, Enum):
    PRODUCER = "P"
    ADMINISTRATOR = "A"
    ENTREPRENEUR = "E"
    INTEGRATOR = "I"


@dataclass
class PAEIDecision:
    """CONCRETE decision that changes behavior"""
    role: PAEIRole
    xp_amount: int
    email_style: str
    task_approach: str
    calendar_buffer: str
    priority_level: str
    reasoning: str
    execution_notes: List[str]


class PAEIDecisionEngine:
    """
    Makes REAL decisions that change agent behavior.
    
    From PDF Page 4-5:
    "Parent Agent should consult ALL 4 PAEI perspectives before making ANY decision"
    "Then decides optimal approach based on context"
    """
    
    def __init__(self):
        self.decision_history = deque(maxlen=100)
        
    def decide(
        self,
        intent_signals: Dict[str, bool],
        context: Dict[str, Any]
    ) -> PAEIDecision:
        """
        Main decision function - returns HOW to execute.
        
        Args:
            intent_signals: From intent classifier
            context: Current state (WHOOP, morale, deadlines)
            
        Returns:
            Concrete instructions for agents
        """
        
        # 1. Get base role from intent
        base_role = self._analyze_intent(intent_signals)
        
        # 2. Apply context adjustments (PDF Page 40-41)
        final_role = self._apply_context_adjustments(base_role, context)
        
        # 3. Get execution details
        execution_details = self._get_execution_details(final_role, context)
        
        # 4. Calculate XP (PDF requirement)
        xp_amount = self._calculate_xp(final_role, intent_signals, context)
        
        # 5. Update history
        self.decision_history.append(final_role)
        
        return PAEIDecision(
            role=final_role,
            xp_amount=xp_amount,
            **execution_details
        )
    
    def _analyze_intent(self, signals: Dict[str, bool]) -> PAEIRole:
        """Which PAEI role does this intent need?"""
        
        scores = {role: 0.0 for role in PAEIRole}
        
        # Producer (fast execution)
        if signals.get("urgency"): scores[PAEIRole.PRODUCER] += 0.8
        if signals.get("deadline"): scores[PAEIRole.PRODUCER] += 0.6
        if signals.get("execution_focus"): scores[PAEIRole.PRODUCER] += 0.7
        
        # Administrator (structure)
        if signals.get("administrative"): scores[PAEIRole.ADMINISTRATOR] += 0.9
        if signals.get("structured"): scores[PAEIRole.ADMINISTRATOR] += 0.7
        if signals.get("documentation"): scores[PAEIRole.ADMINISTRATOR] += 0.6
        
        # Entrepreneur (vision)
        if signals.get("exploratory"): scores[PAEIRole.ENTREPRENEUR] += 0.8
        if signals.get("strategic"): scores[PAEIRole.ENTREPRENEUR] += 0.9
        if signals.get("creative"): scores[PAEIRole.ENTREPRENEUR] += 0.7
        
        # Integrator (people)
        if signals.get("involves_people"): scores[PAEIRole.INTEGRATOR] += 0.8
        if signals.get("emotional_tone"): scores[PAEIRole.INTEGRATOR] += 0.9
        if signals.get("relationship_focus"): scores[PAEIRole.INTEGRATOR] += 0.8
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _apply_context_adjustments(
        self,
        base_role: PAEIRole,
        context: Dict[str, Any]
    ) -> PAEIRole:
        """Apply PDF's context-aware weighting (Page 40-41)"""
        
        whoop_recovery = context.get("whoop_recovery", 70)
        team_morale = context.get("team_morale", "stable")
        deadline_pressure = context.get("deadline_pressure", "low")
        
        # PDF Page 40: Low recovery → prioritize relationships
        if whoop_recovery < 40:
            if base_role == PAEIRole.PRODUCER:
                return PAEIRole.INTEGRATOR  # Don't push when tired
        
        # PDF Page 40: Critical deadline → prioritize execution
        if deadline_pressure == "critical":
            return PAEIRole.PRODUCER  # Get it done
        
        # PDF Page 5: Fragile team morale → prioritize harmony
        if team_morale == "fragile":
            return PAEIRole.INTEGRATOR
        
        # Check PAEI balance
        if len(self.decision_history) >= 20:
            distribution = self._get_current_distribution()
            neglected = min(distribution.items(), key=lambda x: x[1])[0]
            if distribution[neglected] < 0.15:
                return neglected  # Rebalance
        
        return base_role
    
    def _get_execution_details(
        self,
        role: PAEIRole,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """CONCRETE instructions that agents MUST follow"""
        
        if role == PAEIRole.INTEGRATOR:
            return {
                "email_style": "empathetic",
                "task_approach": "include team check-ins",
                "calendar_buffer": "15min",
                "priority_level": "medium",
                "reasoning": f"Team harmony focus (morale: {context.get('team_morale', 'stable')})",
                "execution_notes": [
                    "Acknowledge team effort",
                    "Show leadership responsibility",
                    "Schedule 1:1 check-ins if needed"
                ]
            }
        
        elif role == PAEIRole.PRODUCER:
            return {
                "email_style": "bullet_points",
                "task_approach": "time-boxed execution",
                "calendar_buffer": "5min",
                "priority_level": "high",
                "reasoning": f"Fast execution required (deadline: {context.get('deadline_pressure', 'low')})",
                "execution_notes": [
                    "Time-box to 15min",
                    "Skip documentation",
                    "Focus on shipping"
                ]
            }
        
        elif role == PAEIRole.ADMINISTRATOR:
            return {
                "email_style": "structured",
                "task_approach": "follow process",
                "calendar_buffer": "10min",
                "priority_level": "medium",
                "reasoning": "Systematic work required",
                "execution_notes": [
                    "Document thoroughly",
                    "Follow established protocols",
                    "Include all stakeholders"
                ]
            }
        
        else:  # ENTREPRENEUR
            return {
                "email_style": "visionary",
                "task_approach": "creative exploration",
                "calendar_buffer": "20min",
                "priority_level": "medium",
                "reasoning": "Strategic/visionary focus",
                "execution_notes": [
                    "Think big picture",
                    "Challenge assumptions",
                    "Focus on long-term impact"
                ]
            }
    
    def _calculate_xp(
        self,
        role: PAEIRole,
        signals: Dict[str, bool],
        context: Dict[str, Any]
    ) -> int:
        """Calculate XP based on PDF requirements"""
        
        base_xp = {
            PAEIRole.PRODUCER: 5,
            PAEIRole.ADMINISTRATOR: 8,
            PAEIRole.ENTREPRENEUR: 10,
            PAEIRole.INTEGRATOR: 7
        }
        
        xp = base_xp[role]
        
        # Context bonuses
        whoop_recovery = context.get("whoop_recovery", 70)
        if whoop_recovery < 40 and role == PAEIRole.INTEGRATOR:
            xp += 3  # Extra for self-care during low recovery
        
        if context.get("deadline_pressure") == "critical" and role == PAEIRole.PRODUCER:
            xp += 5  # Extra for execution under pressure
        
        if signals.get("urgency") and role == PAEIRole.PRODUCER:
            xp += 2  # Urgent tasks get bonus
        
        return max(1, xp)
    
    def _get_current_distribution(self) -> Dict[PAEIRole, float]:
        """Get current PAEI distribution"""
        total = len(self.decision_history)
        if total == 0:
            return {role: 0.25 for role in PAEIRole}
        
        distribution = {}
        for role in PAEIRole:
            count = sum(1 for r in self.decision_history if r == role)
            distribution[role] = count / total
        
        return distribution


# Global instance
_decision_engine = PAEIDecisionEngine()


def get_paei_decision(
    intent_signals: Dict[str, bool],
    context: Dict[str, Any]
) -> PAEIDecision:
    """Main API - gets concrete decision that changes behavior"""
    return _decision_engine.decide(intent_signals, context)


# Backward compatibility
@dataclass
class PAEIResult:
    P: float
    A: float
    E: float
    I: float
    dominant: str


def compute_paei_from_aggregated(contexts: List[Dict[str, Any]]) -> PAEIResult:
    """Legacy function for backward compatibility"""
    merged = defaultdict(bool)
    for ctx in contexts:
        for k, v in ctx.items():
            merged[k] = merged[k] or bool(v)
    
    # Simple calculation for compatibility
    P = 0.3 if merged.get("urgency") else 0.1
    A = 0.4 if merged.get("administrative") else 0.1
    E = 0.2 if merged.get("exploratory") else 0.1
    I = 0.5 if merged.get("involves_people") else 0.1
    
    scores = {"P": P, "A": A, "E": E, "I": I}
    dominant = max(scores, key=scores.get)
    
    return PAEIResult(P=P, A=A, E=E, I=I, dominant=dominant)
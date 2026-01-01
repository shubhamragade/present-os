"""
PresentOS State - PDF-Compliant

PDF REQUIREMENTS MET:
- Tracks PAEI context
- Stores RPM goals
- Maintains execution history
- JSON serializable
- LangGraph compatible
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field, validator
from enum import Enum


# ---------------------------------------------------------
# Enums
# ---------------------------------------------------------

class PAEIRole(str, Enum):
    PRODUCER = "P"
    ADMINISTRATOR = "A"
    ENTREPRENEUR = "E"
    INTEGRATOR = "I"


class EnergyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------------------------------------------------------
# Helper Models
# ---------------------------------------------------------

class AgentOutput(BaseModel):
    agent_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    result: Dict[str, Any] = Field(default_factory=dict)
    paei_role: Optional[PAEIRole] = None
    score: float = 0.0
    meta: Dict[str, Any] = Field(default_factory=dict)


class TaskContext(BaseModel):
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    paei: Optional[PAEIRole] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    estimated_minutes: Optional[int] = None
    map_id: Optional[str] = None
    quest_id: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class XPEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    amount: float
    paei: Optional[PAEIRole] = None
    reason: Optional[str] = None
    task_id: Optional[str] = None
    map_id: Optional[str] = None
    quest_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QuestContext(BaseModel):
    id: str
    name: str
    result: str  # RPM Result
    purpose: str  # RPM Purpose
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    extra: Dict[str, Any] = Field(default_factory=dict)


class MapContext(BaseModel):
    id: str
    name: str
    quest_id: str
    description: Optional[str] = None
    status: str = "active"
    tasks_completed: int = 0
    tasks_total: int = 0
    extra: Dict[str, Any] = Field(default_factory=dict)


class CalendarContext(BaseModel):
    today_events: List[Dict[str, Any]] = Field(default_factory=list)
    free_blocks_minutes: int = 0
    deep_work_blocks: List[Dict[str, Any]] = Field(default_factory=list)
    next_meeting: Optional[Dict[str, Any]] = None


class PAEIDecisionContext(BaseModel):
    role: PAEIRole
    email_style: str
    task_approach: str
    reasoning: str
    xp_amount: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------
# MAIN STATE
# ---------------------------------------------------------

class PresentOSState(BaseModel):
    # Session
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = "default_user"
    received_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Input
    input_text: str = ""
    input_channel: str = "web"
    raw_input: Optional[Dict[str, Any]] = None
    
    # Intent
    intent: Optional[Any] = None
    
    # RPM Context (PDF Page 5-6)
    quests: Dict[str, QuestContext] = Field(default_factory=dict)
    maps: Dict[str, MapContext] = Field(default_factory=dict)
    tasks: Dict[str, TaskContext] = Field(default_factory=dict)
    
    # XP System (PDF Requirement)
    xp_events: List[XPEvent] = Field(default_factory=list)
    xp_totals_by_paei: Dict[PAEIRole, float] = Field(
        default_factory=lambda: {role: 0.0 for role in PAEIRole}
    )
    
    # External Context
    energy_level: float = 0.5
    energy_capacity: EnergyLevel = EnergyLevel.MEDIUM
    whoop_recovery_score: Optional[float] = None
    weather_snapshot: Dict[str, Any] = Field(default_factory=dict)
    
    # Calendar
    calendar: CalendarContext = Field(default_factory=CalendarContext)
    timezone: str = "Asia/Kolkata"
    
    # Conversation
    conversation: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Agent Coordination
    parent_decision: Optional[Dict[str, Any]] = None
    activated_agents: List[str] = Field(default_factory=list)
    agent_outputs: List[AgentOutput] = Field(default_factory=list)
    
    # PAEI Context (NEW - Critical)
    current_paei_context: Optional[PAEIDecisionContext] = None
    recent_paei_decisions: List[PAEIRole] = Field(default_factory=list)
    
    # Output
    final_response: Optional[str] = None
    response_payload: Dict[str, Any] = Field(default_factory=dict)
    planned_actions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    meta: Dict[str, Any] = Field(default_factory=dict)
    
    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------
    
    def add_agent_output(
        self, 
        agent: str, 
        result: Dict[str, Any], 
        paei_role: Optional[PAEIRole] = None,
        score: float = 0.0
    ):
        self.agent_outputs.append(
            AgentOutput(
                agent_name=agent, 
                result=result, 
                paei_role=paei_role,
                score=score
            )
        )
    
    def add_xp_event(
        self,
        amount: float,
        paei: Optional[PAEIRole] = None,
        reason: Optional[str] = None,
        task_id: Optional[str] = None
    ):
        event = XPEvent(
            amount=amount,
            paei=paei,
            reason=reason,
            task_id=task_id
        )
        self.xp_events.append(event)
        
        if paei:
            self.xp_totals_by_paei[paei] = self.xp_totals_by_paei.get(paei, 0.0) + amount
    
    def set_paei_context(self, context: PAEIDecisionContext):
        self.current_paei_context = context
        self.recent_paei_decisions.append(context.role)
        # Keep only last 50 decisions
        if len(self.recent_paei_decisions) > 50:
            self.recent_paei_decisions = self.recent_paei_decisions[-50:]
    
    def get_paei_distribution(self) -> Dict[PAEIRole, float]:
        """Get recent PAEI distribution"""
        if not self.recent_paei_decisions:
            return {role: 0.25 for role in PAEIRole}
        
        total = len(self.recent_paei_decisions)
        distribution = {}
        for role in PAEIRole:
            count = sum(1 for r in self.recent_paei_decisions if r == role)
            distribution[role] = count / total
        
        return distribution
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            PAEIRole: lambda v: v.value
        }
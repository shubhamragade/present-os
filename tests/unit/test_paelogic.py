# tests/unit/test_paelogic.py

import pytest
from app.services.paei_engine import PAEIDecisionEngine, PAEIRole, get_paei_decision

@pytest.fixture
def engine():
    return PAEIDecisionEngine()

# -------------------------------------------------
# INTENT ANALYSIS TESTS
# -------------------------------------------------

def test_analyze_intent_producer(engine):
    signals = {
        "urgency": True, 
        "execution_focus": True
    }
    role = engine._analyze_intent(signals)
    assert role == PAEIRole.PRODUCER

def test_analyze_intent_administrator(engine):
    signals = {
        "administrative": True,
        "documentation": True
    }
    role = engine._analyze_intent(signals)
    assert role == PAEIRole.ADMINISTRATOR

def test_analyze_intent_entrepreneur(engine):
    signals = {
        "strategic": True,
        "creative": True
    }
    role = engine._analyze_intent(signals)
    assert role == PAEIRole.ENTREPRENEUR

def test_analyze_intent_integrator(engine):
    signals = {
        "involves_people": True,
        "emotional_tone": True
    }
    role = engine._analyze_intent(signals)
    assert role == PAEIRole.INTEGRATOR

# -------------------------------------------------
# CONTEXT ADJUSTMENT TESTS
# -------------------------------------------------

def test_context_adjustment_low_energy(engine):
    # Producer task but low recovery -> Should switch to Integrator (self-care/delegation)
    base_role = PAEIRole.PRODUCER
    context = {"whoop_recovery": 30}
    
    final_role = engine._apply_context_adjustments(base_role, context)
    assert final_role == PAEIRole.INTEGRATOR

def test_context_adjustment_critical_deadline(engine):
    # Any role -> Producer if critical deadline
    base_role = PAEIRole.ADMINISTRATOR
    context = {"deadline_pressure": "critical"}
    
    final_role = engine._apply_context_adjustments(base_role, context)
    assert final_role == PAEIRole.PRODUCER

def test_context_adjustment_fragile_morale(engine):
    # Any role -> Integrator if team morale is fragile
    base_role = PAEIRole.PRODUCER
    context = {"team_morale": "fragile"}
    
    final_role = engine._apply_context_adjustments(base_role, context)
    assert final_role == PAEIRole.INTEGRATOR

# -------------------------------------------------
# XP CALCULATION TESTS
# -------------------------------------------------

def test_xp_calculation_basics(engine):
    signals = {}
    context = {}
    
    # Base XP checks
    assert engine._calculate_xp(PAEIRole.PRODUCER, signals, context) == 5
    assert engine._calculate_xp(PAEIRole.ADMINISTRATOR, signals, context) == 8
    assert engine._calculate_xp(PAEIRole.ENTREPRENEUR, signals, context) == 10
    assert engine._calculate_xp(PAEIRole.INTEGRATOR, signals, context) == 7

def test_xp_calculation_bonuses(engine):
    # Low recovery bonus for Integrator
    assert engine._calculate_xp(
        PAEIRole.INTEGRATOR, 
        {}, 
        {"whoop_recovery": 30}
    ) == 10  # 7 + 3
    
    # Deadline pressure bonus for Producer
    assert engine._calculate_xp(
        PAEIRole.PRODUCER, 
        {}, 
        {"deadline_pressure": "critical"}
    ) == 10 # 5 + 5
    
    # Urgency bonus for Producer
    assert engine._calculate_xp(
        PAEIRole.PRODUCER, 
        {"urgency": True}, 
        {}
    ) == 7 # 5 + 2

# -------------------------------------------------
# FULL FLOW TEST
# -------------------------------------------------

def test_get_paei_decision_api():
    intent_signals = {"urgency": True}
    context = {
        "whoop_recovery": 80,
        "deadline_pressure": "normal"
    }
    
    decision = get_paei_decision(intent_signals, context)
    
    assert decision.role == PAEIRole.PRODUCER
    assert decision.priority_level == "high"
    assert decision.xp_amount >= 5
    assert decision.calendar_buffer == "5min"

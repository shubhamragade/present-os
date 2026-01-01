"""
Golden End-to-End Tests for PresentOS

COVERS:
- Intent → Parent → Execution → Response
- Multi-agent coordination
- Read-only vs write agents
- XP triggering rules
- Research → Browser dependency
- Weather advisory
- PDF-compliant behavior

RUN:
pytest tests/test_golden_e2e_presentos.py -v
"""

import pytest
from dotenv import load_dotenv

load_dotenv()

from app.graph.build_graph import build_presentos_graph
from app.graph.state import PresentOSState


# -------------------------------------------------
# Helper
# -------------------------------------------------
def run_e2e(graph, text: str) -> PresentOSState:
    state = PresentOSState(
        input_text=text,
        timezone="Asia/Kolkata",
    )
    return graph.invoke(state)


# -------------------------------------------------
# Fixture
# -------------------------------------------------
@pytest.fixture(scope="module")
def graph():
    return build_presentos_graph()


# -------------------------------------------------
# 1️⃣ CHAT / NO ACTION
# -------------------------------------------------
def test_chat_no_action(graph):
    state = run_e2e(graph, "hello")

    assert state.activated_agents == []
    assert state.agent_outputs == []
    assert state.response_payload["status"] in {"no_action", "awaiting_user"}


# -------------------------------------------------
# 2️⃣ PLAN REPORT (READ-ONLY)
# -------------------------------------------------
def test_plan_report(graph):
    state = run_e2e(graph, "show my plan for today")

    agents = {o.agent_name for o in state.agent_outputs}

    assert "plan_report_agent" in agents
    assert "xp_agent" not in agents


# -------------------------------------------------
# 3️⃣ TASK CREATION + XP
# -------------------------------------------------
def test_task_creation(graph):
    state = run_e2e(graph, "remind me to submit the assignment tomorrow")

    agents = {o.agent_name for o in state.agent_outputs}

    assert "task_agent" in agents
    assert "xp_agent" in agents

    task = next(o for o in state.agent_outputs if o.agent_name == "task_agent")
    assert task.result["action"] == "task_created"


# -------------------------------------------------
# 4️⃣ CALENDAR MEETING
# -------------------------------------------------
def test_calendar_meeting(graph):
    state = run_e2e(graph, "schedule a meeting with Rahul tomorrow at 4 PM")

    agents = {o.agent_name for o in state.agent_outputs}
    assert "calendar_agent" in agents

    cal = next(o for o in state.agent_outputs if o.agent_name == "calendar_agent")
    assert cal.result["action"] == "created_event"


# -------------------------------------------------
# 5️⃣ MULTI-INTENT COORDINATION
# -------------------------------------------------
def test_multi_intent_coordination(graph):
    state = run_e2e(
        graph,
        "Schedule a meeting with Rahul tomorrow at 4 PM, "
        "send him an email invite, and remind me 30 minutes before"
    )

    agents = {o.agent_name for o in state.agent_outputs}

    assert "calendar_agent" in agents
    assert "email_sender_agent" in agents
    assert "task_agent" in agents
    assert "xp_agent" in agents


# -------------------------------------------------
# 6️⃣ RESEARCH → BROWSER DEPENDENCY
# -------------------------------------------------
def test_research_pipeline(graph):
    state = run_e2e(
        graph,
        "compare Pinecone vs Weaviate for long term AI memory"
    )

    agents = {o.agent_name for o in state.agent_outputs}

    assert "browser_agent" in agents
    assert "research_agent" in agents
    assert "xp_agent" not in agents


# -------------------------------------------------
# 7️⃣ WEATHER (READ-ONLY)
# -------------------------------------------------
def test_weather_agent(graph):
    state = run_e2e(
        graph,
        "what's the weather like tomorrow in Pune"
    )

    agents = {o.agent_name for o in state.agent_outputs}

    assert "weather_agent" in agents
    assert "xp_agent" not in agents

    weather = next(o for o in state.agent_outputs if o.agent_name == "weather_agent")
    assert weather.result["action"] in {
        "weather_advisory",
        "weather_info",
        "forecast",
    }


# -------------------------------------------------
# 8️⃣ FOCUS MODE
# -------------------------------------------------
def test_focus_mode(graph):
    state = run_e2e(
        graph,
        "start focus mode for 2 hours"
    )

    agents = {o.agent_name for o in state.agent_outputs}
    assert "focus_agent" in agents
    assert "xp_agent" in agents


# -------------------------------------------------
# 9️⃣ QUEST CREATION (BLOCKED)
# -------------------------------------------------
def test_quest_creation_blocked(graph):
    state = run_e2e(
        graph,
        "create a new quest to build PresentOS MVP"
    )

    agents = {o.agent_name for o in state.agent_outputs}
    assert "quest_agent" in agents

    quest = next(o for o in state.agent_outputs if o.agent_name == "quest_agent")
    assert quest.result["status"] == "blocked"


# -------------------------------------------------
# 🔟 XP NEVER FOR READ-ONLY
# -------------------------------------------------
def test_no_xp_for_read_only(graph):
    state = run_e2e(
        graph,
        "what's the weather in Pune"
    )

    agents = {o.agent_name for o in state.agent_outputs}
    assert "xp_agent" not in agents


import pytest
from app.graph.state import PresentOSState, AgentOutput
from app.graph.parent_response_node import run_parent_response_node
from unittest.mock import patch, MagicMock

def test_run_parent_response_node_plan_report():
    state = PresentOSState()
    # Mock output from plan_report_agent
    state.add_agent_output(
        agent="plan_report_agent",
        result={
            "action": "daily_plan",
            "date": "2026-01-26",
            "tasks": [
                {"title": "Task A"},
                {"title": "Task B"},
                {"title": "Task C"},
                {"title": "Task D"}
            ]
        }
    )
    
    with patch('app.graph.parent_response_node._llm_complete') as mock_llm:
        mock_llm.return_value = "Here is your plan: Task A, Task B, Task C..."
        
        result_state = run_parent_response_node(state)
        
        # Verify LLM was called with the plan info
        args, _ = mock_llm.call_args
        prompt = args[0]
        assert "📅 Daily plan loaded: 4 tasks found" in prompt
        assert "Task A, Task B, Task C..." in prompt
        assert result_state.final_response == "Here is your plan: Task A, Task B, Task C..."

def test_run_parent_response_node_weather_report():
    state = PresentOSState()
    # Mock output from weather_agent (read-only)
    state.add_agent_output(
        agent="weather_agent",
        result={
            "status": "read_only_forecast",
            "forecast": {
                "condition": "Cloudy",
                "description": "Scattered clouds"
            }
        }
    )
    
    with patch('app.graph.parent_response_node._llm_complete') as mock_llm:
        mock_llm.return_value = "The weather is Cloudy."
        
        result_state = run_parent_response_node(state)
        
        args, _ = mock_llm.call_args
        prompt = args[0]
        assert "🌤️ Weather: Cloudy" in prompt
        assert result_state.final_response == "The weather is Cloudy."

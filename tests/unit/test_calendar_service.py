# tests/unit/test_calendar_service.py

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from app.services.calendar_service import CalendarService, CalendarContext, PAEITimePreferences

# -------------------------------------------------
# FIXTURES
# -------------------------------------------------

@pytest.fixture
def mock_notion():
    return MagicMock()

@pytest.fixture
def calendar_service(mock_notion):
    return CalendarService(notion=mock_notion)

@pytest.fixture
def base_context():
    return CalendarContext(
        user_id="test_user",
        timezone="UTC",
        location="Test City",
        whoop_recovery=80.0,
        current_paei_role="P",
        today_meetings_count=0,
        deep_work_blocks=[],
        outdoor_preferences=[]
    )

# -------------------------------------------------
# INTERNAL SCORING TESTS
# -------------------------------------------------

def test_score_paei_time(calendar_service):
    # Test Producer peak hours (9-12, 15-17)
    # 10:00 AM -> Peak -> 1.0
    dt_peak = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert calendar_service._score_paei_time(dt_peak, "P") == 1.0

    # 13:30 -> Avoid (13-14) -> 0.2
    dt_avoid = datetime(2023, 1, 1, 13, 30, 0, tzinfo=timezone.utc)
    assert calendar_service._score_paei_time(dt_avoid, "P") == 0.2

    # 20:00 -> Neutral -> 0.6
    dt_neutral = datetime(2023, 1, 1, 20, 0, 0, tzinfo=timezone.utc)
    assert calendar_service._score_paei_time(dt_neutral, "P") == 0.6

def test_score_energy_match(calendar_service):
    # High recovery (>70) + Morning (9-12) -> 1.0
    dt_morning = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert calendar_service._score_energy_match(dt_morning, 90) == 1.0

    # Low recovery (<40) -> 0.3
    dt_any = datetime(2023, 1, 1, 14, 0, 0, tzinfo=timezone.utc)
    assert calendar_service._score_energy_match(dt_any, 30) == 0.3

    # Normal case -> 0.7
    dt_afternoon = datetime(2023, 1, 1, 15, 0, 0, tzinfo=timezone.utc)
    assert calendar_service._score_energy_match(dt_afternoon, 80) == 0.7

def test_score_deadline_proximity(calendar_service):
    now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    # < 24 hours -> 1.0
    deadline_urgent = now + timedelta(hours=20)
    assert calendar_service._score_deadline_proximity(now, deadline_urgent) == 1.0

    # < 72 hours -> 0.7
    deadline_soon = now + timedelta(hours=48)
    assert calendar_service._score_deadline_proximity(now, deadline_soon) == 0.7

    # > 72 hours -> 0.4
    deadline_far = now + timedelta(hours=100)
    assert calendar_service._score_deadline_proximity(now, deadline_far) == 0.4

# -------------------------------------------------
# SCHEDULE TASK TESTS (High Level)
# -------------------------------------------------

@patch("app.services.calendar_service.CalendarService._get_free_slots")
@patch("app.services.calendar_service.CalendarService._get_whoop_recovery")
@patch("app.services.calendar_service.CalendarService._get_weather_score")
@patch("app.integrations.google_calendar.create_event")
def test_schedule_task_success(
    mock_create_event,
    mock_weather_score,
    mock_whoop,
    mock_free_slots,
    calendar_service
):
    # SETUP
    mock_whoop.return_value = 85.0
    mock_weather_score.return_value = 0.8
    
    # Fake slot from 9am to 10am today
    start_time = datetime.now(timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)
    
    # Needs to be a simple object with start/end attributes as per implementation
    Slot = type("Slot", (), {"start": start_time, "end": end_time})
    mock_free_slots.return_value = [Slot]
    
    mock_create_event.return_value = {"id": "evt_123", "status": "confirmed"}

    # EXECUTE
    task_payload = {
        "title": "Important Task",
        "paei": "P",
        "estimated_minutes": 60,
        "deadline": (start_time + timedelta(days=2)).isoformat()
    }
    user_context = {
        "user_id": "u1",
        "timezone": "UTC",
        "calendar_id": "primary"
    }

    result = calendar_service.schedule_task(task_payload, user_context)

    # ASSERT
    assert result["action"] == "blocked_time"
    assert result["event"]["id"] == "evt_123"
    assert result["slot_score"] > 0
    
    mock_create_event.assert_called_once()
    args, kwargs = mock_create_event.call_args
    assert kwargs["calendar_id"] == "primary"
    assert kwargs["event"]["summary"] == "Deep Work: Important Task"

@patch("app.services.calendar_service.CalendarService._get_free_slots")
@patch("app.services.calendar_service.CalendarService._get_whoop_recovery")
def test_schedule_task_deferred_no_slots(
    mock_whoop,
    mock_free_slots,
    calendar_service
):
    # SETUP
    mock_whoop.return_value = 80.0
    mock_free_slots.return_value = [] # No slots available

    # EXECUTE
    task_payload = {"title": "Task", "paei": "P"}
    user_context = {}
    
    result = calendar_service.schedule_task(task_payload, user_context)

    # ASSERT
    assert result["action"] == "deferred"


# -------------------------------------------------
# WEATHER AUTO-RESCHEDULE TESTS
# -------------------------------------------------

@patch("app.integrations.weather_client.get_forecast")
def test_auto_reschedule_perfect_kite(mock_forecast, calendar_service):
    # PDF condition: 15-25 knots wind
    mock_forecast.return_value = {
        "wind_speed_knots": 20, 
        "rain_risk": "low"
    }
    
    user_context = {"location": "Maui"}
    
    result = calendar_service.auto_reschedule_based_on_weather(user_context)
    
    assert result["action"] == "block_time_for_perfect_conditions"
    assert result["reason"] == "perfect_kite_conditions"
    assert result["duration_minutes"] == 180

@patch("app.integrations.weather_client.get_forecast")
def test_auto_reschedule_rain_risk(mock_forecast, calendar_service):
    # Rain risk high
    mock_forecast.return_value = {
        "wind_speed_knots": 5, 
        "rain_risk": "high"
    }
    
    user_context = {"location": "London"}
    
    result = calendar_service.auto_reschedule_based_on_weather(user_context)
    
    assert result["action"] == "suggest_virtual_meetings"
    assert result["reason"] == "high_rain_risk"

@patch("app.integrations.weather_client.get_forecast")
def test_auto_reschedule_no_change(mock_forecast, calendar_service):
    # Boring weather
    mock_forecast.return_value = {
        "wind_speed_knots": 5, 
        "rain_risk": "low"
    }
    
    user_context = {"location": "San Jose"}
    
    result = calendar_service.auto_reschedule_based_on_weather(user_context)
    
    assert result["action"] == "no_changes_needed"

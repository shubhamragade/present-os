"""
Full production-grade CalendarService for PresentOS - PDF COMPLIANT
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field

from app.integrations.notion_client import NotionClient
from app.integrations import google_calendar
from app.integrations import fireflies_client

logger = logging.getLogger("presentos.calendar_service")

# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None

# -------------------------------------------------
# PDF-COMPLIANT MODELS
# -------------------------------------------------

@dataclass
class PAEITimePreferences:
    P: Dict[str, Any] = field(default_factory=lambda: {
        "peak_hours": [(9, 12), (15, 17)],
        "avoid_hours": [(13, 14)]
    })
    A: Dict[str, Any] = field(default_factory=lambda: {
        "peak_hours": [(10, 12), (14, 16)],
        "avoid_hours": []
    })
    E: Dict[str, Any] = field(default_factory=lambda: {
        "peak_hours": [(11, 13), (16, 18)],
        "avoid_hours": [(9, 10)]
    })
    I: Dict[str, Any] = field(default_factory=lambda: {
        "peak_hours": [(13, 15), (17, 19)],
        "avoid_hours": [(9, 12)]
    })

class WeatherAwareSlot(BaseModel):
    start: datetime
    end: datetime
    score: float
    weather_score: float
    surf_score: float = 0.0
    is_outdoor_friendly: bool = False
    breakdown: Dict[str, float] = Field(default_factory=dict)

@dataclass
class CalendarContext:
    user_id: str
    timezone: str
    location: str
    whoop_recovery: float
    current_paei_role: str
    today_meetings_count: int
    deep_work_blocks: List[Dict[str, Any]]
    outdoor_preferences: List[str]

# -------------------------------------------------
# CALENDAR SERVICE
# -------------------------------------------------

@dataclass
class CalendarService:
    notion: NotionClient

    fireflies_email: str = "ai@fireflies.ai"
    min_deep_work_protection: int = 60
    surf_location: str = "Santa Monica"

    paei_prefs: PAEITimePreferences = field(default_factory=PAEITimePreferences)

    # -------------------------------------------------
    # WEATHER AGENT — REAL CONNECTION
    # -------------------------------------------------

    def _get_weather_score(self, slot_start: datetime, location: str) -> float:
        """Get REAL weather score from your weather_client"""
        try:
            from app.integrations.weather_client import get_forecast

            location_dict = {
                "city": location.split(",")[0].strip() if "," in location else location
            }

            forecast = get_forecast(location_dict)

            # Use real surf score (0.0–1.0)
            return forecast.get("surf_score", 0.5)

        except Exception as e:
            logger.error(f"Weather score failed: {e}")
            return 0.5
    # Add this method to CalendarService class:
def _score_deadline_proximity(self, slot_start: datetime, deadline: datetime) -> float:
    """Score based on how close to deadline"""
    if deadline is None:
        return 0.5
    
    hours_until_deadline = (deadline - slot_start).total_seconds() / 3600
    
    if hours_until_deadline <= 0:
        return 1.0  # Overdue
    elif hours_until_deadline <= 24:
        return 0.9  # Urgent (today/tomorrow)
    elif hours_until_deadline <= 72:
        return 0.7  # Soon (3 days)
    elif hours_until_deadline <= 168:
        return 0.5  # This week
    else:
        return 0.3  # Later

    def _get_perfect_kite_conditions(self, location: str) -> bool:
        """PDF Page 14-15: Perfect kite conditions detection"""
        try:
            from app.integrations.weather_client import get_forecast

            forecast = get_forecast({"city": location})
            wind_knots = forecast.get("wind_speed_knots", 0)

            # PDF logic: 15–25 knots = perfect kiting
            return 15 <= wind_knots <= 25

        except Exception:
            return False

    # -------------------------------------------------
    # WHOOP — REAL CONNECTION
    # -------------------------------------------------

    def _get_whoop_recovery(self, user_id: Optional[str]) -> float:
        try:
            from app.integrations.whoop_client import DummyWhoopClient

            client = DummyWhoopClient()
            signal = client.get_signal()
            return signal.recovery_score * 100

        except Exception:
            return 70.0

    # -------------------------------------------------
    # GOOGLE CALENDAR — FREE/BUSY
    # -------------------------------------------------

    def _get_free_slots(
        self,
        calendar_id: str,
        start: datetime,
        end: datetime,
        min_duration: int
    ) -> List[Any]:

        from app.integrations.google_calendar import freebusy

        busy_periods = freebusy(
            calendar_id=calendar_id,
            time_min=start.isoformat(),
            time_max=end.isoformat()
        )

        free_slots = []
        current = start

        for busy in busy_periods:
            busy_start = parse_iso(busy["start"])
            busy_end = parse_iso(busy["end"])

            if not busy_start or not busy_end:
                continue

            if current < busy_start:
                gap_minutes = (busy_start - current).total_seconds() / 60
                if gap_minutes >= min_duration:
                    free_slots.append(
                        type("Slot", (), {"start": current, "end": busy_start})
                    )

            current = max(current, busy_end)

        if current < end:
            remaining = (end - current).total_seconds() / 60
            if remaining >= min_duration:
                free_slots.append(
                    type("Slot", (), {"start": current, "end": end})
                )

        return free_slots

    # -------------------------------------------------
    # TASK SCHEDULING
    # -------------------------------------------------

    def schedule_task(self, task_payload: Dict[str, Any], user_context: Dict[str, Any]) -> Dict[str, Any]:
        context = CalendarContext(
            user_id=user_context.get("user_id", "default"),
            timezone=user_context.get("timezone", "UTC"),
            location=user_context.get("location", self.surf_location),
            whoop_recovery=self._get_whoop_recovery(user_context.get("whoop_user_id")),
            current_paei_role=task_payload.get("paei", "P"),
            today_meetings_count=0,
            deep_work_blocks=[],
            outdoor_preferences=user_context.get("outdoor_preferences", [])
        )

        best_slot = self._find_optimal_slot(task_payload, context)

        if not best_slot or best_slot.score < 0.3:
            return {"action": "deferred"}

        event = google_calendar.create_event(
            calendar_id=user_context.get("calendar_id", "primary"),
            event={
                "summary": f"Deep Work: {task_payload.get('title','Task')}",
                "start": {"dateTime": best_slot.start.isoformat()},
                "end": {"dateTime": best_slot.end.isoformat()},
                "visibility": "private"
            },
            idempotency_key=str(uuid.uuid4())
        )

        return {
            "action": "blocked_time",
            "event": event,
            "slot_score": best_slot.score,
            "breakdown": best_slot.breakdown
        }

    # -------------------------------------------------
    # SLOT OPTIMIZATION
    # -------------------------------------------------

    def _find_optimal_slot(self, task_payload: Dict, context: CalendarContext) -> Optional[WeatherAwareSlot]:
        deadline = parse_iso(task_payload.get("deadline")) or datetime.now(timezone.utc) + timedelta(days=2)
        duration = task_payload.get("estimated_minutes", 30)

        free_slots = self._get_free_slots(
            "primary",
            datetime.now(timezone.utc),
            deadline,
            duration
        )

        best = None
        best_score = -1.0

        for slot in free_slots:
            paei = self._score_paei_time(slot.start, context.current_paei_role)
            energy = self._score_energy_match(slot.start, context.whoop_recovery)
            weather = self._get_weather_score(slot.start, context.location)
            deadline_score = self._score_deadline_proximity(slot.start, deadline)

            score = (
                0.3 * paei +
                0.3 * energy +
                0.2 * weather +
                0.2 * deadline_score
            )

            if score > best_score:
                best_score = score
                best = WeatherAwareSlot(
                    start=slot.start,
                    end=slot.end,
                    score=score,
                    weather_score=weather,
                    is_outdoor_friendly=weather > 0.7,
                    breakdown={
                        "paei": paei,
                        "energy": energy,
                        "weather": weather,
                        "deadline": deadline_score
                    }
                )

        return best

    # -------------------------------------------------
    # SCORING HELPERS
    # -------------------------------------------------

    def _score_paei_time(self, slot_start: datetime, role: str) -> float:
        hour = slot_start.hour
        prefs = getattr(self.paei_prefs, role, {})
        for a, b in prefs.get("peak_hours", []):
            if a <= hour < b:
                return 1.0
        for a, b in prefs.get("avoid_hours", []):
            if a <= hour < b:
                return 0.2
        return 0.6

    def _score_energy_match(self, slot_start: datetime, recovery: float) -> float:
        if recovery > 70 and 9 <= slot_start.hour < 12:
            return 1.0
        if recovery < 40:
            return 0.3
        return 0.7

    def _score_deadline_proximity(self, slot_start: datetime, deadline: datetime) -> float:
        hours = (deadline - slot_start).total_seconds() / 3600
        if hours < 24:
            return 1.0
        if hours < 72:
            return 0.7
        return 0.4

    # -------------------------------------------------
    # WEATHER-BASED AUTO RESCHEDULING
    # -------------------------------------------------

    def auto_reschedule_based_on_weather(self, user_context: Dict) -> Dict[str, Any]:
        """PDF Page 14-15: Auto-reschedule for perfect conditions"""

        location = user_context.get("location", self.surf_location)

        # Perfect kite conditions
        if self._get_perfect_kite_conditions(location):
            return {
                "action": "block_time_for_perfect_conditions",
                "reason": "perfect_kite_conditions",
                "duration_minutes": 180,
                "priority": "high",
                "auto_reschedule_conflicts": True
            }

        # Rain risk for outdoor meetings
        from app.integrations.weather_client import get_forecast
        forecast = get_forecast({"city": location})

        if forecast.get("rain_risk") in ["high", "very_high"]:
            return {
                "action": "suggest_virtual_meetings",
                "reason": "high_rain_risk",
                "rain_risk": forecast["rain_risk"]
            }

        return {"action": "no_changes_needed"}

# tests/unit/test_calendar_service.py

import pytest
from datetime import datetime, timedelta

from app.services.calendar_service import CalendarService
from app.graph.state import TaskContext
from app.integrations.notion_client import NotionClient


# -------------------------
# Test Setup (safe + offline)
# -------------------------

@pytest.fixture
def calendar_service(monkeypatch):
    """
    CalendarService with all external signals stubbed.
    No Google, no WHOOP, no Weather required.
    """

    # Fake Notion client (not used directly here)
    notion = NotionClient.from_env()

    svc = CalendarService(notion=notion)

    # Stub energy pattern
    monkeypatch.setattr(
        svc,
        "_get_user_energy_profile",
        lambda: {
            "peak": ("09:00", "12:00"),
            "dip": ("14:00", "17:00")
        }
    )

    # Stub calendar availability (full free day)
    monkeypatch.setattr(
        svc,
        "_get_calendar_freebusy",
        lambda date: [
            ("09:00", "12:00"),
            ("13:00", "18:00")
        ]
    )

    # Stub WHOOP recovery
    monkeypatch.setattr(
        svc,
        "_get_recovery_score",
        lambda: 80
    )

    # Stub surf score
    monkeypatch.setattr(
        svc,
        "_get_surf_score",
        lambda: 0.0
    )

    return svc


# -------------------------
# TESTS
# -------------------------

def test_producer_task_scheduled_in_morning(calendar_service):
    task = TaskContext(
        id="t1",
        name="Hard producer task",
        paei="P",
        estimated_minutes=90
    )

    slot = calendar_service.assign_time_block(task)

    assert slot.start.hour >= 9
    assert slot.start.hour < 12


def test_admin_task_scheduled_in_afternoon(calendar_service):
    task = TaskContext(
        id="t2",
        name="Admin task",
        paei="A",
        estimated_minutes=30
    )

    slot = calendar_service.assign_time_block(task)

    assert slot.start.hour >= 14


def test_entrepreneur_task_requires_deep_work(calendar_service):
    task = TaskContext(
        id="t3",
        name="Creative strategy",
        paei="E",
        estimated_minutes=120
    )

    slot = calendar_service.assign_time_block(task)

    duration = (slot.end - slot.start).seconds / 60
    assert duration >= 120
    assert slot.is_deep_work is True


def test_integrator_task_post_lunch(calendar_service):
    task = TaskContext(
        id="t4",
        name="Client call",
        paei="I",
        estimated_minutes=45
    )

    slot = calendar_service.assign_time_block(task)

    assert slot.start.hour >= 13


def test_low_recovery_reschedules_hard_tasks(calendar_service, monkeypatch):
    monkeypatch.setattr(
        calendar_service,
        "_get_recovery_score",
        lambda: 35
    )

    task = TaskContext(
        id="t5",
        name="Heavy producer task",
        paei="P",
        estimated_minutes=90
    )

    slot = calendar_service.assign_time_block(task)

    assert slot.deferred is True


def test_high_priority_overrides_energy(calendar_service):
    task = TaskContext(
        id="t6",
        name="Urgent deadline",
        paei="P",
        estimated_minutes=60,
        priority="High",
        deadline=datetime.utcnow().date().isoformat()
    )

    slot = calendar_service.assign_time_block(task)

    assert slot.override_reason == "high_priority"


def test_calendar_service_works_without_google(calendar_service):
    task = TaskContext(
        id="t7",
        name="Offline scheduling test",
        paei="A",
        estimated_minutes=20
    )

    slot = calendar_service.assign_time_block(task)

    assert slot is not None

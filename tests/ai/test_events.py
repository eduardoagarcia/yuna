"""Tests for AI events."""

import time

from yuna.ai.events import (
    BlackboardValueChanged,
    EntityLost,
    EntityPerceived,
    PathBlocked,
    PathCompleted,
)
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2


def test_blackboard_value_changed_event_creation() -> None:
    """Test creating BlackboardValueChanged event."""
    event = BlackboardValueChanged(
        timestamp=1.0,
        tick=10,
        entity_id=EntityID("agent-1"),
        key="target",
        old_value=None,
        new_value=EntityID("enemy-1"),
    )

    assert event.timestamp == 1.0
    assert event.tick == 10
    assert event.entity_id == EntityID("agent-1")
    assert event.key == "target"
    assert event.old_value is None
    assert event.new_value == EntityID("enemy-1")
    assert event.event_type == "BlackboardValueChanged"


def test_blackboard_value_changed_create_stamps_tick_and_timestamp() -> None:
    """create() stamps the given tick and an auto-generated timestamp."""
    before = time.time()
    event = BlackboardValueChanged.create(
        tick=10,
        entity_id=EntityID("agent-1"),
        key="target",
        old_value=None,
        new_value=EntityID("enemy-1"),
    )
    after = time.time()

    assert event.tick == 10
    assert before <= event.timestamp <= after
    assert event.entity_id == EntityID("agent-1")
    assert event.key == "target"
    assert event.old_value is None
    assert event.new_value == EntityID("enemy-1")


def test_entity_perceived_event_creation() -> None:
    """Test creating EntityPerceived event."""
    event = EntityPerceived(
        timestamp=2.0,
        tick=20,
        perceiver=EntityID("agent-1"),
        perceived=EntityID("player-1"),
        perception_type="vision",
        position=Vector2(x=10.0, y=20.0),
    )

    assert event.timestamp == 2.0
    assert event.tick == 20
    assert event.perceiver == EntityID("agent-1")
    assert event.perceived == EntityID("player-1")
    assert event.perception_type == "vision"
    assert event.position == Vector2(x=10.0, y=20.0)
    assert event.event_type == "EntityPerceived"


def test_entity_perceived_hearing_type() -> None:
    """Test EntityPerceived event with hearing type."""
    event = EntityPerceived(
        timestamp=2.0,
        tick=20,
        perceiver=EntityID("agent-1"),
        perceived=EntityID("player-1"),
        perception_type="hearing",
        position=Vector2(x=15.0, y=25.0),
    )

    assert event.perception_type == "hearing"


def test_entity_lost_event_creation() -> None:
    """Test creating EntityLost event."""
    event = EntityLost(
        timestamp=3.0,
        tick=30,
        perceiver=EntityID("agent-1"),
        lost=EntityID("player-1"),
        perception_type="vision",
        last_known_position=Vector2(x=30.0, y=40.0),
    )

    assert event.timestamp == 3.0
    assert event.tick == 30
    assert event.perceiver == EntityID("agent-1")
    assert event.lost == EntityID("player-1")
    assert event.perception_type == "vision"
    assert event.last_known_position == Vector2(x=30.0, y=40.0)
    assert event.event_type == "EntityLost"


def test_path_blocked_event_creation() -> None:
    """Test creating PathBlocked event."""
    event = PathBlocked(
        timestamp=4.0,
        tick=40,
        entity_id=EntityID("agent-1"),
        blocked_at=Vector2(x=50.0, y=60.0),
        goal=Vector2(x=100.0, y=100.0),
    )

    assert event.timestamp == 4.0
    assert event.tick == 40
    assert event.entity_id == EntityID("agent-1")
    assert event.blocked_at == Vector2(x=50.0, y=60.0)
    assert event.goal == Vector2(x=100.0, y=100.0)
    assert event.event_type == "PathBlocked"


def test_path_completed_event_creation() -> None:
    """Test creating PathCompleted event."""
    event = PathCompleted(
        timestamp=5.0,
        tick=50,
        entity_id=EntityID("agent-1"),
        final_position=Vector2(x=100.0, y=100.0),
    )

    assert event.timestamp == 5.0
    assert event.tick == 50
    assert event.entity_id == EntityID("agent-1")
    assert event.final_position == Vector2(x=100.0, y=100.0)
    assert event.event_type == "PathCompleted"

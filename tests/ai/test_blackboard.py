"""Tests for Blackboard pattern AI memory system."""

from unittest.mock import Mock

import pytest

from yuna.ai.blackboard import Blackboard, BlackboardKey
from yuna.ai.events import BlackboardValueChanged
from yuna.types.identifiers import EntityID


def test_blackboard_creation() -> None:
    """Test creating empty Blackboard."""
    blackboard = Blackboard()
    assert blackboard.data == {}
    assert blackboard.schema == {}
    assert blackboard.emit_events is True


def test_blackboard_key_registration() -> None:
    """Test registering key with schema."""
    blackboard = Blackboard()
    key = BlackboardKey(
        name="target",
        value_type=EntityID,
        description="Current combat target",
    )

    blackboard.register_key(key=key)

    assert "target" in blackboard.schema
    assert blackboard.schema["target"] == key


def test_blackboard_key_registration_with_default_value() -> None:
    """Test registering key with default value sets data."""
    blackboard = Blackboard()
    key = BlackboardKey(
        name="is_alert",
        value_type=bool,
        default_value=False,
    )

    blackboard.register_key(key=key)

    assert blackboard.get_value(key="is_alert") is False


def test_set_value_without_schema() -> None:
    """Test setting value without schema validation."""
    blackboard = Blackboard()

    blackboard.set_value(key="target", value=EntityID("enemy-123"))

    assert blackboard.get_value(key="target") == EntityID("enemy-123")


def test_set_value_with_correct_type() -> None:
    """Test setting value with correct type passes validation."""
    blackboard = Blackboard()
    key = BlackboardKey(name="count", value_type=int)
    blackboard.register_key(key=key)

    blackboard.set_value(key="count", value=42)

    assert blackboard.get_value(key="count") == 42


def test_set_value_with_incorrect_type_raises_type_error() -> None:
    """Test setting value with wrong type raises TypeError."""
    blackboard = Blackboard()
    key = BlackboardKey(name="count", value_type=int)
    blackboard.register_key(key=key)

    with pytest.raises(TypeError) as exc_info:
        blackboard.set_value(key="count", value="not an int")

    assert "expects int" in str(exc_info.value)
    assert "got str" in str(exc_info.value)


def test_set_value_emits_event() -> None:
    """Test setting value emits BlackboardValueChanged event."""
    blackboard = Blackboard()
    mock_bus = Mock()
    entity_id = EntityID("agent-1")

    blackboard.set_value(
        key="target",
        value=EntityID("enemy-1"),
        entity_id=entity_id,
        event_bus=mock_bus,
        tick=7,
    )

    mock_bus.emit.assert_called_once()
    event = mock_bus.emit.call_args.kwargs["event"]
    assert isinstance(event, BlackboardValueChanged)
    assert event.entity_id == entity_id
    assert event.key == "target"
    assert event.old_value is None
    assert event.new_value == EntityID("enemy-1")
    assert event.tick == 7
    assert event.timestamp > 0


def test_set_value_tracks_old_value() -> None:
    """Test setting value tracks old value in event."""
    blackboard = Blackboard()
    mock_bus = Mock()
    entity_id = EntityID("agent-1")

    blackboard.set_value(
        key="health",
        value=100,
        entity_id=entity_id,
        event_bus=mock_bus,
    )
    mock_bus.reset_mock()

    blackboard.set_value(
        key="health",
        value=75,
        entity_id=entity_id,
        event_bus=mock_bus,
    )

    event = mock_bus.emit.call_args.kwargs["event"]
    assert event.old_value == 100
    assert event.new_value == 75


def test_set_value_without_event_bus_does_not_emit() -> None:
    """Test setting value without event bus skips emission."""
    blackboard = Blackboard()

    blackboard.set_value(key="target", value=EntityID("enemy-1"))

    assert blackboard.get_value(key="target") == EntityID("enemy-1")


def test_set_value_with_emit_events_false() -> None:
    """Test setting value with emit_events=False skips emission."""
    blackboard = Blackboard(emit_events=False)
    mock_bus = Mock()

    blackboard.set_value(
        key="target",
        value=EntityID("enemy-1"),
        entity_id=EntityID("agent-1"),
        event_bus=mock_bus,
    )

    mock_bus.emit.assert_not_called()


def test_get_value_returns_stored_value() -> None:
    """Test getting value returns stored data."""
    blackboard = Blackboard()
    blackboard.set_value(key="score", value=1000)

    result = blackboard.get_value(key="score")

    assert result == 1000


def test_get_value_returns_default_for_missing_key() -> None:
    """Test getting missing key returns default."""
    blackboard = Blackboard()

    result = blackboard.get_value(key="missing", default="default_value")

    assert result == "default_value"


def test_get_value_returns_none_for_missing_key_without_default() -> None:
    """Test getting missing key without default returns None."""
    blackboard = Blackboard()

    result = blackboard.get_value(key="missing")

    assert result is None


def test_has_key_returns_true_for_existing_key() -> None:
    """Test has_key returns True for existing key."""
    blackboard = Blackboard()
    blackboard.set_value(key="target", value=EntityID("enemy-1"))

    assert blackboard.has_key(key="target") is True


def test_has_key_returns_false_for_missing_key() -> None:
    """Test has_key returns False for missing key."""
    blackboard = Blackboard()

    assert blackboard.has_key(key="target") is False


def test_clear_key_removes_key() -> None:
    """Test clear_key removes key from data."""
    blackboard = Blackboard()
    blackboard.set_value(key="target", value=EntityID("enemy-1"))

    blackboard.clear_key(key="target")

    assert blackboard.has_key(key="target") is False


def test_clear_key_on_missing_key_does_nothing() -> None:
    """Test clear_key on missing key does not raise error."""
    blackboard = Blackboard()

    blackboard.clear_key(key="missing")

    assert blackboard.has_key(key="missing") is False


def test_clear_all_removes_all_keys() -> None:
    """Test clear_all removes all data."""
    blackboard = Blackboard()
    blackboard.set_value(key="target", value=EntityID("enemy-1"))
    blackboard.set_value(key="score", value=1000)
    blackboard.set_value(key="is_alert", value=True)

    blackboard.clear_all()

    assert blackboard.data == {}
    assert blackboard.has_key(key="target") is False
    assert blackboard.has_key(key="score") is False
    assert blackboard.has_key(key="is_alert") is False


def test_blackboard_with_multiple_types() -> None:
    """Test blackboard handles multiple value types."""
    blackboard = Blackboard()

    blackboard.set_value(key="target", value=EntityID("enemy-1"))
    blackboard.set_value(key="score", value=1000)
    blackboard.set_value(key="is_alert", value=True)
    blackboard.set_value(key="position", value=(10.0, 20.0))

    assert blackboard.get_value(key="target") == EntityID("enemy-1")
    assert blackboard.get_value(key="score") == 1000
    assert blackboard.get_value(key="is_alert") is True
    assert blackboard.get_value(key="position") == (10.0, 20.0)

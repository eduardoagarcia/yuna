"""Tests for behavior tree types."""

from unittest.mock import Mock

from yuna.ai.behavior_tree.types import (
    BehaviorContext,
    NodeStatus,
)
from yuna.types.identifiers import EntityID


def test_node_status_enum_values() -> None:
    """Test NodeStatus enum has correct values."""
    assert NodeStatus.SUCCESS.value == "success"
    assert NodeStatus.FAILURE.value == "failure"
    assert NodeStatus.RUNNING.value == "running"


def test_node_status_enum_members() -> None:
    """Test NodeStatus enum has all expected members."""
    statuses = [status.name for status in NodeStatus]
    assert "SUCCESS" in statuses
    assert "FAILURE" in statuses
    assert "RUNNING" in statuses
    assert len(statuses) == 3


def test_behavior_context_creation() -> None:
    """Test creating BehaviorContext with required fields."""
    mock_world = Mock()
    mock_blackboard = Mock()
    entity_id = EntityID("agent-1")

    context = BehaviorContext(
        world=mock_world,
        entity_id=entity_id,
        blackboard=mock_blackboard,
        delta_time=0.016,
    )

    assert context.world == mock_world
    assert context.entity_id == entity_id
    assert context.blackboard == mock_blackboard
    assert context.delta_time == 0.016
    assert context.data is None


def test_behavior_context_with_custom_data() -> None:
    """Test BehaviorContext with custom data dict."""
    mock_world = Mock()
    mock_blackboard = Mock()
    custom_data = {"foo": "bar", "count": 42}

    context = BehaviorContext(
        world=mock_world,
        entity_id=EntityID("agent-1"),
        blackboard=mock_blackboard,
        delta_time=0.016,
        data=custom_data,
    )

    assert context.data == custom_data
    assert context.data["foo"] == "bar"
    assert context.data["count"] == 42

"""Tests for behavior tree node base class."""

from unittest.mock import Mock

from yuna.ai.behavior_tree.node import BehaviorNode
from yuna.ai.behavior_tree.types import (
    BehaviorContext,
    NodeStatus,
)


class TestActionNode(BehaviorNode):
    """Test node that returns configurable status."""

    def __init__(self, return_status: NodeStatus) -> None:
        """Initialize test node.

        Args:
            return_status: Status to return when ticked
        """
        self.return_status = return_status
        self.tick_count = 0

    def tick(self, context: BehaviorContext) -> NodeStatus:
        """Execute node and return configured status.

        Args:
            context: Execution context

        Returns:
            Configured status
        """
        self.tick_count += 1
        return self.return_status


def test_custom_node_implementation() -> None:
    """Test custom node can be implemented and executed."""
    node = TestActionNode(return_status=NodeStatus.SUCCESS)
    mock_context = Mock(spec=BehaviorContext)

    status = node.tick(context=mock_context)

    assert status == NodeStatus.SUCCESS
    assert node.tick_count == 1


def test_custom_node_returns_failure() -> None:
    """Test custom node can return failure."""
    node = TestActionNode(return_status=NodeStatus.FAILURE)
    mock_context = Mock(spec=BehaviorContext)

    status = node.tick(context=mock_context)

    assert status == NodeStatus.FAILURE


def test_custom_node_returns_running() -> None:
    """Test custom node can return running."""
    node = TestActionNode(return_status=NodeStatus.RUNNING)
    mock_context = Mock(spec=BehaviorContext)

    status = node.tick(context=mock_context)

    assert status == NodeStatus.RUNNING


def test_custom_node_multiple_ticks() -> None:
    """Test custom node can be ticked multiple times."""
    node = TestActionNode(return_status=NodeStatus.SUCCESS)
    mock_context = Mock(spec=BehaviorContext)

    node.tick(context=mock_context)
    node.tick(context=mock_context)
    status = node.tick(context=mock_context)

    assert status == NodeStatus.SUCCESS
    assert node.tick_count == 3

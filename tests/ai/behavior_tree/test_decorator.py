"""Tests for decorator behavior tree nodes."""

from unittest.mock import Mock

from yuna.ai.behavior_tree.decorator import (
    ConditionalNode,
    InverterNode,
    RepeatNode,
    UntilFailNode,
)
from yuna.ai.behavior_tree.node import BehaviorNode
from yuna.ai.behavior_tree.types import (
    BehaviorContext,
    NodeStatus,
)


class MockNode(BehaviorNode):
    """Mock node for testing."""

    def __init__(self, return_status: NodeStatus) -> None:
        """Initialize mock node.

        Args:
            return_status: Status to return
        """
        self.return_status = return_status
        self.tick_count = 0

    def tick(self, context: BehaviorContext) -> NodeStatus:
        """Execute and return configured status.

        Args:
            context: Execution context

        Returns:
            Configured status
        """
        self.tick_count += 1
        return self.return_status


def test_inverter_node_inverts_success() -> None:
    """Test InverterNode returns FAILURE when child succeeds."""
    child = MockNode(return_status=NodeStatus.SUCCESS)
    inverter = InverterNode(child=child)
    mock_context = Mock(spec=BehaviorContext)

    status = inverter.tick(context=mock_context)

    assert status == NodeStatus.FAILURE
    assert child.tick_count == 1


def test_inverter_node_inverts_failure() -> None:
    """Test InverterNode returns SUCCESS when child fails."""
    child = MockNode(return_status=NodeStatus.FAILURE)
    inverter = InverterNode(child=child)
    mock_context = Mock(spec=BehaviorContext)

    status = inverter.tick(context=mock_context)

    assert status == NodeStatus.SUCCESS
    assert child.tick_count == 1


def test_inverter_node_passes_running() -> None:
    """Test InverterNode returns RUNNING when child is running."""
    child = MockNode(return_status=NodeStatus.RUNNING)
    inverter = InverterNode(child=child)
    mock_context = Mock(spec=BehaviorContext)

    status = inverter.tick(context=mock_context)

    assert status == NodeStatus.RUNNING
    assert child.tick_count == 1


def test_inverter_node_with_no_child() -> None:
    """Test InverterNode returns FAILURE when child is None."""
    inverter = InverterNode(child=None)
    mock_context = Mock(spec=BehaviorContext)

    status = inverter.tick(context=mock_context)

    assert status == NodeStatus.FAILURE


def test_repeat_node_finite_repeats() -> None:
    """Test RepeatNode repeats child finite times."""
    child = MockNode(return_status=NodeStatus.SUCCESS)
    repeat = RepeatNode(child=child, max_repeats=3)
    mock_context = Mock(spec=BehaviorContext)

    status1 = repeat.tick(context=mock_context)
    assert status1 == NodeStatus.RUNNING
    assert child.tick_count == 1

    status2 = repeat.tick(context=mock_context)
    assert status2 == NodeStatus.RUNNING
    assert child.tick_count == 2

    status3 = repeat.tick(context=mock_context)
    assert status3 == NodeStatus.SUCCESS
    assert child.tick_count == 3


def test_repeat_node_infinite_repeats() -> None:
    """Test RepeatNode repeats infinitely when max_repeats is -1."""
    child = MockNode(return_status=NodeStatus.SUCCESS)
    repeat = RepeatNode(child=child, max_repeats=-1)
    mock_context = Mock(spec=BehaviorContext)

    status1 = repeat.tick(context=mock_context)
    status2 = repeat.tick(context=mock_context)
    status3 = repeat.tick(context=mock_context)

    assert status1 == NodeStatus.RUNNING
    assert status2 == NodeStatus.RUNNING
    assert status3 == NodeStatus.RUNNING
    assert child.tick_count == 3


def test_repeat_node_child_fails() -> None:
    """Test RepeatNode returns FAILURE when child fails."""
    child = MockNode(return_status=NodeStatus.FAILURE)
    repeat = RepeatNode(child=child, max_repeats=5)
    mock_context = Mock(spec=BehaviorContext)

    status = repeat.tick(context=mock_context)

    assert status == NodeStatus.FAILURE
    assert child.tick_count == 1


def test_repeat_node_child_running() -> None:
    """Test RepeatNode returns RUNNING when child is running."""
    child = MockNode(return_status=NodeStatus.RUNNING)
    repeat = RepeatNode(child=child, max_repeats=5)
    mock_context = Mock(spec=BehaviorContext)

    status = repeat.tick(context=mock_context)

    assert status == NodeStatus.RUNNING
    assert child.tick_count == 1


def test_repeat_node_with_no_child() -> None:
    """Test RepeatNode returns FAILURE when child is None."""
    repeat = RepeatNode(child=None, max_repeats=5)
    mock_context = Mock(spec=BehaviorContext)

    status = repeat.tick(context=mock_context)

    assert status == NodeStatus.FAILURE


def test_conditional_node_condition_true() -> None:
    """Test ConditionalNode executes child when condition is true."""
    child = MockNode(return_status=NodeStatus.SUCCESS)
    conditional = ConditionalNode(
        child=child,
        condition=lambda ctx: True,
    )
    mock_context = Mock(spec=BehaviorContext)

    status = conditional.tick(context=mock_context)

    assert status == NodeStatus.SUCCESS
    assert child.tick_count == 1


def test_conditional_node_condition_false() -> None:
    """Test ConditionalNode skips child when condition is false."""
    child = MockNode(return_status=NodeStatus.SUCCESS)
    conditional = ConditionalNode(
        child=child,
        condition=lambda ctx: False,
    )
    mock_context = Mock(spec=BehaviorContext)

    status = conditional.tick(context=mock_context)

    assert status == NodeStatus.FAILURE
    assert child.tick_count == 0


def test_conditional_node_uses_context() -> None:
    """Test ConditionalNode passes context to condition function."""
    child = MockNode(return_status=NodeStatus.SUCCESS)
    mock_blackboard = Mock()
    mock_blackboard.get_value.return_value = True
    mock_context = Mock(spec=BehaviorContext)
    mock_context.blackboard = mock_blackboard

    conditional = ConditionalNode(
        child=child,
        condition=lambda ctx: ctx.blackboard.get_value("has_target"),
    )

    status = conditional.tick(context=mock_context)

    assert status == NodeStatus.SUCCESS
    assert child.tick_count == 1


def test_conditional_node_with_no_child() -> None:
    """Test ConditionalNode returns FAILURE when child is None."""
    conditional = ConditionalNode(
        child=None,
        condition=lambda ctx: True,
    )
    mock_context = Mock(spec=BehaviorContext)

    status = conditional.tick(context=mock_context)

    assert status == NodeStatus.FAILURE


def test_conditional_node_with_no_condition() -> None:
    """Test ConditionalNode returns FAILURE when condition is None."""
    child = MockNode(return_status=NodeStatus.SUCCESS)
    conditional = ConditionalNode(child=child, condition=None)
    mock_context = Mock(spec=BehaviorContext)

    status = conditional.tick(context=mock_context)

    assert status == NodeStatus.FAILURE


def test_until_fail_node_child_succeeds() -> None:
    """Test UntilFailNode returns RUNNING when child succeeds."""
    child = MockNode(return_status=NodeStatus.SUCCESS)
    until_fail = UntilFailNode(child=child)
    mock_context = Mock(spec=BehaviorContext)

    status = until_fail.tick(context=mock_context)

    assert status == NodeStatus.RUNNING
    assert child.tick_count == 1


def test_until_fail_node_child_fails() -> None:
    """Test UntilFailNode returns SUCCESS when child fails."""
    child = MockNode(return_status=NodeStatus.FAILURE)
    until_fail = UntilFailNode(child=child)
    mock_context = Mock(spec=BehaviorContext)

    status = until_fail.tick(context=mock_context)

    assert status == NodeStatus.SUCCESS
    assert child.tick_count == 1


def test_until_fail_node_child_running() -> None:
    """Test UntilFailNode returns RUNNING when child is running."""
    child = MockNode(return_status=NodeStatus.RUNNING)
    until_fail = UntilFailNode(child=child)
    mock_context = Mock(spec=BehaviorContext)

    status = until_fail.tick(context=mock_context)

    assert status == NodeStatus.RUNNING
    assert child.tick_count == 1


def test_until_fail_node_with_no_child() -> None:
    """Test UntilFailNode returns SUCCESS when child is None."""
    until_fail = UntilFailNode(child=None)
    mock_context = Mock(spec=BehaviorContext)

    status = until_fail.tick(context=mock_context)

    assert status == NodeStatus.SUCCESS

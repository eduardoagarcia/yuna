"""Tests for composite behavior tree nodes."""

from unittest.mock import Mock

from yuna.ai.behavior_tree.composite import (
    ParallelNode,
    SelectorNode,
    SequenceNode,
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
        self.was_ticked = False

    def tick(self, context: BehaviorContext) -> NodeStatus:
        """Execute and return configured status.

        Args:
            context: Execution context

        Returns:
            Configured status
        """
        self.was_ticked = True
        return self.return_status


def test_sequence_node_all_succeed() -> None:
    """Test SequenceNode returns SUCCESS when all children succeed."""
    node1 = MockNode(return_status=NodeStatus.SUCCESS)
    node2 = MockNode(return_status=NodeStatus.SUCCESS)
    node3 = MockNode(return_status=NodeStatus.SUCCESS)

    sequence = SequenceNode(children=[node1, node2, node3])
    mock_context = Mock(spec=BehaviorContext)

    status = sequence.tick(context=mock_context)

    assert status == NodeStatus.SUCCESS
    assert node1.was_ticked
    assert node2.was_ticked
    assert node3.was_ticked


def test_sequence_node_first_child_fails() -> None:
    """Test SequenceNode returns FAILURE when first child fails."""
    node1 = MockNode(return_status=NodeStatus.FAILURE)
    node2 = MockNode(return_status=NodeStatus.SUCCESS)

    sequence = SequenceNode(children=[node1, node2])
    mock_context = Mock(spec=BehaviorContext)

    status = sequence.tick(context=mock_context)

    assert status == NodeStatus.FAILURE
    assert node1.was_ticked
    assert not node2.was_ticked


def test_sequence_node_middle_child_fails() -> None:
    """Test SequenceNode returns FAILURE when middle child fails."""
    node1 = MockNode(return_status=NodeStatus.SUCCESS)
    node2 = MockNode(return_status=NodeStatus.FAILURE)
    node3 = MockNode(return_status=NodeStatus.SUCCESS)

    sequence = SequenceNode(children=[node1, node2, node3])
    mock_context = Mock(spec=BehaviorContext)

    status = sequence.tick(context=mock_context)

    assert status == NodeStatus.FAILURE
    assert node1.was_ticked
    assert node2.was_ticked
    assert not node3.was_ticked


def test_sequence_node_child_running() -> None:
    """Test SequenceNode returns RUNNING when child is running."""
    node1 = MockNode(return_status=NodeStatus.SUCCESS)
    node2 = MockNode(return_status=NodeStatus.RUNNING)
    node3 = MockNode(return_status=NodeStatus.SUCCESS)

    sequence = SequenceNode(children=[node1, node2, node3])
    mock_context = Mock(spec=BehaviorContext)

    status = sequence.tick(context=mock_context)

    assert status == NodeStatus.RUNNING
    assert node1.was_ticked
    assert node2.was_ticked
    assert not node3.was_ticked


def test_selector_node_first_child_succeeds() -> None:
    """Test SelectorNode returns SUCCESS when first child succeeds."""
    node1 = MockNode(return_status=NodeStatus.SUCCESS)
    node2 = MockNode(return_status=NodeStatus.FAILURE)

    selector = SelectorNode(children=[node1, node2])
    mock_context = Mock(spec=BehaviorContext)

    status = selector.tick(context=mock_context)

    assert status == NodeStatus.SUCCESS
    assert node1.was_ticked
    assert not node2.was_ticked


def test_selector_node_second_child_succeeds() -> None:
    """Test SelectorNode returns SUCCESS when second child succeeds."""
    node1 = MockNode(return_status=NodeStatus.FAILURE)
    node2 = MockNode(return_status=NodeStatus.SUCCESS)

    selector = SelectorNode(children=[node1, node2])
    mock_context = Mock(spec=BehaviorContext)

    status = selector.tick(context=mock_context)

    assert status == NodeStatus.SUCCESS
    assert node1.was_ticked
    assert node2.was_ticked


def test_selector_node_all_fail() -> None:
    """Test SelectorNode returns FAILURE when all children fail."""
    node1 = MockNode(return_status=NodeStatus.FAILURE)
    node2 = MockNode(return_status=NodeStatus.FAILURE)
    node3 = MockNode(return_status=NodeStatus.FAILURE)

    selector = SelectorNode(children=[node1, node2, node3])
    mock_context = Mock(spec=BehaviorContext)

    status = selector.tick(context=mock_context)

    assert status == NodeStatus.FAILURE
    assert node1.was_ticked
    assert node2.was_ticked
    assert node3.was_ticked


def test_selector_node_child_running() -> None:
    """Test SelectorNode returns RUNNING when child is running."""
    node1 = MockNode(return_status=NodeStatus.FAILURE)
    node2 = MockNode(return_status=NodeStatus.RUNNING)
    node3 = MockNode(return_status=NodeStatus.SUCCESS)

    selector = SelectorNode(children=[node1, node2, node3])
    mock_context = Mock(spec=BehaviorContext)

    status = selector.tick(context=mock_context)

    assert status == NodeStatus.RUNNING
    assert node1.was_ticked
    assert node2.was_ticked
    assert not node3.was_ticked


def test_parallel_node_all_succeed() -> None:
    """Test ParallelNode returns SUCCESS when all children succeed."""
    node1 = MockNode(return_status=NodeStatus.SUCCESS)
    node2 = MockNode(return_status=NodeStatus.SUCCESS)
    node3 = MockNode(return_status=NodeStatus.SUCCESS)

    parallel = ParallelNode(children=[node1, node2, node3])
    mock_context = Mock(spec=BehaviorContext)

    status = parallel.tick(context=mock_context)

    assert status == NodeStatus.SUCCESS
    assert node1.was_ticked
    assert node2.was_ticked
    assert node3.was_ticked


def test_parallel_node_one_fails() -> None:
    """Test ParallelNode returns FAILURE when any child fails."""
    node1 = MockNode(return_status=NodeStatus.SUCCESS)
    node2 = MockNode(return_status=NodeStatus.FAILURE)
    node3 = MockNode(return_status=NodeStatus.SUCCESS)

    parallel = ParallelNode(children=[node1, node2, node3])
    mock_context = Mock(spec=BehaviorContext)

    status = parallel.tick(context=mock_context)

    assert status == NodeStatus.FAILURE
    assert node1.was_ticked
    assert node2.was_ticked
    assert not node3.was_ticked


def test_parallel_node_one_running() -> None:
    """Test ParallelNode returns RUNNING when any child is running."""
    node1 = MockNode(return_status=NodeStatus.SUCCESS)
    node2 = MockNode(return_status=NodeStatus.RUNNING)
    node3 = MockNode(return_status=NodeStatus.SUCCESS)

    parallel = ParallelNode(children=[node1, node2, node3])
    mock_context = Mock(spec=BehaviorContext)

    status = parallel.tick(context=mock_context)

    assert status == NodeStatus.RUNNING
    assert node1.was_ticked
    assert node2.was_ticked
    assert node3.was_ticked


def test_composite_node_reset() -> None:
    """Test CompositeNode reset clears child index."""
    node = SequenceNode()
    node.current_child_index = 5

    node.reset()

    assert node.current_child_index == 0


def test_composite_node_empty_children() -> None:
    """Test composite nodes with empty children list."""
    sequence = SequenceNode(children=[])
    selector = SelectorNode(children=[])
    parallel = ParallelNode(children=[])
    mock_context = Mock(spec=BehaviorContext)

    assert sequence.tick(context=mock_context) == NodeStatus.SUCCESS
    assert selector.tick(context=mock_context) == NodeStatus.FAILURE
    assert parallel.tick(context=mock_context) == NodeStatus.SUCCESS

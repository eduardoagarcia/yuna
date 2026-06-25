"""Tests for behavior tree system."""

from unittest.mock import Mock

from yuna.ai.behavior_tree.component import BehaviorTreeComponent
from yuna.ai.behavior_tree.node import BehaviorNode
from yuna.ai.behavior_tree.system import BehaviorTreeSystem
from yuna.ai.behavior_tree.types import (
    BehaviorContext,
    NodeStatus,
)
from yuna.ai.blackboard import Blackboard
from yuna.types.identifiers import EntityID


class MockNode(BehaviorNode):
    """Mock node for testing."""

    def __init__(self) -> None:
        """Initialize mock node."""
        self.tick_count = 0
        self.last_context: BehaviorContext | None = None

    def tick(self, context: BehaviorContext) -> NodeStatus:
        """Execute and track context.

        Args:
            context: Execution context

        Returns:
            SUCCESS status
        """
        self.tick_count += 1
        self.last_context = context
        return NodeStatus.SUCCESS


def test_behavior_tree_system_priority() -> None:
    """Test BehaviorTreeSystem has correct priority."""
    system = BehaviorTreeSystem()

    assert system.priority == 200


def test_behavior_tree_system_executes_tree() -> None:
    """Test BehaviorTreeSystem executes behavior tree."""
    system = BehaviorTreeSystem()
    mock_world = Mock()

    entity_id = EntityID("agent-1")
    mock_node = MockNode()
    tree_component = BehaviorTreeComponent(root=mock_node, tick_interval=1)
    blackboard = Blackboard()

    mock_query_builder = Mock()
    mock_query = Mock()
    mock_query.get_entities.return_value = [entity_id]
    mock_query_builder.with_components.return_value = mock_query
    mock_world.query.return_value = mock_query_builder
    mock_world.get_component.side_effect = lambda entity_id, component_type: (
        tree_component if component_type == BehaviorTreeComponent else blackboard
    )

    system.update(world=mock_world, delta_time=0.016)

    assert mock_node.tick_count == 1
    assert mock_node.last_context is not None
    assert mock_node.last_context.world == mock_world
    assert mock_node.last_context.entity_id == entity_id
    assert mock_node.last_context.blackboard == blackboard
    assert mock_node.last_context.delta_time == 0.016


def test_behavior_tree_system_respects_tick_interval() -> None:
    """Test BehaviorTreeSystem respects component tick interval."""
    system = BehaviorTreeSystem()
    mock_world = Mock()

    entity_id = EntityID("agent-1")
    mock_node = MockNode()
    tree_component = BehaviorTreeComponent(root=mock_node, tick_interval=3)
    blackboard = Blackboard()

    mock_query_builder = Mock()
    mock_query = Mock()
    mock_query.get_entities.return_value = [entity_id]
    mock_query_builder.with_components.return_value = mock_query
    mock_world.query.return_value = mock_query_builder
    mock_world.get_component.side_effect = lambda entity_id, component_type: (
        tree_component if component_type == BehaviorTreeComponent else blackboard
    )

    system.update(world=mock_world, delta_time=0.016)
    system.update(world=mock_world, delta_time=0.016)
    system.update(world=mock_world, delta_time=0.016)

    assert mock_node.tick_count == 1


def test_behavior_tree_system_skips_disabled_components() -> None:
    """Test BehaviorTreeSystem skips disabled components."""
    system = BehaviorTreeSystem()
    mock_world = Mock()

    entity_id = EntityID("agent-1")
    mock_node = MockNode()
    tree_component = BehaviorTreeComponent(
        root=mock_node,
        tick_interval=1,
        enabled=False,
    )
    blackboard = Blackboard()

    mock_query_builder = Mock()
    mock_query = Mock()
    mock_query.get_entities.return_value = [entity_id]
    mock_query_builder.with_components.return_value = mock_query
    mock_world.query.return_value = mock_query_builder
    mock_world.get_component.side_effect = lambda entity_id, component_type: (
        tree_component if component_type == BehaviorTreeComponent else blackboard
    )

    system.update(world=mock_world, delta_time=0.016)

    assert mock_node.tick_count == 0


def test_behavior_tree_system_skips_components_without_root() -> None:
    """Test BehaviorTreeSystem skips components without root node."""
    system = BehaviorTreeSystem()
    mock_world = Mock()

    entity_id = EntityID("agent-1")
    tree_component = BehaviorTreeComponent(root=None, tick_interval=1)
    blackboard = Blackboard()

    mock_query_builder = Mock()
    mock_query = Mock()
    mock_query.get_entities.return_value = [entity_id]
    mock_query_builder.with_components.return_value = mock_query
    mock_world.query.return_value = mock_query_builder
    mock_world.get_component.side_effect = lambda entity_id, component_type: (
        tree_component if component_type == BehaviorTreeComponent else blackboard
    )

    system.update(world=mock_world, delta_time=0.016)


def test_behavior_tree_system_processes_multiple_entities() -> None:
    """Test BehaviorTreeSystem processes multiple AI entities."""
    system = BehaviorTreeSystem()
    mock_world = Mock()

    entity_id_1 = EntityID("agent-1")
    mock_node_1 = MockNode()
    tree_component_1 = BehaviorTreeComponent(root=mock_node_1, tick_interval=1)
    blackboard_1 = Blackboard()

    entity_id_2 = EntityID("agent-2")
    mock_node_2 = MockNode()
    tree_component_2 = BehaviorTreeComponent(root=mock_node_2, tick_interval=1)
    blackboard_2 = Blackboard()

    mock_query_builder = Mock()
    mock_query = Mock()
    mock_query.get_entities.return_value = [entity_id_1, entity_id_2]
    mock_query_builder.with_components.return_value = mock_query
    mock_world.query.return_value = mock_query_builder

    def get_component_side_effect(entity_id, component_type):
        if entity_id == entity_id_1:
            return (
                tree_component_1
                if component_type == BehaviorTreeComponent
                else blackboard_1
            )
        else:
            return (
                tree_component_2
                if component_type == BehaviorTreeComponent
                else blackboard_2
            )

    mock_world.get_component.side_effect = get_component_side_effect

    system.update(world=mock_world, delta_time=0.016)

    assert mock_node_1.tick_count == 1
    assert mock_node_2.tick_count == 1
    assert mock_node_1.last_context is not None
    assert mock_node_2.last_context is not None
    assert mock_node_1.last_context.entity_id == entity_id_1
    assert mock_node_2.last_context.entity_id == entity_id_2


def test_behavior_tree_system_queries_correct_components() -> None:
    """Test BehaviorTreeSystem queries for correct component types."""
    system = BehaviorTreeSystem()
    mock_world = Mock()

    mock_query_builder = Mock()
    mock_query = Mock()
    mock_query.get_entities.return_value = []
    mock_query_builder.with_components.return_value = mock_query
    mock_world.query.return_value = mock_query_builder

    system.update(world=mock_world, delta_time=0.016)

    mock_query_builder.with_components.assert_called_once_with(
        BehaviorTreeComponent,
        Blackboard,
    )


def test_behavior_tree_system_handles_missing_component() -> None:
    """Test BehaviorTreeSystem handles entities with missing components."""
    system = BehaviorTreeSystem()
    mock_world = Mock()

    entity_id = EntityID("agent-1")

    mock_query_builder = Mock()
    mock_query = Mock()
    mock_query.get_entities.return_value = [entity_id]
    mock_query_builder.with_components.return_value = mock_query
    mock_world.query.return_value = mock_query_builder
    mock_world.get_component.return_value = None

    system.update(world=mock_world, delta_time=0.016)


def test_behavior_tree_system_handles_missing_blackboard() -> None:
    """Test BehaviorTreeSystem handles entities with missing blackboard."""
    system = BehaviorTreeSystem()
    mock_world = Mock()

    entity_id = EntityID("agent-1")
    mock_node = MockNode()
    tree_component = BehaviorTreeComponent(root=mock_node, tick_interval=1)

    mock_query_builder = Mock()
    mock_query = Mock()
    mock_query.get_entities.return_value = [entity_id]
    mock_query_builder.with_components.return_value = mock_query
    mock_world.query.return_value = mock_query_builder

    def get_component_side_effect(entity_id, component_type):
        if component_type == BehaviorTreeComponent:
            return tree_component
        return None

    mock_world.get_component.side_effect = get_component_side_effect

    system.update(world=mock_world, delta_time=0.016)

    assert mock_node.tick_count == 0

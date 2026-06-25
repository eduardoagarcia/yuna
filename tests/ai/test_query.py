"""Tests for AI query system."""

from unittest.mock import Mock

from faker import Faker

from yuna.ai.behavior_tree.component import BehaviorTreeComponent
from yuna.ai.behavior_tree.types import NodeStatus
from yuna.ai.blackboard import Blackboard
from yuna.ai.perception import PerceivedEntities
from yuna.ai.query import AIQuery
from yuna.ecs.world import ECSWorld
from yuna.types.identifiers import EntityID

fake = Faker()


def test_find_by_blackboard_value_matching() -> None:
    """Test finding entities with matching blackboard value."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()
    entity2 = world.create_entity()
    entity3 = world.create_entity()

    blackboard1 = Blackboard()
    blackboard1.set_value(key="state", value="aggressive")
    blackboard2 = Blackboard()
    blackboard2.set_value(key="state", value="aggressive")
    blackboard3 = Blackboard()
    blackboard3.set_value(key="state", value="passive")

    world.add_component(entity_id=entity1, component=blackboard1)
    world.add_component(entity_id=entity2, component=blackboard2)
    world.add_component(entity_id=entity3, component=blackboard3)

    results = query.find_by_blackboard_value(
        world=world,
        key="state",
        value="aggressive",
    )

    assert len(results) == 2
    assert entity1 in results
    assert entity2 in results
    assert entity3 not in results


def test_find_by_blackboard_value_no_matches() -> None:
    """Test finding entities with no matching blackboard value."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()

    blackboard1 = Blackboard()
    blackboard1.set_value(key="state", value="passive")

    world.add_component(entity_id=entity1, component=blackboard1)

    results = query.find_by_blackboard_value(
        world=world,
        key="state",
        value="aggressive",
    )

    assert len(results) == 0


def test_find_by_blackboard_value_missing_key() -> None:
    """Test finding entities when blackboard missing key."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()

    blackboard1 = Blackboard()
    blackboard1.set_value(key="other_key", value="value")

    world.add_component(entity_id=entity1, component=blackboard1)

    results = query.find_by_blackboard_value(
        world=world,
        key="state",
        value="aggressive",
    )

    assert len(results) == 0


def test_find_by_blackboard_value_empty_world() -> None:
    """Test finding entities in empty world."""
    world = ECSWorld()
    query = AIQuery()

    results = query.find_by_blackboard_value(
        world=world,
        key="state",
        value="aggressive",
    )

    assert len(results) == 0


def test_find_by_behavior_tree_status_success() -> None:
    """Test finding entities with SUCCESS behavior tree status."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()
    entity2 = world.create_entity()

    root1 = Mock()
    root1._last_status = NodeStatus.SUCCESS
    root2 = Mock()
    root2._last_status = NodeStatus.FAILURE

    tree1 = BehaviorTreeComponent(root=root1)
    tree2 = BehaviorTreeComponent(root=root2)

    world.add_component(entity_id=entity1, component=tree1)
    world.add_component(entity_id=entity2, component=tree2)

    results = query.find_by_behavior_tree_status(
        world=world,
        status=NodeStatus.SUCCESS,
    )

    assert len(results) == 1
    assert entity1 in results


def test_find_by_behavior_tree_status_running() -> None:
    """Test finding entities with RUNNING behavior tree status."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()

    root1 = Mock()
    root1._last_status = NodeStatus.RUNNING

    tree1 = BehaviorTreeComponent(root=root1)

    world.add_component(entity_id=entity1, component=tree1)

    results = query.find_by_behavior_tree_status(
        world=world,
        status=NodeStatus.RUNNING,
    )

    assert len(results) == 1
    assert entity1 in results


def test_find_by_behavior_tree_status_disabled_tree() -> None:
    """Test finding entities skips disabled behavior trees."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()

    root1 = Mock()
    root1._last_status = NodeStatus.SUCCESS

    tree1 = BehaviorTreeComponent(root=root1, enabled=False)

    world.add_component(entity_id=entity1, component=tree1)

    results = query.find_by_behavior_tree_status(
        world=world,
        status=NodeStatus.SUCCESS,
    )

    assert len(results) == 0


def test_find_by_behavior_tree_status_no_root() -> None:
    """Test finding entities skips trees with no root."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()

    tree1 = BehaviorTreeComponent(root=None)

    world.add_component(entity_id=entity1, component=tree1)

    results = query.find_by_behavior_tree_status(
        world=world,
        status=NodeStatus.SUCCESS,
    )

    assert len(results) == 0


def test_find_by_behavior_tree_status_no_last_status() -> None:
    """Test finding entities skips trees without _last_status."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()

    root1 = Mock(spec=[])

    tree1 = BehaviorTreeComponent(root=root1)

    world.add_component(entity_id=entity1, component=tree1)

    results = query.find_by_behavior_tree_status(
        world=world,
        status=NodeStatus.SUCCESS,
    )

    assert len(results) == 0


def test_find_perceiving_entity_visible() -> None:
    """Test finding entities that can see target."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()
    target = EntityID(fake.uuid4())

    perceived1 = PerceivedEntities()
    perceived1.visible.add(target)

    world.add_component(entity_id=entity1, component=perceived1)

    results = query.find_perceiving_entity(
        world=world,
        target_entity=target,
    )

    assert len(results) == 1
    assert entity1 in results


def test_find_perceiving_entity_audible() -> None:
    """Test finding entities that can hear target."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()
    target = EntityID(fake.uuid4())

    perceived1 = PerceivedEntities()
    perceived1.audible.add(target)

    world.add_component(entity_id=entity1, component=perceived1)

    results = query.find_perceiving_entity(
        world=world,
        target_entity=target,
    )

    assert len(results) == 1
    assert entity1 in results


def test_find_perceiving_entity_both() -> None:
    """Test finding entities that can see and hear target."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()
    target = EntityID(fake.uuid4())

    perceived1 = PerceivedEntities()
    perceived1.visible.add(target)
    perceived1.audible.add(target)

    world.add_component(entity_id=entity1, component=perceived1)

    results = query.find_perceiving_entity(
        world=world,
        target_entity=target,
    )

    assert len(results) == 1
    assert entity1 in results


def test_find_perceiving_entity_multiple() -> None:
    """Test finding multiple entities perceiving target."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()
    entity2 = world.create_entity()
    target = EntityID(fake.uuid4())

    perceived1 = PerceivedEntities()
    perceived1.visible.add(target)
    perceived2 = PerceivedEntities()
    perceived2.audible.add(target)

    world.add_component(entity_id=entity1, component=perceived1)
    world.add_component(entity_id=entity2, component=perceived2)

    results = query.find_perceiving_entity(
        world=world,
        target_entity=target,
    )

    assert len(results) == 2
    assert entity1 in results
    assert entity2 in results


def test_find_perceiving_entity_not_perceiving() -> None:
    """Test finding entities that don't perceive target."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()
    target = EntityID(fake.uuid4())
    other_target = EntityID(fake.uuid4())

    perceived1 = PerceivedEntities()
    perceived1.visible.add(other_target)

    world.add_component(entity_id=entity1, component=perceived1)

    results = query.find_perceiving_entity(
        world=world,
        target_entity=target,
    )

    assert len(results) == 0


def test_bulk_update_blackboard() -> None:
    """Test bulk updating blackboard values."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()
    entity2 = world.create_entity()

    blackboard1 = Blackboard()
    blackboard2 = Blackboard()

    world.add_component(entity_id=entity1, component=blackboard1)
    world.add_component(entity_id=entity2, component=blackboard2)

    query.bulk_update_blackboard(
        world=world,
        entity_ids=[entity1, entity2],
        key="alert_level",
        value=10,
    )

    assert blackboard1.get_value(key="alert_level") == 10
    assert blackboard2.get_value(key="alert_level") == 10


def test_bulk_update_blackboard_empty_list() -> None:
    """Test bulk updating with empty entity list."""
    world = ECSWorld()
    query = AIQuery()

    query.bulk_update_blackboard(
        world=world,
        entity_ids=[],
        key="alert_level",
        value=10,
    )


def test_bulk_update_blackboard_missing_component() -> None:
    """Test bulk updating when entity missing blackboard."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()

    query.bulk_update_blackboard(
        world=world,
        entity_ids=[entity1],
        key="alert_level",
        value=10,
    )


def test_bulk_update_blackboard_existing_value() -> None:
    """Test bulk updating overwrites existing blackboard values."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()

    blackboard1 = Blackboard()
    blackboard1.set_value(key="alert_level", value=5)

    world.add_component(entity_id=entity1, component=blackboard1)

    query.bulk_update_blackboard(
        world=world,
        entity_ids=[entity1],
        key="alert_level",
        value=10,
    )

    assert blackboard1.get_value(key="alert_level") == 10


def test_bulk_interrupt_behavior_trees() -> None:
    """Test bulk interrupting behavior trees."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()
    entity2 = world.create_entity()

    root1 = Mock()
    root2 = Mock()

    tree1 = BehaviorTreeComponent(root=root1, enabled=True)
    tree2 = BehaviorTreeComponent(root=root2, enabled=True)

    tree1._ticks_since_update = 5
    tree2._ticks_since_update = 3

    world.add_component(entity_id=entity1, component=tree1)
    world.add_component(entity_id=entity2, component=tree2)

    query.bulk_interrupt_behavior_trees(
        world=world,
        entity_ids=[entity1, entity2],
    )

    assert tree1.enabled is True
    assert tree2.enabled is True
    assert tree1._ticks_since_update == 0
    assert tree2._ticks_since_update == 0


def test_bulk_interrupt_behavior_trees_empty_list() -> None:
    """Test bulk interrupting with empty entity list."""
    world = ECSWorld()
    query = AIQuery()

    query.bulk_interrupt_behavior_trees(
        world=world,
        entity_ids=[],
    )


def test_bulk_interrupt_behavior_trees_missing_component() -> None:
    """Test bulk interrupting when entity missing tree."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()

    query.bulk_interrupt_behavior_trees(
        world=world,
        entity_ids=[entity1],
    )


def test_bulk_interrupt_behavior_trees_disabled_tree() -> None:
    """Test bulk interrupting re-enables disabled trees."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()

    root1 = Mock()

    tree1 = BehaviorTreeComponent(root=root1, enabled=False)
    tree1._ticks_since_update = 5

    world.add_component(entity_id=entity1, component=tree1)

    query.bulk_interrupt_behavior_trees(
        world=world,
        entity_ids=[entity1],
    )

    assert tree1.enabled is True
    assert tree1._ticks_since_update == 0


def test_find_by_blackboard_value_different_types() -> None:
    """Test finding entities with different value types."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()
    entity2 = world.create_entity()
    entity3 = world.create_entity()

    blackboard1 = Blackboard()
    blackboard1.set_value(key="count", value=10)
    blackboard2 = Blackboard()
    blackboard2.set_value(key="count", value=20)
    blackboard3 = Blackboard()
    blackboard3.set_value(key="count", value=10)

    world.add_component(entity_id=entity1, component=blackboard1)
    world.add_component(entity_id=entity2, component=blackboard2)
    world.add_component(entity_id=entity3, component=blackboard3)

    results = query.find_by_blackboard_value(
        world=world,
        key="count",
        value=10,
    )

    assert len(results) == 2
    assert entity1 in results
    assert entity3 in results


def test_find_perceiving_entity_empty_perception() -> None:
    """Test finding entities with empty perception sets."""
    world = ECSWorld()
    query = AIQuery()

    entity1 = world.create_entity()
    target = EntityID(fake.uuid4())

    perceived1 = PerceivedEntities()

    world.add_component(entity_id=entity1, component=perceived1)

    results = query.find_perceiving_entity(
        world=world,
        target_entity=target,
    )

    assert len(results) == 0

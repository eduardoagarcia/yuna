"""Tests for priority calculation and entity sorting."""

from faker import Faker

from yuna.ecs.priority import (
    EqualPriorityCalculator,
    PriorityCalculator,
)
from yuna.ecs.world import ECSWorld
from yuna.types.identifiers import EntityID

fake = Faker()


def test_equal_priority_calculator_returns_equal_priority():
    """All entities get same priority with equal calculator."""
    world = ECSWorld(seed=42)
    calculator = EqualPriorityCalculator()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    priority1 = calculator.calculate_priority(entity_id=entity1, world=world)
    priority2 = calculator.calculate_priority(entity_id=entity2, world=world)

    assert priority1 == 0.5
    assert priority2 == 0.5
    assert priority1 == priority2


def test_world_sort_empty_list_returns_empty():
    """Sorting empty list returns empty list."""
    world = ECSWorld(seed=42)

    sorted_entities = world.sort_entities_by_priority(
        entity_ids=[],
        priority_calculator=None,
        tick=0,
    )

    assert sorted_entities == []


def test_world_sort_single_entity_returns_same():
    """Sorting single entity returns same entity."""
    world = ECSWorld(seed=42)
    entity = EntityID(fake.uuid4())

    sorted_entities = world.sort_entities_by_priority(
        entity_ids=[entity],
        priority_calculator=None,
        tick=0,
    )

    assert sorted_entities == [entity]


def test_world_sort_uses_equal_priority_by_default():
    """World uses EqualPriorityCalculator when no calculator provided."""
    world = ECSWorld(seed=42)
    entities = [EntityID(fake.uuid4()) for _ in range(5)]

    sorted_entities = world.sort_entities_by_priority(
        entity_ids=entities,
        priority_calculator=None,
        tick=0,
    )

    assert len(sorted_entities) == len(entities)
    assert set(sorted_entities) == set(entities)


def test_world_sort_deterministic_with_same_seed():
    """Same seed produces same ordering for equal priority entities."""
    seed = fake.random_int(min=1, max=10000)
    tick = fake.random_int(min=0, max=100)
    entities = [EntityID(fake.uuid4()) for _ in range(10)]

    world1 = ECSWorld(seed=seed)
    sorted1 = world1.sort_entities_by_priority(
        entity_ids=entities[:],
        priority_calculator=None,
        tick=tick,
    )

    world2 = ECSWorld(seed=seed)
    sorted2 = world2.sort_entities_by_priority(
        entity_ids=entities[:],
        priority_calculator=None,
        tick=tick,
    )

    assert sorted1 == sorted2


def test_world_sort_different_seed_may_differ():
    """Different seeds may produce different ordering for equal priority."""
    entities = [EntityID(fake.uuid4()) for _ in range(10)]
    tick = fake.random_int(min=0, max=100)

    world1 = ECSWorld(seed=1)
    sorted1 = world1.sort_entities_by_priority(
        entity_ids=entities[:],
        priority_calculator=None,
        tick=tick,
    )

    world2 = ECSWorld(seed=2)
    sorted2 = world2.sort_entities_by_priority(
        entity_ids=entities[:],
        priority_calculator=None,
        tick=tick,
    )

    assert set(sorted1) == set(sorted2)


def test_world_sort_respects_priority_order():
    """Higher priority entities sorted before lower priority entities."""

    class CustomPriorityCalculator:
        def __init__(self, priorities: dict[EntityID, float]):
            self._priorities = priorities

        def calculate_priority(self, entity_id: EntityID, world: ECSWorld) -> float:
            return self._priorities.get(entity_id, 0.5)

    world = ECSWorld(seed=42)
    high_priority_entity = EntityID(fake.uuid4())
    medium_priority_entity = EntityID(fake.uuid4())
    low_priority_entity = EntityID(fake.uuid4())

    priorities = {
        high_priority_entity: 0.9,
        medium_priority_entity: 0.5,
        low_priority_entity: 0.1,
    }
    calculator = CustomPriorityCalculator(priorities=priorities)

    entities = [low_priority_entity, high_priority_entity, medium_priority_entity]
    sorted_entities = world.sort_entities_by_priority(
        entity_ids=entities,
        priority_calculator=calculator,
        tick=0,
    )

    assert sorted_entities[0] == high_priority_entity
    assert sorted_entities[1] == medium_priority_entity
    assert sorted_entities[2] == low_priority_entity


def test_world_sort_tie_breaking_deterministic():
    """Equal priority entities ordered consistently with same seed and tick."""

    class FixedPriorityCalculator:
        def calculate_priority(self, entity_id: EntityID, world: ECSWorld) -> float:
            return 0.5

    world = ECSWorld(seed=42)
    entities = [EntityID(fake.uuid4()) for _ in range(10)]
    calculator = FixedPriorityCalculator()

    sorted1 = world.sort_entities_by_priority(
        entity_ids=entities[:],
        priority_calculator=calculator,
        tick=5,
    )

    sorted2 = world.sort_entities_by_priority(
        entity_ids=entities[:],
        priority_calculator=calculator,
        tick=5,
    )

    assert sorted1 == sorted2


def test_world_sort_different_tick_may_differ():
    """Different tick values may produce different tie-breaking order."""
    world = ECSWorld(seed=42)
    entities = [EntityID(fake.uuid4()) for _ in range(10)]

    sorted1 = world.sort_entities_by_priority(
        entity_ids=entities[:],
        priority_calculator=None,
        tick=1,
    )

    sorted2 = world.sort_entities_by_priority(
        entity_ids=entities[:],
        priority_calculator=None,
        tick=2,
    )

    assert set(sorted1) == set(sorted2)


def test_world_sort_accepts_different_calculators():
    """World can use different calculators for different sorts."""

    class Calculator1:
        def calculate_priority(self, entity_id: EntityID, world: ECSWorld) -> float:
            return 0.3

    class Calculator2:
        def calculate_priority(self, entity_id: EntityID, world: ECSWorld) -> float:
            return 0.7

    world = ECSWorld(seed=42)
    entity = EntityID(fake.uuid4())

    calculator1 = Calculator1()
    calculator2 = Calculator2()

    priorities1 = [calculator1.calculate_priority(entity_id=entity, world=world)]
    priorities2 = [calculator2.calculate_priority(entity_id=entity, world=world)]

    assert priorities1[0] == 0.3
    assert priorities2[0] == 0.7


def test_priority_calculator_protocol_compliance():
    """Custom calculator can implement PriorityCalculator protocol."""

    class TestCalculator:
        def calculate_priority(self, entity_id: EntityID, world: ECSWorld) -> float:
            return 0.8

    world = ECSWorld(seed=42)
    calculator: PriorityCalculator = TestCalculator()
    entity = EntityID(fake.uuid4())

    priority = calculator.calculate_priority(entity_id=entity, world=world)
    assert priority == 0.8


def test_world_seed_stored_correctly():
    """World stores seed value correctly."""
    seed = fake.random_int(min=1, max=10000)
    world = ECSWorld(seed=seed)

    assert world.seed == seed


def test_world_seed_defaults_to_zero():
    """World seed defaults to 0 when not provided."""
    world = ECSWorld()

    assert world.seed == 0


def test_world_sort_tie_break_independent_of_input_order():
    """Equal-priority tie-break is canonical regardless of input list order.

    Regression for a determinism bug where the seeded shuffle was fed a
    non-deterministically ordered input list, so identical entity sets in
    different orders produced divergent results across runs.
    """

    class FixedPriorityCalculator:
        def calculate_priority(self, entity_id: EntityID, world: ECSWorld) -> float:
            return 0.5

    seed = fake.random_int(min=1, max=10000)
    tick = fake.random_int(min=0, max=100)
    entities = [EntityID(fake.uuid4()) for _ in range(12)]
    shuffled = entities[:]
    fake.random.shuffle(shuffled)

    sorted_original = ECSWorld(seed=seed).sort_entities_by_priority(
        entity_ids=entities[:],
        priority_calculator=FixedPriorityCalculator(),
        tick=tick,
    )
    sorted_shuffled = ECSWorld(seed=seed).sort_entities_by_priority(
        entity_ids=shuffled,
        priority_calculator=FixedPriorityCalculator(),
        tick=tick,
    )

    assert sorted_original == sorted_shuffled


def test_world_sort_preserves_all_entities():
    """Sorting preserves all entities in the list."""
    world = ECSWorld(seed=42)
    entities = [EntityID(fake.uuid4()) for _ in range(20)]

    sorted_entities = world.sort_entities_by_priority(
        entity_ids=entities,
        priority_calculator=None,
        tick=0,
    )

    assert len(sorted_entities) == len(entities)
    assert set(sorted_entities) == set(entities)

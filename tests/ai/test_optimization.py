"""Tests for AI optimization tools."""

from faker import Faker

from yuna.ai.optimization import AIOptimization, AIScheduler
from yuna.types.identifiers import EntityID

fake = Faker()


def test_ai_scheduler_initialization() -> None:
    """Test AIScheduler initializes with correct defaults."""
    scheduler = AIScheduler()

    assert scheduler._groups == 10
    assert scheduler._current_group == 0
    assert scheduler._entity_assignments == {}


def test_ai_scheduler_custom_groups() -> None:
    """Test AIScheduler initializes with custom group count."""
    groups = fake.random_int(min=1, max=20)
    scheduler = AIScheduler(groups=groups)

    assert scheduler._groups == groups


def test_ai_scheduler_assign_entity() -> None:
    """Test AIScheduler assigns entity to group."""
    scheduler = AIScheduler(groups=5)
    entity_id = EntityID(fake.uuid4())

    scheduler.assign_entity(entity_id=entity_id)

    assert entity_id in scheduler._entity_assignments
    assert 0 <= scheduler._entity_assignments[entity_id] < 5


def test_ai_scheduler_assign_entity_deterministic() -> None:
    """Test AIScheduler assigns same entity to same group consistently."""
    scheduler = AIScheduler(groups=10)
    entity_id = EntityID(fake.uuid4())

    scheduler.assign_entity(entity_id=entity_id)
    first_group = scheduler._entity_assignments[entity_id]

    scheduler.assign_entity(entity_id=entity_id)
    second_group = scheduler._entity_assignments[entity_id]

    assert first_group == second_group


def test_ai_scheduler_should_update_auto_assign() -> None:
    """Test should_update auto-assigns entity if not already assigned."""
    scheduler = AIScheduler(groups=5)
    entity_id = EntityID(fake.uuid4())

    assert entity_id not in scheduler._entity_assignments

    scheduler.should_update(entity_id=entity_id)

    assert entity_id in scheduler._entity_assignments


def test_ai_scheduler_should_update_current_group() -> None:
    """Test should_update returns True for entity in current group."""
    scheduler = AIScheduler(groups=5)
    entity_id = EntityID(fake.uuid4())

    scheduler.assign_entity(entity_id=entity_id)
    assigned_group = scheduler._entity_assignments[entity_id]
    scheduler._current_group = assigned_group

    assert scheduler.should_update(entity_id=entity_id) is True


def test_ai_scheduler_should_update_different_group() -> None:
    """Test should_update returns False for entity in different group."""
    scheduler = AIScheduler(groups=5)
    entity_id = EntityID(fake.uuid4())

    scheduler.assign_entity(entity_id=entity_id)
    assigned_group = scheduler._entity_assignments[entity_id]
    scheduler._current_group = (assigned_group + 1) % 5

    assert scheduler.should_update(entity_id=entity_id) is False


def test_ai_scheduler_advance_frame() -> None:
    """Test advance_frame increments current group."""
    scheduler = AIScheduler(groups=10)

    assert scheduler._current_group == 0

    scheduler.advance_frame()

    assert scheduler._current_group == 1


def test_ai_scheduler_advance_frame_wraps() -> None:
    """Test advance_frame wraps around to 0 after last group."""
    scheduler = AIScheduler(groups=5)
    scheduler._current_group = 4

    scheduler.advance_frame()

    assert scheduler._current_group == 0


def test_ai_scheduler_staggered_updates() -> None:
    """Test AIScheduler distributes entities across groups."""
    scheduler = AIScheduler(groups=3)
    entities = [EntityID(fake.uuid4()) for _ in range(9)]

    for entity_id in entities:
        scheduler.assign_entity(entity_id=entity_id)

    group_0 = [e for e in entities if scheduler._entity_assignments[e] == 0]
    group_1 = [e for e in entities if scheduler._entity_assignments[e] == 1]
    group_2 = [e for e in entities if scheduler._entity_assignments[e] == 2]

    assert len(group_0) + len(group_1) + len(group_2) == 9

    assigned_groups = {scheduler._entity_assignments[e] for e in entities}
    assert len(assigned_groups) >= 1
    assert all(0 <= group < 3 for group in assigned_groups)


def test_ai_scheduler_update_cycle() -> None:
    """Test AIScheduler cycles through all groups."""
    scheduler = AIScheduler(groups=3)
    entity_id = EntityID(fake.uuid4())
    scheduler.assign_entity(entity_id=entity_id)
    assigned_group = scheduler._entity_assignments[entity_id]

    updates = []
    for _ in range(9):
        updates.append(scheduler.should_update(entity_id=entity_id))
        scheduler.advance_frame()

    true_count = sum(updates)
    assert true_count == 3

    for i in range(3):
        expected = (
            i == assigned_group or i + 3 == assigned_group or i + 6 == assigned_group
        )
        assert updates[i] == expected


def test_ai_scheduler_multiple_entities() -> None:
    """Test AIScheduler handles multiple entities correctly."""
    scheduler = AIScheduler(groups=5)
    entities = [EntityID(fake.uuid4()) for _ in range(15)]

    for entity_id in entities:
        scheduler.assign_entity(entity_id=entity_id)

    all_updated = set()
    for group in range(5):
        scheduler._current_group = group
        updating = [e for e in entities if scheduler.should_update(entity_id=e)]
        for entity_id in updating:
            assert scheduler._entity_assignments[entity_id] == group
            all_updated.add(entity_id)

    assert len(all_updated) == 15


def test_ai_optimization_default_values() -> None:
    """Test AIOptimization has correct default values."""
    optimization = AIOptimization()

    assert optimization.update_interval == 1
    assert optimization.distance_scaling is True
    assert optimization.enabled_distance == 100.0


def test_ai_optimization_custom_values() -> None:
    """Test AIOptimization accepts custom values."""
    update_interval = fake.random_int(min=1, max=100)
    distance_scaling = fake.boolean()
    enabled_distance = fake.random.uniform(a=50.0, b=200.0)

    optimization = AIOptimization(
        update_interval=update_interval,
        distance_scaling=distance_scaling,
        enabled_distance=enabled_distance,
    )

    assert optimization.update_interval == update_interval
    assert optimization.distance_scaling == distance_scaling
    assert optimization.enabled_distance == enabled_distance


def test_ai_optimization_update_interval_range() -> None:
    """Test AIOptimization accepts various update intervals."""
    for interval in [1, 5, 10, 30, 60]:
        optimization = AIOptimization(update_interval=interval)
        assert optimization.update_interval == interval


def test_ai_optimization_enabled_distance_range() -> None:
    """Test AIOptimization accepts various enabled distances."""
    for distance in [50.0, 100.0, 200.0, 500.0]:
        optimization = AIOptimization(enabled_distance=distance)
        assert optimization.enabled_distance == distance


def test_ai_optimization_distance_scaling_toggle() -> None:
    """Test AIOptimization distance_scaling can be toggled."""
    optimization_enabled = AIOptimization(distance_scaling=True)
    optimization_disabled = AIOptimization(distance_scaling=False)

    assert optimization_enabled.distance_scaling is True
    assert optimization_disabled.distance_scaling is False


def test_ai_scheduler_hash_distribution() -> None:
    """Test AIScheduler hash-based assignment distributes entities fairly."""
    scheduler = AIScheduler(groups=10)
    entities = [EntityID(fake.uuid4()) for _ in range(100)]

    for entity_id in entities:
        scheduler.assign_entity(entity_id=entity_id)

    group_counts = [0] * 10
    for entity_id in entities:
        group = scheduler._entity_assignments[entity_id]
        group_counts[group] += 1

    for count in group_counts:
        assert count > 0
        assert count <= 20


def test_ai_scheduler_single_group() -> None:
    """Test AIScheduler with single group updates all entities."""
    scheduler = AIScheduler(groups=1)
    entities = [EntityID(fake.uuid4()) for _ in range(5)]

    for entity_id in entities:
        scheduler.assign_entity(entity_id=entity_id)

    for entity_id in entities:
        assert scheduler.should_update(entity_id=entity_id) is True


def test_ai_scheduler_large_group_count() -> None:
    """Test AIScheduler handles large group counts."""
    scheduler = AIScheduler(groups=100)
    entities = [EntityID(fake.uuid4()) for _ in range(100)]

    for entity_id in entities:
        scheduler.assign_entity(entity_id=entity_id)

    assigned_groups = set()
    for entity_id in entities:
        assigned_groups.add(scheduler._entity_assignments[entity_id])

    assert len(assigned_groups) > 50

"""Tests for entity management."""

import pytest
from faker import Faker

from yuna.ecs.entity import EntityManager
from yuna.exceptions import StateError
from yuna.types.identifiers import EntityID

fake = Faker()


def test_entity_manager_creation() -> None:
    """Test EntityManager can be instantiated."""
    manager = EntityManager()
    assert manager is not None


def test_create_entity_without_name() -> None:
    """Test creating entity without name."""
    manager = EntityManager()
    entity_id = manager.create()
    assert isinstance(entity_id, str)
    assert len(entity_id) > 0


def test_create_entity_with_name() -> None:
    """Test creating entity with name."""
    manager = EntityManager()
    name = fake.word()
    entity_id = manager.create(name=name)
    assert isinstance(entity_id, str)
    assert manager.get_name(entity_id=entity_id) == name


def test_create_multiple_entities_have_unique_ids() -> None:
    """Test multiple entities get unique IDs."""
    manager = EntityManager()
    entity_1 = manager.create()
    entity_2 = manager.create()
    entity_3 = manager.create()
    assert entity_1 != entity_2
    assert entity_2 != entity_3
    assert entity_1 != entity_3


def test_exists_returns_true_for_created_entity() -> None:
    """Test exists returns True for newly created entity."""
    manager = EntityManager()
    entity_id = manager.create()
    assert manager.exists(entity_id=entity_id) is True


def test_exists_returns_false_for_non_existent_entity() -> None:
    """Test exists returns False for entity that was never created."""
    manager = EntityManager()
    fake_id = EntityID(fake.uuid4())
    assert manager.exists(entity_id=fake_id) is False


def test_destroy_marks_entity_for_destruction() -> None:
    """Test destroy marks entity but doesn't remove immediately."""
    manager = EntityManager()
    entity_id = manager.create()
    manager.destroy(entity_id=entity_id)
    assert manager.exists(entity_id=entity_id) is False


def test_destroy_non_existent_entity_does_not_raise() -> None:
    """Test destroying non-existent entity is safe."""
    manager = EntityManager()
    fake_id = EntityID(fake.uuid4())
    manager.destroy(entity_id=fake_id)


def test_flush_destroyed_removes_destroyed_entities() -> None:
    """Test flush_destroyed removes all destroyed entities."""
    manager = EntityManager()
    entity_1 = manager.create()
    entity_2 = manager.create()
    manager.destroy(entity_id=entity_1)
    destroyed = manager.flush_destroyed()
    assert entity_1 in destroyed
    assert entity_2 not in destroyed


def test_flush_destroyed_returns_empty_set_when_none_destroyed() -> None:
    """Test flush_destroyed returns empty set when no entities destroyed."""
    manager = EntityManager()
    manager.create()
    manager.create()
    destroyed = manager.flush_destroyed()
    assert len(destroyed) == 0


def test_flush_destroyed_clears_destroyed_list() -> None:
    """Test flush_destroyed clears the destroyed entities list."""
    manager = EntityManager()
    entity_id = manager.create()
    manager.destroy(entity_id=entity_id)
    manager.flush_destroyed()
    destroyed_again = manager.flush_destroyed()
    assert len(destroyed_again) == 0


def test_entity_not_exists_after_flush() -> None:
    """Test entity does not exist after being flushed."""
    manager = EntityManager()
    entity_id = manager.create()
    manager.destroy(entity_id=entity_id)
    manager.flush_destroyed()
    assert manager.exists(entity_id=entity_id) is False


def test_get_name_returns_none_for_unnamed_entity() -> None:
    """Test get_name returns None for entity without name."""
    manager = EntityManager()
    entity_id = manager.create()
    assert manager.get_name(entity_id=entity_id) is None


def test_get_name_returns_none_for_non_existent_entity() -> None:
    """Test get_name returns None for non-existent entity."""
    manager = EntityManager()
    fake_id = EntityID(fake.uuid4())
    assert manager.get_name(entity_id=fake_id) is None


def test_count_returns_zero_initially() -> None:
    """Test count returns zero for new manager."""
    manager = EntityManager()
    assert manager.count() == 0


def test_count_increases_with_created_entities() -> None:
    """Test count increases as entities are created."""
    manager = EntityManager()
    manager.create()
    assert manager.count() == 1
    manager.create()
    assert manager.count() == 2
    manager.create()
    assert manager.count() == 3


def test_count_decreases_when_entity_marked_destroyed() -> None:
    """Test count decreases when entity is marked for destruction."""
    manager = EntityManager()
    entity_1 = manager.create()
    manager.create()
    assert manager.count() == 2
    manager.destroy(entity_id=entity_1)
    assert manager.count() == 1


def test_count_after_flush_destroyed() -> None:
    """Test count is correct after flushing destroyed entities."""
    manager = EntityManager()
    entity_1 = manager.create()
    entity_2 = manager.create()
    manager.create()
    manager.destroy(entity_id=entity_1)
    manager.destroy(entity_id=entity_2)
    manager.flush_destroyed()
    assert manager.count() == 1


def test_multiple_destroys_same_entity() -> None:
    """Test destroying same entity multiple times is safe."""
    manager = EntityManager()
    entity_id = manager.create()
    manager.destroy(entity_id=entity_id)
    manager.destroy(entity_id=entity_id)
    destroyed = manager.flush_destroyed()
    assert entity_id in destroyed
    assert len(destroyed) == 1


def test_flush_destroyed_removes_entity_name() -> None:
    """Test flushing destroyed entity removes its name."""
    manager = EntityManager()
    name = fake.word()
    entity_id = manager.create(name=name)
    manager.destroy(entity_id=entity_id)
    manager.flush_destroyed()
    assert manager.get_name(entity_id=entity_id) is None


def test_create_many_entities() -> None:
    """Test creating many entities works correctly."""
    manager = EntityManager()
    entity_count = 100
    entities = [manager.create() for _ in range(entity_count)]
    assert len(entities) == entity_count
    assert len(set(entities)) == entity_count
    assert manager.count() == entity_count


def test_destroy_all_then_flush() -> None:
    """Test destroying all entities and flushing."""
    manager = EntityManager()
    entities = [manager.create() for _ in range(10)]
    for entity_id in entities:
        manager.destroy(entity_id=entity_id)
    destroyed = manager.flush_destroyed()
    assert len(destroyed) == 10
    assert manager.count() == 0
    for entity_id in entities:
        assert not manager.exists(entity_id=entity_id)


def test_create_entity_with_explicit_entity_id() -> None:
    """Test creating entity with explicit entity_id uses that ID."""
    manager = EntityManager()
    explicit_id = EntityID(fake.uuid4())
    result = manager.create(entity_id=explicit_id)
    assert result == explicit_id
    assert manager.exists(entity_id=explicit_id) is True


def test_create_entity_with_explicit_id_increments_counter() -> None:
    """Test creation counter increments even with explicit ID."""
    manager = EntityManager()
    explicit_id = EntityID(fake.uuid4())
    manager.create(entity_id=explicit_id)
    auto_id = manager.create()
    assert auto_id != explicit_id
    assert manager.count() == 2


def test_create_entity_with_explicit_id_and_name() -> None:
    """Test creating entity with both explicit ID and name."""
    manager = EntityManager()
    explicit_id = EntityID(fake.uuid4())
    name = fake.word()
    result = manager.create(name=name, entity_id=explicit_id)
    assert result == explicit_id
    assert manager.get_name(entity_id=explicit_id) == name


def test_create_entity_without_explicit_id_generates_id() -> None:
    """Test creating entity without explicit ID generates one."""
    manager = EntityManager()
    result = manager.create(entity_id=None)
    assert isinstance(result, str)
    assert len(result) > 0
    assert manager.exists(entity_id=result) is True


def test_derive_id_is_deterministic_per_seed_and_name() -> None:
    """Same seed and name always derive the same ID."""
    seed = fake.random_int(min=1, max=999999)
    name = fake.word()

    assert EntityManager(seed=seed).derive_id(name=name) == EntityManager(
        seed=seed
    ).derive_id(name=name)


def test_derive_id_is_independent_of_creation_order() -> None:
    """Derived IDs ignore the creation counter entirely."""
    manager = EntityManager(seed=42)
    name = fake.word()

    before_creations = manager.derive_id(name=name)
    manager.create()
    manager.create()

    assert manager.derive_id(name=name) == before_creations
    assert manager.exists(entity_id=before_creations) is False


def test_derive_id_differs_by_seed_and_name() -> None:
    """Different seeds or names derive different IDs."""
    name = fake.word()

    assert EntityManager(seed=1).derive_id(name=name) != EntityManager(
        seed=2
    ).derive_id(name=name)
    assert EntityManager(seed=1).derive_id(name="a") != EntityManager(seed=1).derive_id(
        name="b"
    )


def test_derived_id_never_collides_with_counter_ids() -> None:
    """Counter-generated IDs and derived IDs live in distinct name spaces."""
    manager = EntityManager(seed=7)
    counter_ids = {manager.create() for _ in range(50)}
    derived_ids = {manager.derive_id(name=str(index)) for index in range(50)}

    assert counter_ids.isdisjoint(derived_ids)


def test_create_with_duplicate_explicit_id_raises() -> None:
    """Re-creating a live entity ID fails loudly instead of merging."""
    manager = EntityManager()
    entity_id = EntityID(fake.uuid4())
    manager.create(entity_id=entity_id)

    with pytest.raises(StateError, match="already exists"):
        manager.create(entity_id=entity_id)

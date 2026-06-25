"""Tests for Archetype implementation."""

from dataclasses import dataclass

import pytest
from faker import Faker

from yuna.ecs.archetype import Archetype
from yuna.ecs.component import Component
from yuna.exceptions import StateError, ValidationError
from yuna.types.identifiers import EntityID

fake = Faker()


@dataclass
class Position(Component):
    """Test position component."""

    x: float
    y: float


@dataclass
class Velocity(Component):
    """Test velocity component."""

    x: float
    y: float


@dataclass
class Health(Component):
    """Test health component."""

    current: float
    maximum: float


def test_archetype_initialization() -> None:
    """Test Archetype can be initialized with component types."""
    component_types = frozenset({Position, Velocity})
    archetype = Archetype(component_types=component_types)

    assert archetype.component_types == component_types
    assert archetype.entity_count == 0


def test_add_entity_to_archetype() -> None:
    """Test adding entity to archetype."""
    archetype = Archetype(component_types=frozenset({Position, Velocity}))
    entity_id = EntityID(fake.uuid4())

    archetype.add_entity(
        entity_id=entity_id,
        components={
            Position: Position(x=10.0, y=20.0),
            Velocity: Velocity(x=1.0, y=2.0),
        },
    )

    assert archetype.entity_count == 1
    assert archetype.has_entity(entity_id=entity_id)


def test_add_entity_with_mismatched_components_raises_error() -> None:
    """Test adding entity with wrong components raises ValueError."""
    archetype = Archetype(component_types=frozenset({Position, Velocity}))
    entity_id = EntityID(fake.uuid4())

    with pytest.raises(ValidationError, match="don't match archetype signature"):
        archetype.add_entity(
            entity_id=entity_id,
            components={Position: Position(x=10.0, y=20.0)},
        )


def test_add_duplicate_entity_raises_error() -> None:
    """Test adding same entity twice raises ValueError."""
    archetype = Archetype(component_types=frozenset({Position}))
    entity_id = EntityID(fake.uuid4())

    archetype.add_entity(
        entity_id=entity_id,
        components={Position: Position(x=10.0, y=20.0)},
    )

    with pytest.raises(StateError, match="already in archetype"):
        archetype.add_entity(
            entity_id=entity_id,
            components={Position: Position(x=5.0, y=5.0)},
        )


def test_remove_entity_from_archetype() -> None:
    """Test removing entity from archetype."""
    archetype = Archetype(component_types=frozenset({Position}))
    entity_id = EntityID(fake.uuid4())

    archetype.add_entity(
        entity_id=entity_id,
        components={Position: Position(x=10.0, y=20.0)},
    )

    removed = archetype.remove_entity(entity_id=entity_id)

    assert archetype.entity_count == 0
    assert not archetype.has_entity(entity_id=entity_id)
    assert Position in removed
    assert isinstance(removed[Position], Position)


def test_remove_nonexistent_entity_raises_error() -> None:
    """Test removing entity not in archetype raises ValueError."""
    archetype = Archetype(component_types=frozenset({Position}))
    entity_id = EntityID(fake.uuid4())

    with pytest.raises(ValidationError, match="Entity.*not in archetype"):
        archetype.remove_entity(entity_id=entity_id)


def test_remove_entity_maintains_data_locality() -> None:
    """Test swap-and-pop preserves component order for remaining entities."""
    archetype = Archetype(component_types=frozenset({Position}))
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    archetype.add_entity(
        entity_id=entity1, components={Position: Position(x=1.0, y=1.0)}
    )
    archetype.add_entity(
        entity_id=entity2, components={Position: Position(x=2.0, y=2.0)}
    )
    archetype.add_entity(
        entity_id=entity3, components={Position: Position(x=3.0, y=3.0)}
    )

    archetype.remove_entity(entity_id=entity2)

    assert archetype.entity_count == 2
    assert archetype.has_entity(entity_id=entity1)
    assert archetype.has_entity(entity_id=entity3)
    assert not archetype.has_entity(entity_id=entity2)


def test_get_component_from_archetype() -> None:
    """Test getting component from entity in archetype."""
    archetype = Archetype(component_types=frozenset({Position, Velocity}))
    entity_id = EntityID(fake.uuid4())

    position = Position(x=10.0, y=20.0)
    velocity = Velocity(x=1.0, y=2.0)

    archetype.add_entity(
        entity_id=entity_id,
        components={Position: position, Velocity: velocity},
    )

    retrieved_position = archetype.get_component(
        entity_id=entity_id, component_type=Position
    )
    assert retrieved_position is position
    assert isinstance(retrieved_position, Position)
    assert retrieved_position.x == 10.0


def test_get_component_not_in_archetype_returns_none() -> None:
    """Test getting component not in archetype signature returns None."""
    archetype = Archetype(component_types=frozenset({Position}))
    entity_id = EntityID(fake.uuid4())

    archetype.add_entity(
        entity_id=entity_id,
        components={Position: Position(x=10.0, y=20.0)},
    )

    health = archetype.get_component(entity_id=entity_id, component_type=Health)
    assert health is None


def test_get_component_from_nonexistent_entity_returns_none() -> None:
    """Test getting component from entity not in archetype returns None."""
    archetype = Archetype(component_types=frozenset({Position}))
    entity_id = EntityID(fake.uuid4())

    position = archetype.get_component(entity_id=entity_id, component_type=Position)
    assert position is None


def test_has_entity() -> None:
    """Test checking if entity is in archetype."""
    archetype = Archetype(component_types=frozenset({Position}))
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    archetype.add_entity(
        entity_id=entity1,
        components={Position: Position(x=10.0, y=20.0)},
    )

    assert archetype.has_entity(entity_id=entity1)
    assert not archetype.has_entity(entity_id=entity2)


def test_get_components_column() -> None:
    """Test getting column of components for iteration."""
    archetype = Archetype(component_types=frozenset({Position}))
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    archetype.add_entity(
        entity_id=entity1,
        components={Position: Position(x=1.0, y=1.0)},
    )
    archetype.add_entity(
        entity_id=entity2,
        components={Position: Position(x=2.0, y=2.0)},
    )

    positions = archetype.get_components_column(component_type=Position)
    assert len(positions) == 2
    assert all(isinstance(pos, Position) for pos in positions)


def test_get_components_column_not_in_signature_raises_error() -> None:
    """Test getting column for component not in archetype raises ValueError."""
    archetype = Archetype(component_types=frozenset({Position}))

    with pytest.raises(ValidationError, match="not in archetype signature"):
        archetype.get_components_column(component_type=Health)


def test_iter_components() -> None:
    """Test iterating over entities with selected components."""
    archetype = Archetype(component_types=frozenset({Position, Velocity}))
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    archetype.add_entity(
        entity_id=entity1,
        components={
            Position: Position(x=1.0, y=1.0),
            Velocity: Velocity(x=0.5, y=0.5),
        },
    )
    archetype.add_entity(
        entity_id=entity2,
        components={
            Position: Position(x=2.0, y=2.0),
            Velocity: Velocity(x=1.0, y=1.0),
        },
    )

    results = archetype.iter_components(component_types=[Position, Velocity])
    assert len(results) == 2

    for _entity_id, (pos, vel) in results:
        assert isinstance(pos, Position)
        assert isinstance(vel, Velocity)


def test_iter_components_subset() -> None:
    """Test iterating with subset of archetype components."""
    archetype = Archetype(component_types=frozenset({Position, Velocity, Health}))
    entity_id = EntityID(fake.uuid4())

    archetype.add_entity(
        entity_id=entity_id,
        components={
            Position: Position(x=1.0, y=1.0),
            Velocity: Velocity(x=0.5, y=0.5),
            Health: Health(current=100.0, maximum=100.0),
        },
    )

    results = archetype.iter_components(component_types=[Position, Health])
    assert len(results) == 1

    entity_id_result, (pos, health) = results[0]
    assert entity_id_result == entity_id
    assert isinstance(pos, Position)
    assert isinstance(health, Health)


def test_iter_components_not_in_signature_raises_error() -> None:
    """Test iterating with component not in archetype raises ValueError."""
    archetype = Archetype(component_types=frozenset({Position}))
    entity_id = EntityID(fake.uuid4())

    archetype.add_entity(
        entity_id=entity_id,
        components={Position: Position(x=1.0, y=1.0)},
    )

    with pytest.raises(ValidationError, match="not in archetype signature"):
        archetype.iter_components(component_types=[Position, Health])


def test_entities_property_returns_copy() -> None:
    """Test entities property returns copy not reference."""
    archetype = Archetype(component_types=frozenset({Position}))
    entity_id = EntityID(fake.uuid4())

    archetype.add_entity(
        entity_id=entity_id,
        components={Position: Position(x=1.0, y=1.0)},
    )

    entities1 = archetype.entities
    entities2 = archetype.entities

    assert entities1 is not entities2
    assert entities1 == entities2


def test_get_components_column_returns_copy() -> None:
    """Test get_components_column returns copy not reference."""
    archetype = Archetype(component_types=frozenset({Position}))
    entity_id = EntityID(fake.uuid4())

    archetype.add_entity(
        entity_id=entity_id,
        components={Position: Position(x=1.0, y=1.0)},
    )

    column1 = archetype.get_components_column(component_type=Position)
    column2 = archetype.get_components_column(component_type=Position)

    assert column1 is not column2
    assert column1 == column2


def test_archetype_with_no_components() -> None:
    """Test archetype with empty component signature."""
    archetype = Archetype(component_types=frozenset())

    assert archetype.component_types == frozenset()
    assert archetype.entity_count == 0


def test_multiple_entities_cache_locality() -> None:
    """Test archetype maintains cache-friendly component layout."""
    archetype = Archetype(component_types=frozenset({Position, Velocity}))

    entities = [EntityID(fake.uuid4()) for _ in range(10)]
    for i, entity_id in enumerate(entities):
        archetype.add_entity(
            entity_id=entity_id,
            components={
                Position: Position(x=float(i), y=float(i)),
                Velocity: Velocity(x=float(i) * 0.5, y=float(i) * 0.5),
            },
        )

    positions = archetype.get_components_column(component_type=Position)
    velocities = archetype.get_components_column(component_type=Velocity)

    assert len(positions) == 10
    assert len(velocities) == 10

    for i, pos in enumerate(positions):
        assert isinstance(pos, Position)
        assert pos.x == float(i)
        assert pos.y == float(i)

"""Tests for priority calculation."""

from typing import Any

import pytest
from faker import Faker

from yuna.network.priority import (
    EntityPriority,
    PriorityCalculator,
    PriorityWeights,
)
from yuna.types.identifiers import EntityID

fake = Faker()


def test_priority_weights_defaults() -> None:
    """Test PriorityWeights has correct defaults."""
    weights = PriorityWeights()
    assert weights.distance == 1.0
    assert weights.movement == 0.5
    assert weights.importance == 2.0


def test_priority_weights_custom() -> None:
    """Test PriorityWeights with custom values."""
    weights = PriorityWeights(distance=2.0, movement=1.0, importance=3.0)
    assert weights.distance == 2.0
    assert weights.movement == 1.0
    assert weights.importance == 3.0


def test_entity_priority_dataclass() -> None:
    """Test EntityPriority dataclass."""
    entity_id = EntityID(fake.uuid4())
    priority = fake.pyfloat(min_value=0.0, max_value=1.0)
    entity_priority = EntityPriority(entity_id=entity_id, priority=priority)
    assert entity_priority.entity_id == entity_id
    assert entity_priority.priority == priority


def test_calculator_init_defaults() -> None:
    """Test PriorityCalculator initializes with defaults."""
    calculator = PriorityCalculator()
    assert calculator.weights.distance == 1.0
    assert calculator.decay_rate == 0.95
    assert calculator.max_distance == 100.0


def test_calculator_init_custom() -> None:
    """Test PriorityCalculator with custom values."""
    weights = PriorityWeights(distance=2.0, movement=1.0, importance=3.0)
    calculator = PriorityCalculator(
        weights=weights,
        decay_rate=0.9,
        max_distance=200.0,
    )
    assert calculator.weights == weights
    assert calculator.decay_rate == 0.9
    assert calculator.max_distance == 200.0


def test_calculate_distance_priority_close_entity() -> None:
    """Test distance priority for close entity (high priority)."""
    calculator = PriorityCalculator(max_distance=100.0)
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())

    entities = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity_id: {"Position": {"x": 10.0, "y": 0.0}},
    }

    priority = calculator._calculate_distance_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    assert priority == 0.9


def test_calculate_distance_priority_far_entity() -> None:
    """Test distance priority for far entity (low priority)."""
    calculator = PriorityCalculator(max_distance=100.0)
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())

    entities = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity_id: {"Position": {"x": 90.0, "y": 0.0}},
    }

    priority = calculator._calculate_distance_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    assert priority == pytest.approx(0.1)


def test_calculate_distance_priority_max_distance() -> None:
    """Test distance priority at max distance (zero priority)."""
    calculator = PriorityCalculator(max_distance=100.0)
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())

    entities = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity_id: {"Position": {"x": 100.0, "y": 0.0}},
    }

    priority = calculator._calculate_distance_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    assert priority == 0.0


def test_calculate_distance_priority_beyond_max_distance() -> None:
    """Test distance priority beyond max distance (clamped to zero)."""
    calculator = PriorityCalculator(max_distance=100.0)
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())

    entities = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity_id: {"Position": {"x": 200.0, "y": 0.0}},
    }

    priority = calculator._calculate_distance_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    assert priority == 0.0


def test_calculate_distance_priority_missing_position() -> None:
    """Test distance priority with missing Position component."""
    calculator = PriorityCalculator()
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())

    entities = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity_id: {},
    }

    priority = calculator._calculate_distance_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    assert priority == 0.0


def test_calculate_movement_priority_static() -> None:
    """Test movement priority for static entity (zero priority)."""
    entity_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Velocity": {"x": 0.0, "y": 0.0}},
    }

    priority = PriorityCalculator._calculate_movement_priority(
        entity_id=entity_id,
        entities=entities,
    )

    assert priority == 0.0


def test_calculate_movement_priority_slow() -> None:
    """Test movement priority for slow entity."""
    entity_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Velocity": {"x": 3.0, "y": 4.0}},
    }

    priority = PriorityCalculator._calculate_movement_priority(
        entity_id=entity_id,
        entities=entities,
    )

    assert priority == 0.5


def test_calculate_movement_priority_fast() -> None:
    """Test movement priority for fast entity."""
    entity_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Velocity": {"x": 6.0, "y": 8.0}},
    }

    priority = PriorityCalculator._calculate_movement_priority(
        entity_id=entity_id,
        entities=entities,
    )

    assert priority == 1.0


def test_calculate_movement_priority_max_speed() -> None:
    """Test movement priority clamped at max speed."""
    entity_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Velocity": {"x": 20.0, "y": 0.0}},
    }

    priority = PriorityCalculator._calculate_movement_priority(
        entity_id=entity_id,
        entities=entities,
    )

    assert priority == 1.0


def test_calculate_movement_priority_missing_velocity() -> None:
    """Test movement priority with missing Velocity component."""
    entity_id = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id: {},
    }

    priority = PriorityCalculator._calculate_movement_priority(
        entity_id=entity_id,
        entities=entities,
    )

    assert priority == 0.0


def test_calculate_importance_priority_critical() -> None:
    """Test importance priority for critical entity."""
    entity_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Importance": {"tag": "critical"}},
    }

    priority = PriorityCalculator._calculate_importance_priority(
        entity_id=entity_id,
        entities=entities,
    )

    assert priority == 1.0


def test_calculate_importance_priority_high() -> None:
    """Test importance priority for high importance entity."""
    entity_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Importance": {"tag": "high"}},
    }

    priority = PriorityCalculator._calculate_importance_priority(
        entity_id=entity_id,
        entities=entities,
    )

    assert priority == 0.75


def test_calculate_importance_priority_normal() -> None:
    """Test importance priority for normal entity."""
    entity_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Importance": {"tag": "normal"}},
    }

    priority = PriorityCalculator._calculate_importance_priority(
        entity_id=entity_id,
        entities=entities,
    )

    assert priority == 0.5


def test_calculate_importance_priority_low() -> None:
    """Test importance priority for low importance entity."""
    entity_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Importance": {"tag": "low"}},
    }

    priority = PriorityCalculator._calculate_importance_priority(
        entity_id=entity_id,
        entities=entities,
    )

    assert priority == 0.25


def test_calculate_importance_priority_unknown_tag() -> None:
    """Test importance priority for unknown tag."""
    entity_id = EntityID(fake.uuid4())
    entities = {
        entity_id: {"Importance": {"tag": "unknown"}},
    }

    priority = PriorityCalculator._calculate_importance_priority(
        entity_id=entity_id,
        entities=entities,
    )

    assert priority == 0.0


def test_calculate_importance_priority_missing_component() -> None:
    """Test importance priority with missing Importance component."""
    entity_id = EntityID(fake.uuid4())
    entities: dict[EntityID, dict[str, Any]] = {
        entity_id: {},
    }

    priority = PriorityCalculator._calculate_importance_priority(
        entity_id=entity_id,
        entities=entities,
    )

    assert priority == 0.0


def test_calculate_priority_combines_factors() -> None:
    """Test calculate_priority combines all factors."""
    calculator = PriorityCalculator(
        weights=PriorityWeights(distance=1.0, movement=1.0, importance=1.0),
        max_distance=100.0,
    )
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())

    entities: dict[EntityID, dict[str, Any]] = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity_id: {
            "Position": {"x": 10.0, "y": 0.0},
            "Velocity": {"x": 5.0, "y": 0.0},
            "Importance": {"tag": "high"},
        },
    }

    priority = calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    expected = 0.9 * 1.0 + 0.5 * 1.0 + 0.75 * 1.0
    assert priority == expected


def test_calculate_priority_applies_weights() -> None:
    """Test calculate_priority applies custom weights."""
    calculator = PriorityCalculator(
        weights=PriorityWeights(distance=2.0, movement=1.0, importance=3.0),
        max_distance=100.0,
    )
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())

    entities: dict[EntityID, dict[str, Any]] = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity_id: {
            "Position": {"x": 50.0, "y": 0.0},
            "Velocity": {"x": 5.0, "y": 0.0},
            "Importance": {"tag": "critical"},
        },
    }

    priority = calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    expected = 0.5 * 2.0 + 0.5 * 1.0 + 1.0 * 3.0
    assert priority == expected


def test_calculate_priority_static_decay() -> None:
    """Test calculate_priority applies decay for static entities."""
    calculator = PriorityCalculator(decay_rate=0.9)
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())

    entities = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity_id: {"Position": {"x": 10.0, "y": 0.0}},
    }

    first_priority = calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    second_priority = calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    assert second_priority < first_priority
    assert second_priority == first_priority * 0.9


def test_calculate_priority_no_decay_for_moving() -> None:
    """Test calculate_priority does not apply decay for moving entities."""
    calculator = PriorityCalculator(decay_rate=0.9)
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())

    entities = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity_id: {
            "Position": {"x": 10.0, "y": 0.0},
            "Velocity": {"x": 5.0, "y": 0.0},
        },
    }

    first_priority = calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    second_priority = calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    assert second_priority == first_priority


def test_calculate_priority_missing_entity() -> None:
    """Test calculate_priority with missing entity."""
    calculator = PriorityCalculator()
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())

    entities: dict[EntityID, dict[str, Any]] = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
    }

    priority = calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    assert priority == 0.0


def test_calculate_priority_missing_observer() -> None:
    """Test calculate_priority with missing observer."""
    calculator = PriorityCalculator()
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())

    entities: dict[EntityID, dict[str, Any]] = {
        entity_id: {"Position": {"x": 10.0, "y": 0.0}},
    }

    priority = calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    assert priority == 0.0


def test_calculate_priorities_sorts_by_priority() -> None:
    """Test calculate_priorities returns sorted list."""
    calculator = PriorityCalculator(max_distance=100.0)
    observer_id = EntityID(fake.uuid4())
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    entities = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity1: {"Position": {"x": 90.0, "y": 0.0}},
        entity2: {"Position": {"x": 10.0, "y": 0.0}},
        entity3: {"Position": {"x": 50.0, "y": 0.0}},
    }

    priorities = calculator.calculate_priorities(
        observer_id=observer_id,
        entity_ids={entity1, entity2, entity3},
        entities=entities,
    )

    assert len(priorities) == 3
    assert priorities[0].entity_id == entity2
    assert priorities[1].entity_id == entity3
    assert priorities[2].entity_id == entity1
    assert priorities[0].priority > priorities[1].priority > priorities[2].priority


def test_calculate_priorities_empty_set() -> None:
    """Test calculate_priorities with empty entity set."""
    calculator = PriorityCalculator()
    observer_id = EntityID(fake.uuid4())

    entities = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
    }

    priorities = calculator.calculate_priorities(
        observer_id=observer_id,
        entity_ids=set(),
        entities=entities,
    )

    assert len(priorities) == 0


def test_reset_decay() -> None:
    """Test reset_decay clears decay for entity."""
    calculator = PriorityCalculator(decay_rate=0.5)
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())

    entities = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity_id: {"Position": {"x": 10.0, "y": 0.0}},
    }

    first_priority = calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )
    second_priority = calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    assert second_priority < first_priority

    calculator.reset_decay(entity_id=entity_id)
    third_priority = calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    assert third_priority == first_priority


def test_clear_decay() -> None:
    """Test clear_decay removes all decay tracking."""
    calculator = PriorityCalculator(decay_rate=0.5)
    observer_id = EntityID(fake.uuid4())
    entity_id = EntityID(fake.uuid4())

    entities = {
        observer_id: {"Position": {"x": 0.0, "y": 0.0}},
        entity_id: {"Position": {"x": 10.0, "y": 0.0}},
    }

    calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )
    calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    calculator.clear_decay()

    first_priority_after_clear = calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )
    second_priority_after_clear = calculator.calculate_priority(
        entity_id=entity_id,
        observer_id=observer_id,
        entities=entities,
    )

    assert second_priority_after_clear < first_priority_after_clear

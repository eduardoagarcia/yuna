"""Tests for modifier."""

from dataclasses import FrozenInstanceError

from faker import Faker

from yuna.modifiers.modifier import Modifier
from yuna.modifiers.types import (
    ModificationType,
    ModifierPriority,
)
from yuna.types.identifiers import EntityID

fake = Faker()


def test_modifier_creation() -> None:
    """Test Modifier can be instantiated."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.random.random(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier is not None


def test_modifier_has_entity_id() -> None:
    """Test modifier has entity_id."""
    entity_id = EntityID(fake.uuid4())
    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.entity_id == entity_id


def test_modifier_has_stat() -> None:
    """Test modifier has stat name."""
    stat = fake.word()
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.stat == stat


def test_modifier_has_modification_type() -> None:
    """Test modifier has modification type."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.PERCENTAGE,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.modification_type == ModificationType.PERCENTAGE


def test_modifier_has_value() -> None:
    """Test modifier has value."""
    value = fake.random.random()
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=value,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.value == value


def test_modifier_has_priority() -> None:
    """Test modifier has priority."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.HIGH,
        source=fake.word(),
    )
    assert modifier.priority == ModifierPriority.HIGH


def test_modifier_has_source() -> None:
    """Test modifier has source."""
    source = fake.word()
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=source,
    )
    assert modifier.source == source


def test_modifier_is_immutable() -> None:
    """Test modifier cannot be modified after creation."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    try:
        modifier.value = 999.0  # type: ignore[misc]
        msg = "Expected FrozenInstanceError"
        raise AssertionError(msg)
    except FrozenInstanceError:
        pass


def test_modifier_with_set_type() -> None:
    """Test modifier with SET modification type."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.SET,
        value=100.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.modification_type == ModificationType.SET


def test_modifier_with_flat_type() -> None:
    """Test modifier with FLAT modification type."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.modification_type == ModificationType.FLAT


def test_modifier_with_percentage_type() -> None:
    """Test modifier with PERCENTAGE modification type."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.PERCENTAGE,
        value=0.5,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.modification_type == ModificationType.PERCENTAGE


def test_modifier_with_multiplier_type() -> None:
    """Test modifier with MULTIPLIER modification type."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.MULTIPLIER,
        value=2.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.modification_type == ModificationType.MULTIPLIER


def test_modifier_with_critical_priority() -> None:
    """Test modifier with CRITICAL priority."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.CRITICAL,
        source=fake.word(),
    )
    assert modifier.priority == ModifierPriority.CRITICAL


def test_modifier_with_high_priority() -> None:
    """Test modifier with HIGH priority."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.HIGH,
        source=fake.word(),
    )
    assert modifier.priority == ModifierPriority.HIGH


def test_modifier_with_normal_priority() -> None:
    """Test modifier with NORMAL priority."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.priority == ModifierPriority.NORMAL


def test_modifier_with_low_priority() -> None:
    """Test modifier with LOW priority."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.LOW,
        source=fake.word(),
    )
    assert modifier.priority == ModifierPriority.LOW


def test_modifier_with_zero_value() -> None:
    """Test modifier with zero value."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=0.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.value == 0.0


def test_modifier_with_negative_value() -> None:
    """Test modifier with negative value."""
    value = -fake.random.random()
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=value,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.value == value


def test_modifier_equality() -> None:
    """Test two modifiers with same values are equal."""
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()
    source = fake.word()
    modifier_1 = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=source,
    )
    modifier_2 = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=source,
    )
    assert modifier_1 == modifier_2


def test_modifier_inequality() -> None:
    """Test two modifiers with different values are not equal."""
    modifier_1 = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    modifier_2 = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier_1 != modifier_2


def test_modifier_priority_values() -> None:
    """Test priority enum values are correct."""
    assert ModifierPriority.CRITICAL.value == 0
    assert ModifierPriority.HIGH.value == 100
    assert ModifierPriority.NORMAL.value == 200
    assert ModifierPriority.LOW.value == 300


def test_modification_type_has_all_types() -> None:
    """Test all modification types are defined."""
    types = {mt.name for mt in ModificationType}
    assert "SET" in types
    assert "FLAT" in types
    assert "PERCENTAGE" in types
    assert "MULTIPLIER" in types


def test_modifier_priority_has_all_priorities() -> None:
    """Test all priorities are defined."""
    priorities = {p.name for p in ModifierPriority}
    assert "CRITICAL" in priorities
    assert "HIGH" in priorities
    assert "NORMAL" in priorities
    assert "LOW" in priorities


def test_modifier_with_empty_stat_name() -> None:
    """Test modifier with empty stat name."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat="",
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert not modifier.stat


def test_modifier_with_empty_source() -> None:
    """Test modifier with empty source."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source="",
    )
    assert not modifier.source


def test_modifier_with_tags() -> None:
    """Test modifier with tags."""
    tags = frozenset({fake.word(), fake.word()})
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        tags=tags,
    )
    assert modifier.tags == tags


def test_modifier_with_empty_tags() -> None:
    """Test modifier defaults to empty frozenset for tags."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.tags == frozenset()


def test_modifier_with_single_category() -> None:
    """Test modifier with single category."""
    category = fake.word()
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(category,),
    )
    assert modifier.categories == (category,)


def test_modifier_with_multiple_categories() -> None:
    """Test modifier with multiple categories."""
    category1 = fake.word()
    category2 = fake.word()
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(category1, category2),
    )
    assert modifier.categories == (category1, category2)


def test_modifier_without_categories() -> None:
    """Test modifier defaults to empty tuple for categories."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.categories == ()


def test_modifier_with_display_group() -> None:
    """Test modifier with display_group."""
    display_group = fake.word()
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        display_group=display_group,
    )
    assert modifier.display_group == display_group


def test_modifier_without_display_group() -> None:
    """Test modifier defaults to None for display_group."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.display_group is None


def test_modifier_with_metadata() -> None:
    """Test modifier with metadata."""
    metadata = {fake.word(): fake.word(), fake.word(): fake.random_int()}
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        metadata=metadata,
    )
    assert modifier.metadata == metadata


def test_modifier_without_metadata() -> None:
    """Test modifier defaults to empty dict for metadata."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    assert modifier.metadata == {}


def test_modifier_with_all_semantic_fields() -> None:
    """Test modifier with all semantic metadata fields."""
    tags = frozenset({fake.word(), fake.word()})
    categories = (fake.word(), fake.word())
    display_group = fake.word()
    metadata = {fake.word(): fake.word()}

    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        tags=tags,
        categories=categories,
        display_group=display_group,
        metadata=metadata,
    )

    assert modifier.tags == tags
    assert modifier.categories == categories
    assert modifier.display_group == display_group
    assert modifier.metadata == metadata

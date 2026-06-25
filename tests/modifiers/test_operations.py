"""Tests for modifier operations."""

from faker import Faker

from yuna.modifiers.config import ModifierConfig
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.operations import ModifierOperations
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.modifiers.types import (
    ModificationType,
    ModifierPriority,
)
from yuna.types.identifiers import EntityID

fake = Faker()


def test_operations_creation() -> None:
    """Test ModifierOperations can be instantiated."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    assert operations is not None


def test_remove_by_tag() -> None:
    """Test removing modifiers by tag."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    entity_id = EntityID(fake.uuid4())

    modifier_with_tag = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"temporary"}),
    )

    modifier_without_tag = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
    )

    pipeline.tracker.track_modifier(modifier=modifier_with_tag, current_tick=0)
    pipeline.tracker.track_modifier(modifier=modifier_without_tag, current_tick=0)

    removed_count = operations.remove_by_tag(entity_id=entity_id, tag="temporary")

    assert removed_count == 1
    assert pipeline.tracker.get_tracked_count() == 1


def test_remove_by_tag_no_match() -> None:
    """Test remove_by_tag when no modifiers match."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    entity_id = EntityID(fake.uuid4())

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
    )

    pipeline.tracker.track_modifier(modifier=modifier, current_tick=0)

    removed_count = operations.remove_by_tag(entity_id=entity_id, tag="nonexistent")

    assert removed_count == 0
    assert pipeline.tracker.get_tracked_count() == 1


def test_remove_by_category() -> None:
    """Test removing modifiers by category."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    entity_id = EntityID(fake.uuid4())
    category = fake.word()

    modifier_in_category = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        categories=(category,),
    )

    modifier_no_category = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
    )

    pipeline.tracker.track_modifier(modifier=modifier_in_category, current_tick=0)
    pipeline.tracker.track_modifier(modifier=modifier_no_category, current_tick=0)

    removed_count = operations.remove_by_category(
        entity_id=entity_id, category=category
    )

    assert removed_count == 1
    assert pipeline.tracker.get_tracked_count() == 1


def test_remove_by_category_no_match() -> None:
    """Test remove_by_category when no modifiers match."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    entity_id = EntityID(fake.uuid4())

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
    )

    pipeline.tracker.track_modifier(modifier=modifier, current_tick=0)

    removed_count = operations.remove_by_category(
        entity_id=entity_id, category=fake.word()
    )

    assert removed_count == 0
    assert pipeline.tracker.get_tracked_count() == 1


def test_clear_entity_modifiers() -> None:
    """Test clearing all modifiers from entity."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    entity_id = EntityID(fake.uuid4())

    modifier_1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
    )

    modifier_2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
    )

    pipeline.tracker.track_modifier(modifier=modifier_1, current_tick=0)
    pipeline.tracker.track_modifier(modifier=modifier_2, current_tick=0)

    removed_count = operations.clear_entity_modifiers(entity_id=entity_id)

    assert removed_count == 2
    assert pipeline.tracker.get_tracked_count() == 0


def test_clear_entity_modifiers_with_preserve_tags() -> None:
    """Test clearing modifiers while preserving tagged ones."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    entity_id = EntityID(fake.uuid4())

    modifier_permanent = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"permanent"}),
    )

    modifier_temporary = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"temporary"}),
    )

    modifier_no_tags = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
    )

    pipeline.tracker.track_modifier(modifier=modifier_permanent, current_tick=0)
    pipeline.tracker.track_modifier(modifier=modifier_temporary, current_tick=0)
    pipeline.tracker.track_modifier(modifier=modifier_no_tags, current_tick=0)

    removed_count = operations.clear_entity_modifiers(
        entity_id=entity_id, preserve_tags=frozenset({"permanent"})
    )

    assert removed_count == 2
    assert pipeline.tracker.get_tracked_count() == 1

    remaining = pipeline.tracker.get_all_modifiers()
    assert remaining[0].modifier_id == modifier_permanent.modifier_id


def test_clear_entity_modifiers_empty() -> None:
    """Test clearing modifiers from entity with none."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    entity_id = EntityID(fake.uuid4())

    removed_count = operations.clear_entity_modifiers(entity_id=entity_id)

    assert removed_count == 0


def test_get_stat_total_by_category() -> None:
    """Test getting stat total by category."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()
    category = fake.word()

    modifier_1 = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        categories=(category,),
    )

    modifier_2 = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        categories=(category,),
    )

    modifier_different_category = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        categories=(fake.word(),),
    )

    pipeline.tracker.track_modifier(modifier=modifier_1, current_tick=0)
    pipeline.tracker.track_modifier(modifier=modifier_2, current_tick=0)
    pipeline.tracker.track_modifier(
        modifier=modifier_different_category, current_tick=0
    )

    total = operations.get_stat_total_by_category(
        entity_id=entity_id, stat=stat, category=category
    )

    assert total == 15.0


def test_get_stat_total_by_category_no_match() -> None:
    """Test get_stat_total_by_category with no matching modifiers."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    entity_id = EntityID(fake.uuid4())

    total = operations.get_stat_total_by_category(
        entity_id=entity_id, stat=fake.word(), category=fake.word()
    )

    assert total == 0.0


def test_has_modifier_with_tag_true() -> None:
    """Test has_modifier_with_tag returns True when tag exists."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    entity_id = EntityID(fake.uuid4())

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"buff"}),
    )

    pipeline.tracker.track_modifier(modifier=modifier, current_tick=0)

    has_tag = operations.has_modifier_with_tag(entity_id=entity_id, tag="buff")

    assert has_tag is True


def test_has_modifier_with_tag_false() -> None:
    """Test has_modifier_with_tag returns False when tag doesn't exist."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    entity_id = EntityID(fake.uuid4())

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
    )

    pipeline.tracker.track_modifier(modifier=modifier, current_tick=0)

    has_tag = operations.has_modifier_with_tag(entity_id=entity_id, tag="buff")

    assert has_tag is False


def test_has_modifier_with_tag_no_modifiers() -> None:
    """Test has_modifier_with_tag returns False when no modifiers."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    entity_id = EntityID(fake.uuid4())

    has_tag = operations.has_modifier_with_tag(entity_id=entity_id, tag="buff")

    assert has_tag is False


def test_operations_with_multiple_entities() -> None:
    """Test operations only affect specified entity."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    operations = ModifierOperations(pipeline=pipeline)
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())

    modifier_1 = Modifier(
        entity_id=entity_1,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"buff"}),
    )

    modifier_2 = Modifier(
        entity_id=entity_2,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"buff"}),
    )

    pipeline.tracker.track_modifier(modifier=modifier_1, current_tick=0)
    pipeline.tracker.track_modifier(modifier=modifier_2, current_tick=0)

    removed_count = operations.remove_by_tag(entity_id=entity_1, tag="buff")

    assert removed_count == 1
    assert pipeline.tracker.get_tracked_count() == 1

    remaining = pipeline.tracker.get_all_modifiers()
    assert remaining[0].entity_id == entity_2

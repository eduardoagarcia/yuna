"""Tests for modifier query."""

from faker import Faker

from yuna.modifiers.modifier import Modifier
from yuna.modifiers.query import ModifierQuery
from yuna.modifiers.tracker import ModifierTracker
from yuna.modifiers.types import (
    ModificationType,
    ModifierPriority,
)
from yuna.types.identifiers import EntityID

fake = Faker()


def test_query_creation() -> None:
    """Test ModifierQuery can be instantiated."""
    tracker = ModifierTracker()
    query = ModifierQuery(tracker=tracker)
    assert query is not None


def test_query_with_tag() -> None:
    """Test querying modifiers by tag."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    modifier_with_tag = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"buff"}),
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

    tracker.track_modifier(modifier=modifier_with_tag, current_tick=0)
    tracker.track_modifier(modifier=modifier_without_tag, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    results = query.with_tag(tag="buff").execute()

    assert len(results) == 1
    assert results[0].modifier_id == modifier_with_tag.modifier_id


def test_query_with_any_tag() -> None:
    """Test querying modifiers with any of multiple tags."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    modifier_1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"buff"}),
    )

    modifier_2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"debuff"}),
    )

    modifier_3 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"neutral"}),
    )

    tracker.track_modifier(modifier=modifier_1, current_tick=0)
    tracker.track_modifier(modifier=modifier_2, current_tick=0)
    tracker.track_modifier(modifier=modifier_3, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    results = query.with_any_tag("buff", "debuff").execute()

    assert len(results) == 2


def test_query_with_all_tags() -> None:
    """Test querying modifiers with all specified tags."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    modifier_both = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"buff", "temporary"}),
    )

    modifier_one = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"buff"}),
    )

    tracker.track_modifier(modifier=modifier_both, current_tick=0)
    tracker.track_modifier(modifier=modifier_one, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    results = query.with_all_tags("buff", "temporary").execute()

    assert len(results) == 1
    assert results[0].modifier_id == modifier_both.modifier_id


def test_query_without_tag() -> None:
    """Test querying modifiers without specific tag."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    modifier_with_tag = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"debuff"}),
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

    tracker.track_modifier(modifier=modifier_with_tag, current_tick=0)
    tracker.track_modifier(modifier=modifier_without_tag, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    results = query.without_tag(tag="debuff").execute()

    assert len(results) == 1
    assert results[0].modifier_id == modifier_without_tag.modifier_id


def test_query_in_category() -> None:
    """Test querying modifiers by category."""
    tracker = ModifierTracker()
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

    tracker.track_modifier(modifier=modifier_in_category, current_tick=0)
    tracker.track_modifier(modifier=modifier_no_category, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    results = query.in_category(category=category).execute()

    assert len(results) == 1
    assert results[0].modifier_id == modifier_in_category.modifier_id


def test_query_for_entity() -> None:
    """Test querying modifiers for specific entity."""
    tracker = ModifierTracker()
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
    )

    modifier_2 = Modifier(
        entity_id=entity_2,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
    )

    tracker.track_modifier(modifier=modifier_1, current_tick=0)
    tracker.track_modifier(modifier=modifier_2, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    results = query.for_entity(entity_id=entity_1).execute()

    assert len(results) == 1
    assert results[0].entity_id == entity_1


def test_query_affecting_stat() -> None:
    """Test querying modifiers affecting specific stat."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    stat_1 = fake.unique.word()
    stat_2 = fake.unique.word()

    modifier_1 = Modifier(
        entity_id=entity_id,
        stat=stat_1,
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
    )

    modifier_2 = Modifier(
        entity_id=entity_id,
        stat=stat_2,
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
    )

    tracker.track_modifier(modifier=modifier_1, current_tick=0)
    tracker.track_modifier(modifier=modifier_2, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    results = query.affecting_stat(stat=stat_1).execute()

    assert len(results) == 1
    assert results[0].stat == stat_1


def test_query_from_source() -> None:
    """Test querying modifiers from specific source."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    source_1 = fake.unique.word()
    source_2 = fake.unique.word()

    modifier_1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=source_1,
        modifier_id=fake.uuid4(),
    )

    modifier_2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=source_2,
        modifier_id=fake.uuid4(),
    )

    tracker.track_modifier(modifier=modifier_1, current_tick=0)
    tracker.track_modifier(modifier=modifier_2, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    results = query.from_source(source=source_1).execute()

    assert len(results) == 1
    assert results[0].source == source_1


def test_query_chaining() -> None:
    """Test chaining multiple query filters."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    modifier_match = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"buff"}),
    )

    modifier_no_match = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"buff"}),
    )

    tracker.track_modifier(modifier=modifier_match, current_tick=0)
    tracker.track_modifier(modifier=modifier_no_match, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    results = query.with_tag(tag="buff").affecting_stat(stat="health").execute()

    assert len(results) == 1
    assert results[0].modifier_id == modifier_match.modifier_id


def test_query_count() -> None:
    """Test counting matching modifiers."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    for _ in range(5):
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
        tracker.track_modifier(modifier=modifier, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    count = query.with_tag(tag="buff").count()

    assert count == 5


def test_query_first() -> None:
    """Test getting first matching modifier."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    modifier_1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({"buff"}),
    )

    tracker.track_modifier(modifier=modifier_1, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    result = query.with_tag(tag="buff").first()

    assert result is not None
    assert result.modifier_id == modifier_1.modifier_id


def test_query_first_returns_none_when_no_match() -> None:
    """Test first returns None when no modifiers match."""
    tracker = ModifierTracker()

    query = ModifierQuery(tracker=tracker)
    result = query.with_tag(tag="nonexistent").first()

    assert result is None


def test_query_empty_tracker() -> None:
    """Test querying empty tracker returns empty list."""
    tracker = ModifierTracker()

    query = ModifierQuery(tracker=tracker)
    results = query.with_tag(tag="any").execute()

    assert results == []


def test_query_in_category_with_multi_category_modifier() -> None:
    """Test in_category matches modifiers that belong to multiple categories."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    category_one = fake.unique.word()
    category_two = fake.unique.word()
    category_three = fake.unique.word()

    multi_category_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        categories=(category_one, category_two),
    )

    single_category_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        categories=(category_three,),
    )

    tracker.track_modifier(modifier=multi_category_modifier, current_tick=0)
    tracker.track_modifier(modifier=single_category_modifier, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    results = query.in_category(category=category_one).execute()

    assert len(results) == 1
    assert results[0].modifier_id == multi_category_modifier.modifier_id


def test_query_in_category_finds_all_matching_modifiers() -> None:
    """Test in_category finds all modifiers containing the category."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    category = fake.unique.word()
    other_category = fake.unique.word()

    modifier_one = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        categories=(category,),
    )

    modifier_two = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        categories=(category, other_category),
    )

    modifier_three = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        categories=(other_category,),
    )

    tracker.track_modifier(modifier=modifier_one, current_tick=0)
    tracker.track_modifier(modifier=modifier_two, current_tick=0)
    tracker.track_modifier(modifier=modifier_three, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    results = query.in_category(category=category).execute()

    assert len(results) == 2
    modifier_ids = {m.modifier_id for m in results}
    assert modifier_one.modifier_id in modifier_ids
    assert modifier_two.modifier_id in modifier_ids


def test_query_in_category_with_empty_categories() -> None:
    """Test in_category does not match modifiers with empty categories."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    category = fake.word()

    modifier_no_categories = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
    )

    tracker.track_modifier(modifier=modifier_no_categories, current_tick=0)

    query = ModifierQuery(tracker=tracker)
    results = query.in_category(category=category).execute()

    assert len(results) == 0

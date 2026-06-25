"""Tests for modifier tracker."""

from faker import Faker

from yuna.modifiers.modifier import Modifier
from yuna.modifiers.tracker import ModifierTracker
from yuna.modifiers.types import (
    ModificationType,
    ModifierPriority,
)
from yuna.types.identifiers import EntityID

fake = Faker()


def test_tracker_initialization() -> None:
    """Test ModifierTracker initializes empty."""
    tracker = ModifierTracker()

    assert tracker.get_tracked_count() == 0


def test_track_modifier_with_duration() -> None:
    """Test tracking modifier with duration."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()

    modifier = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
    )

    tracker.track_modifier(modifier=modifier, current_tick=100)

    assert tracker.get_tracked_count() == 1
    active = tracker.get_active_modifiers(entity_id=entity_id, stat=stat)
    assert len(active) == 1
    assert active[0] == modifier


def test_track_modifier_permanent() -> None:
    """Test tracking permanent modifier (no duration)."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()

    modifier = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=None,
    )

    tracker.track_modifier(modifier=modifier, current_tick=100)

    assert tracker.get_tracked_count() == 1


def test_track_multiple_modifiers_same_entity() -> None:
    """Test tracking multiple modifiers on same entity."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=75,
    )

    tracker.track_modifier(modifier=modifier1, current_tick=100)
    tracker.track_modifier(modifier=modifier2, current_tick=100)

    assert tracker.get_tracked_count() == 2
    active = tracker.get_active_modifiers(entity_id=entity_id, stat=stat)
    assert len(active) == 2


def test_track_modifiers_different_stats() -> None:
    """Test tracking modifiers for different stats."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    modifier1 = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat="speed",
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
    )

    tracker.track_modifier(modifier=modifier1, current_tick=100)
    tracker.track_modifier(modifier=modifier2, current_tick=100)

    assert tracker.get_tracked_count() == 2
    health_modifiers = tracker.get_active_modifiers(entity_id=entity_id, stat="health")
    speed_modifiers = tracker.get_active_modifiers(entity_id=entity_id, stat="speed")
    assert len(health_modifiers) == 1
    assert len(speed_modifiers) == 1


def test_clear_expired_removes_expired() -> None:
    """Test clear_expired removes expired modifiers."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()

    modifier = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
    )

    tracker.track_modifier(modifier=modifier, current_tick=100)
    assert tracker.get_tracked_count() == 1

    expired = tracker.clear_expired(current_tick=149)
    assert len(expired) == 0
    assert tracker.get_tracked_count() == 1

    expired = tracker.clear_expired(current_tick=150)
    assert len(expired) == 1
    assert expired[0] == modifier
    assert tracker.get_tracked_count() == 0


def test_clear_expired_keeps_permanent() -> None:
    """Test clear_expired keeps permanent modifiers."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()

    modifier = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=None,
    )

    tracker.track_modifier(modifier=modifier, current_tick=100)

    expired = tracker.clear_expired(current_tick=999999)
    assert len(expired) == 0
    assert tracker.get_tracked_count() == 1


def test_clear_expired_partial() -> None:
    """Test clear_expired removes only some modifiers."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
        modifier_id="mod1",
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=100,
        modifier_id="mod2",
    )

    tracker.track_modifier(modifier=modifier1, current_tick=100)
    tracker.track_modifier(modifier=modifier2, current_tick=100)

    expired = tracker.clear_expired(current_tick=150)
    assert len(expired) == 1
    assert expired[0] == modifier1
    assert tracker.get_tracked_count() == 1

    active = tracker.get_active_modifiers(entity_id=entity_id, stat=stat)
    assert len(active) == 1
    assert active[0] == modifier2


def test_update_calls_clear_expired() -> None:
    """Test update calls clear_expired."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()

    modifier = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
    )

    tracker.track_modifier(modifier=modifier, current_tick=100)

    expired = tracker.update(current_tick=150)
    assert len(expired) == 1
    assert tracker.get_tracked_count() == 0


def test_get_active_modifiers_empty() -> None:
    """Test get_active_modifiers returns empty for unknown entity/stat."""
    tracker = ModifierTracker()

    active = tracker.get_active_modifiers(
        entity_id=EntityID(fake.uuid4()), stat=fake.word()
    )
    assert len(active) == 0


def test_remove_modifier_by_id_string() -> None:
    """Test manually removing modifier by ID string."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()
    modifier_id = fake.uuid4()

    modifier = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
        modifier_id=modifier_id,
    )

    tracker.track_modifier(modifier=modifier, current_tick=100)
    assert tracker.get_tracked_count() == 1

    removed = tracker.remove_modifier(modifier=modifier_id)
    assert removed == modifier
    assert tracker.get_tracked_count() == 0


def test_remove_modifier_by_object() -> None:
    """Test manually removing modifier by object."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()

    modifier = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
        modifier_id=fake.uuid4(),
    )

    tracker.track_modifier(modifier=modifier, current_tick=100)
    assert tracker.get_tracked_count() == 1

    removed = tracker.remove_modifier(modifier=modifier)
    assert removed == modifier
    assert tracker.get_tracked_count() == 0


def test_remove_modifier_not_found() -> None:
    """Test remove_modifier returns None for unknown ID."""
    tracker = ModifierTracker()

    removed = tracker.remove_modifier(modifier=fake.uuid4())
    assert removed is None


def test_remove_modifier_object_without_id() -> None:
    """Test removing modifier object without ID returns None."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()

    modifier = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
        modifier_id=None,
    )

    tracker.track_modifier(modifier=modifier, current_tick=100)

    removed = tracker.remove_modifier(modifier=modifier)
    assert removed is None
    assert tracker.get_tracked_count() == 1


def test_max_stacks_enforced() -> None:
    """Test max_stacks limit enforced."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()
    source_id = EntityID(fake.uuid4())

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source="buff",
        source_id=source_id,
        duration_ticks=50,
        max_stacks=2,
        modifier_id="mod1",
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source="buff",
        source_id=source_id,
        duration_ticks=50,
        max_stacks=2,
        modifier_id="mod2",
    )

    modifier3 = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source="buff",
        source_id=source_id,
        duration_ticks=50,
        max_stacks=2,
        modifier_id="mod3",
    )

    tracker.track_modifier(modifier=modifier1, current_tick=100)
    tracker.track_modifier(modifier=modifier2, current_tick=105)
    assert tracker.get_tracked_count() == 2

    tracker.track_modifier(modifier=modifier3, current_tick=110)
    assert tracker.get_tracked_count() == 2

    active = tracker.get_active_modifiers(entity_id=entity_id, stat=stat)
    assert len(active) == 2
    assert modifier1 not in active
    assert modifier2 in active
    assert modifier3 in active


def test_max_stacks_different_sources() -> None:
    """Test max_stacks only applies to same source."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())
    stat = fake.word()
    source_id1 = EntityID(fake.uuid4())
    source_id2 = EntityID(fake.uuid4())

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source="buff",
        source_id=source_id1,
        duration_ticks=50,
        max_stacks=1,
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat=stat,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source="buff",
        source_id=source_id2,
        duration_ticks=50,
        max_stacks=1,
    )

    tracker.track_modifier(modifier=modifier1, current_tick=100)
    tracker.track_modifier(modifier=modifier2, current_tick=100)

    assert tracker.get_tracked_count() == 2


def test_clear_removes_all() -> None:
    """Test clear removes all tracked modifiers."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    modifier1 = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat="speed",
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
    )

    tracker.track_modifier(modifier=modifier1, current_tick=100)
    tracker.track_modifier(modifier=modifier2, current_tick=100)
    assert tracker.get_tracked_count() == 2

    tracker.clear()
    assert tracker.get_tracked_count() == 0


def test_get_all_modifiers() -> None:
    """Test getting all modifiers across all entities and stats."""
    tracker = ModifierTracker()
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())

    modifier_1 = Modifier(
        entity_id=entity_1,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
    )

    modifier_2 = Modifier(
        entity_id=entity_1,
        stat="speed",
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
    )

    modifier_3 = Modifier(
        entity_id=entity_2,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
    )

    tracker.track_modifier(modifier=modifier_1, current_tick=100)
    tracker.track_modifier(modifier=modifier_2, current_tick=100)
    tracker.track_modifier(modifier=modifier_3, current_tick=100)

    all_modifiers = tracker.get_all_modifiers()

    assert len(all_modifiers) == 3
    assert modifier_1 in all_modifiers
    assert modifier_2 in all_modifiers
    assert modifier_3 in all_modifiers


def test_get_all_modifiers_empty() -> None:
    """Test get_all_modifiers returns empty list for empty tracker."""
    tracker = ModifierTracker()

    all_modifiers = tracker.get_all_modifiers()

    assert all_modifiers == []


def test_get_all_modifiers_after_expiration() -> None:
    """Test get_all_modifiers excludes expired modifiers."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    modifier_1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
    )

    modifier_2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=100,
    )

    tracker.track_modifier(modifier=modifier_1, current_tick=100)
    tracker.track_modifier(modifier=modifier_2, current_tick=100)

    tracker.clear_expired(current_tick=150)

    all_modifiers = tracker.get_all_modifiers()

    assert len(all_modifiers) == 1
    assert modifier_1 not in all_modifiers
    assert modifier_2 in all_modifiers


def test_get_all_modifiers_after_removal() -> None:
    """Test get_all_modifiers excludes manually removed modifiers."""
    tracker = ModifierTracker()
    entity_id = EntityID(fake.uuid4())

    modifier_1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
        modifier_id=fake.uuid4(),
    )

    modifier_2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
        modifier_id=fake.uuid4(),
    )

    tracker.track_modifier(modifier=modifier_1, current_tick=100)
    tracker.track_modifier(modifier=modifier_2, current_tick=100)

    tracker.remove_modifier(modifier=modifier_1)

    all_modifiers = tracker.get_all_modifiers()

    assert len(all_modifiers) == 1
    assert modifier_1 not in all_modifiers
    assert modifier_2 in all_modifiers

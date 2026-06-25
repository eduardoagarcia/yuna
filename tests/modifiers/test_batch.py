"""Tests for BatchModifierProcessor."""

from unittest.mock import Mock, patch

from faker import Faker

from yuna.modifiers.batch import BatchModifierProcessor
from yuna.modifiers.config import ModifierConfig, StackingRule
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.types import (
    ModificationType,
    ModifierPriority,
)
from yuna.types.identifiers import EntityID

fake = Faker()


def test_batch_processor_initializes_with_config() -> None:
    """Test batch processor initializes with modifier config."""
    config = ModifierConfig()
    processor = BatchModifierProcessor(config=config)
    assert processor._pipeline._config == config


def test_batch_processor_initializes_with_profiling_disabled() -> None:
    """Test batch processor initializes with profiling disabled by default."""
    config = ModifierConfig()
    processor = BatchModifierProcessor(config=config)
    assert not processor._profiling_enabled
    assert processor._monitor is None


@patch("yuna.modifiers.batch.get_performance_monitor")
def test_batch_processor_initializes_with_profiling_enabled(
    mock_get_monitor: Mock,
) -> None:
    """Test batch processor initializes with profiling enabled."""
    mock_monitor = Mock()
    mock_get_monitor.return_value = mock_monitor
    config = ModifierConfig()
    processor = BatchModifierProcessor(config=config, profiling_enabled=True)
    assert processor._profiling_enabled
    assert processor._monitor == mock_monitor


def test_queue_modifier_adds_modifier_to_queue() -> None:
    """Test queue_modifier adds modifier to internal pipeline queue."""
    config = ModifierConfig()
    processor = BatchModifierProcessor(config=config)
    entity_id = EntityID(fake.uuid4())
    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    processor.queue_modifier(modifier=modifier)

    assert processor.get_queue_size() == 1


def test_queue_modifier_queues_multiple_modifiers() -> None:
    """Test queue_modifier queues multiple modifiers."""
    config = ModifierConfig()
    processor = BatchModifierProcessor(config=config)
    entity_id = EntityID(fake.uuid4())

    for _ in range(5):
        modifier = Modifier(
            entity_id=entity_id,
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        )
        processor.queue_modifier(modifier=modifier)

    assert processor.get_queue_size() == 5


def test_process_batch_processes_queued_modifiers() -> None:
    """Test process_batch processes all queued modifiers."""
    config = ModifierConfig()
    stat_name = fake.word()
    config.register_stat(
        name=stat_name,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    processor = BatchModifierProcessor(config=config)
    entity_id = EntityID(fake.uuid4())
    modifier = Modifier(
        entity_id=entity_id,
        stat=stat_name,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    processor.queue_modifier(modifier=modifier)
    results = processor.process_batch()

    assert (entity_id, stat_name) in results
    assert results[(entity_id, stat_name)] == 10.0


def test_process_batch_returns_empty_dict_when_no_modifiers() -> None:
    """Test process_batch returns empty dict when queue is empty."""
    config = ModifierConfig()
    processor = BatchModifierProcessor(config=config)

    results = processor.process_batch()

    assert results == {}


def test_process_batch_processes_modifiers_for_multiple_entities() -> None:
    """Test process_batch processes modifiers for multiple entities in batch."""
    config = ModifierConfig()
    stat_name = fake.word()
    config.register_stat(
        name=stat_name,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    processor = BatchModifierProcessor(config=config)
    entity1_id = EntityID(fake.uuid4())
    entity2_id = EntityID(fake.uuid4())

    modifier1 = Modifier(
        entity_id=entity1_id,
        stat=stat_name,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    modifier2 = Modifier(
        entity_id=entity2_id,
        stat=stat_name,
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    processor.queue_modifier(modifier=modifier1)
    processor.queue_modifier(modifier=modifier2)
    results = processor.process_batch()

    assert results[(entity1_id, stat_name)] == 10.0
    assert results[(entity2_id, stat_name)] == 20.0


def test_process_batch_clears_queue_after_processing() -> None:
    """Test process_batch clears queue after processing."""
    config = ModifierConfig()
    stat_name = fake.word()
    config.register_stat(
        name=stat_name,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    processor = BatchModifierProcessor(config=config)
    entity_id = EntityID(fake.uuid4())
    modifier = Modifier(
        entity_id=entity_id,
        stat=stat_name,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    processor.queue_modifier(modifier=modifier)
    processor.process_batch()

    assert processor.get_queue_size() == 0


def test_clear_queue_removes_all_queued_modifiers() -> None:
    """Test clear_queue removes all modifiers from queue."""
    config = ModifierConfig()
    processor = BatchModifierProcessor(config=config)
    entity_id = EntityID(fake.uuid4())

    for _ in range(3):
        modifier = Modifier(
            entity_id=entity_id,
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        )
        processor.queue_modifier(modifier=modifier)

    processor.clear_queue()

    assert processor.get_queue_size() == 0


def test_get_queue_size_returns_zero_initially() -> None:
    """Test get_queue_size returns 0 when queue is empty."""
    config = ModifierConfig()
    processor = BatchModifierProcessor(config=config)
    assert processor.get_queue_size() == 0


def test_get_queue_size_returns_correct_count() -> None:
    """Test get_queue_size returns correct number of queued modifiers."""
    config = ModifierConfig()
    processor = BatchModifierProcessor(config=config)
    entity_id = EntityID(fake.uuid4())
    count = fake.pyint(min_value=1, max_value=10)

    for _ in range(count):
        modifier = Modifier(
            entity_id=entity_id,
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        )
        processor.queue_modifier(modifier=modifier)

    assert processor.get_queue_size() == count


@patch("yuna.modifiers.batch.get_performance_monitor")
def test_process_batch_with_profiling_tracks_execution_time(
    mock_get_monitor: Mock,
) -> None:
    """Test process_batch tracks execution time when profiling enabled."""
    mock_monitor = Mock()
    mock_monitor.sample.return_value.__enter__ = Mock()
    mock_monitor.sample.return_value.__exit__ = Mock()
    mock_get_monitor.return_value = mock_monitor
    config = ModifierConfig()
    processor = BatchModifierProcessor(config=config, profiling_enabled=True)

    processor.process_batch()

    mock_monitor.sample.assert_called_once_with(
        category="modifier_batch", name="process"
    )


@patch("yuna.modifiers.batch.get_performance_monitor")
def test_process_batch_with_profiling_tracks_queue_size(
    mock_get_monitor: Mock,
) -> None:
    """Test process_batch tracks queue size metric when profiling enabled."""
    mock_monitor = Mock()
    mock_monitor.sample.return_value.__enter__ = Mock()
    mock_monitor.sample.return_value.__exit__ = Mock()
    mock_get_monitor.return_value = mock_monitor

    config = ModifierConfig()
    stat_name = fake.word()
    config.register_stat(
        name=stat_name,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    processor = BatchModifierProcessor(config=config, profiling_enabled=True)
    entity_id = EntityID(fake.uuid4())

    for _ in range(3):
        modifier = Modifier(
            entity_id=entity_id,
            stat=stat_name,
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        )
        processor.queue_modifier(modifier=modifier)

    processor.process_batch()

    mock_monitor.record_count.assert_called_once_with(
        category="modifier_batch", name="queue_size", count=3
    )


@patch("yuna.modifiers.batch.get_performance_monitor")
def test_process_batch_without_profiling_does_not_track_metrics(
    mock_get_monitor: Mock,
) -> None:
    """Test process_batch does not track metrics when profiling disabled."""
    config = ModifierConfig()
    processor = BatchModifierProcessor(config=config, profiling_enabled=False)

    processor.process_batch()

    mock_get_monitor.assert_not_called()


def test_process_batch_passes_world_to_pipeline() -> None:
    """Test process_batch passes world parameter to pipeline."""
    config = ModifierConfig()
    processor = BatchModifierProcessor(config=config)
    world = Mock()

    processor.process_batch(world=world)


def test_process_batch_passes_current_tick_to_pipeline() -> None:
    """Test process_batch passes current_tick parameter to pipeline."""
    config = ModifierConfig()
    processor = BatchModifierProcessor(config=config)
    current_tick = fake.pyint(min_value=0, max_value=1000)

    processor.process_batch(current_tick=current_tick)

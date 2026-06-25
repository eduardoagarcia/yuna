"""Tests for profiling integration in modifier pipeline stages."""

from unittest.mock import Mock, patch

from faker import Faker

from yuna.modifiers.config import ModifierConfig, StackingRule
from yuna.modifiers.context import ModifierContext
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.stages import (
    ApplyStage,
    ClampStage,
    CollectStage,
    ConditionStage,
    FilterStage,
    GroupStage,
    SortStage,
    StackStage,
)
from yuna.modifiers.types import (
    ModificationType,
    ModifierPriority,
)
from yuna.pipeline.context import PipelineContext
from yuna.types.identifiers import EntityID

fake = Faker()


@patch("yuna.modifiers.stages.get_performance_monitor")
def test_collect_stage_with_profiling_enabled_tracks_execution(
    mock_get_monitor: Mock,
) -> None:
    """Test CollectStage tracks execution time when profiling enabled."""
    mock_monitor = Mock()
    mock_monitor.sample.return_value.__enter__ = Mock()
    mock_monitor.sample.return_value.__exit__ = Mock()
    mock_get_monitor.return_value = mock_monitor

    stage = CollectStage(profiling_enabled=True)
    config = ModifierConfig()
    context = ModifierContext(modifiers=[], config=config, world=None)
    pipe_context = PipelineContext()

    stage.process(value=context, context=pipe_context)

    mock_monitor.sample.assert_called_once_with(
        category="modifier_stage", name="collect"
    )


@patch("yuna.modifiers.stages.get_performance_monitor")
def test_filter_stage_with_profiling_enabled_tracks_execution(
    mock_get_monitor: Mock,
) -> None:
    """Test FilterStage tracks execution time when profiling enabled."""
    mock_monitor = Mock()
    mock_monitor.sample.return_value.__enter__ = Mock()
    mock_monitor.sample.return_value.__exit__ = Mock()
    mock_get_monitor.return_value = mock_monitor

    stage = FilterStage(profiling_enabled=True)
    config = ModifierConfig()
    context = ModifierContext(modifiers=[], config=config, world=None)
    pipe_context = PipelineContext()

    stage.process(value=context, context=pipe_context)

    mock_monitor.sample.assert_called_once_with(
        category="modifier_stage", name="filter"
    )


@patch("yuna.modifiers.stages.get_performance_monitor")
def test_condition_stage_with_profiling_enabled_tracks_execution(
    mock_get_monitor: Mock,
) -> None:
    """Test ConditionStage tracks execution time when profiling enabled."""
    mock_monitor = Mock()
    mock_monitor.sample.return_value.__enter__ = Mock()
    mock_monitor.sample.return_value.__exit__ = Mock()
    mock_get_monitor.return_value = mock_monitor

    stage = ConditionStage(profiling_enabled=True)
    config = ModifierConfig()
    context = ModifierContext(modifiers=[], config=config, world=None)
    pipe_context = PipelineContext()

    stage.process(value=context, context=pipe_context)

    mock_monitor.sample.assert_called_once_with(
        category="modifier_stage", name="condition"
    )


@patch("yuna.modifiers.stages.get_performance_monitor")
def test_sort_stage_with_profiling_enabled_tracks_execution(
    mock_get_monitor: Mock,
) -> None:
    """Test SortStage tracks execution time when profiling enabled."""
    mock_monitor = Mock()
    mock_monitor.sample.return_value.__enter__ = Mock()
    mock_monitor.sample.return_value.__exit__ = Mock()
    mock_get_monitor.return_value = mock_monitor

    stage = SortStage(profiling_enabled=True)
    config = ModifierConfig()
    context = ModifierContext(modifiers=[], config=config, world=None)
    pipe_context = PipelineContext()

    stage.process(value=context, context=pipe_context)

    mock_monitor.sample.assert_called_once_with(category="modifier_stage", name="sort")


@patch("yuna.modifiers.stages.get_performance_monitor")
def test_group_stage_with_profiling_enabled_tracks_execution(
    mock_get_monitor: Mock,
) -> None:
    """Test GroupStage tracks execution time when profiling enabled."""
    mock_monitor = Mock()
    mock_monitor.sample.return_value.__enter__ = Mock()
    mock_monitor.sample.return_value.__exit__ = Mock()
    mock_get_monitor.return_value = mock_monitor

    stage = GroupStage(profiling_enabled=True)
    config = ModifierConfig()
    context = ModifierContext(modifiers=[], config=config, world=None)
    pipe_context = PipelineContext()

    stage.process(value=context, context=pipe_context)

    mock_monitor.sample.assert_called_once_with(category="modifier_stage", name="group")


@patch("yuna.modifiers.stages.get_performance_monitor")
def test_stack_stage_with_profiling_enabled_tracks_execution(
    mock_get_monitor: Mock,
) -> None:
    """Test StackStage tracks execution time when profiling enabled."""
    mock_monitor = Mock()
    mock_monitor.sample.return_value.__enter__ = Mock()
    mock_monitor.sample.return_value.__exit__ = Mock()
    mock_get_monitor.return_value = mock_monitor

    stage = StackStage(profiling_enabled=True)
    config = ModifierConfig()
    context = ModifierContext(modifiers=[], config=config, world=None)
    context.grouped = {}
    pipe_context = PipelineContext()

    stage.process(value=context, context=pipe_context)

    mock_monitor.sample.assert_called_once_with(category="modifier_stage", name="stack")


@patch("yuna.modifiers.stages.get_performance_monitor")
def test_clamp_stage_with_profiling_enabled_tracks_execution(
    mock_get_monitor: Mock,
) -> None:
    """Test ClampStage tracks execution time when profiling enabled."""
    mock_monitor = Mock()
    mock_monitor.sample.return_value.__enter__ = Mock()
    mock_monitor.sample.return_value.__exit__ = Mock()
    mock_get_monitor.return_value = mock_monitor

    stage = ClampStage(profiling_enabled=True)
    config = ModifierConfig()
    context = ModifierContext(modifiers=[], config=config, world=None)
    context.final_values = {}
    pipe_context = PipelineContext()

    stage.process(value=context, context=pipe_context)

    mock_monitor.sample.assert_called_once_with(category="modifier_stage", name="clamp")


@patch("yuna.modifiers.stages.get_performance_monitor")
def test_apply_stage_with_profiling_enabled_tracks_execution(
    mock_get_monitor: Mock,
) -> None:
    """Test ApplyStage tracks execution time when profiling enabled."""
    mock_monitor = Mock()
    mock_monitor.sample.return_value.__enter__ = Mock()
    mock_monitor.sample.return_value.__exit__ = Mock()
    mock_get_monitor.return_value = mock_monitor

    stage = ApplyStage(profiling_enabled=True)
    config = ModifierConfig()
    context = ModifierContext(modifiers=[], config=config, world=None)
    pipe_context = PipelineContext()

    stage.process(value=context, context=pipe_context)

    mock_monitor.sample.assert_called_once_with(category="modifier_stage", name="apply")


@patch("yuna.modifiers.stages.get_performance_monitor")
def test_stage_with_profiling_disabled_does_not_track_metrics(
    mock_get_monitor: Mock,
) -> None:
    """Test stages do not track metrics when profiling disabled."""
    stage = FilterStage(profiling_enabled=False)
    config = ModifierConfig()
    context = ModifierContext(modifiers=[], config=config, world=None)
    pipe_context = PipelineContext()

    stage.process(value=context, context=pipe_context)

    mock_get_monitor.assert_not_called()


def test_filter_stage_executes_correctly_with_profiling_enabled() -> None:
    """Test FilterStage executes filtering correctly with profiling enabled."""
    stage = FilterStage(profiling_enabled=True)
    entity_id = EntityID(fake.uuid4())
    stat_name = fake.word()

    valid_modifier = Modifier(
        entity_id=entity_id,
        stat=stat_name,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    invalid_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    config = ModifierConfig()
    config.register_stat(
        name=stat_name,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    context = ModifierContext(
        modifiers=[valid_modifier, invalid_modifier], config=config, world=None
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] == valid_modifier


def test_sort_stage_executes_correctly_with_profiling_enabled() -> None:
    """Test SortStage executes sorting correctly with profiling enabled."""
    stage = SortStage(profiling_enabled=True)
    entity_id = EntityID(fake.uuid4())
    stat_name = fake.word()

    high_priority = Modifier(
        entity_id=entity_id,
        stat=stat_name,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.HIGH,
        source=fake.word(),
    )
    normal_priority = Modifier(
        entity_id=entity_id,
        stat=stat_name,
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    config = ModifierConfig()
    context = ModifierContext(
        modifiers=[normal_priority, high_priority], config=config, world=None
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert result.modifiers[0] == high_priority
    assert result.modifiers[1] == normal_priority


def test_group_stage_executes_correctly_with_profiling_enabled() -> None:
    """Test GroupStage executes grouping correctly with profiling enabled."""
    stage = GroupStage(profiling_enabled=True)
    entity_id = EntityID(fake.uuid4())
    stat_name = fake.word()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=stat_name,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    modifier2 = Modifier(
        entity_id=entity_id,
        stat=stat_name,
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    config = ModifierConfig()
    context = ModifierContext(
        modifiers=[modifier1, modifier2], config=config, world=None
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert (entity_id, stat_name) in result.grouped
    assert len(result.grouped[(entity_id, stat_name)]) == 2


def test_clamp_stage_executes_correctly_with_profiling_enabled() -> None:
    """Test ClampStage executes clamping correctly with profiling enabled."""
    stage = ClampStage(profiling_enabled=True)
    entity_id = EntityID(fake.uuid4())
    stat_name = fake.word()

    config = ModifierConfig()
    config.register_stat(
        name=stat_name,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    context = ModifierContext(modifiers=[], config=config, world=None)
    context.final_values = {(entity_id, stat_name): 150.0}
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert result.final_values[(entity_id, stat_name)] == 100.0

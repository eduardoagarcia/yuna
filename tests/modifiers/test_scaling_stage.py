"""Tests for ScalingStage."""

from unittest.mock import Mock

from faker import Faker

from yuna.modifiers.config import ModifierConfig
from yuna.modifiers.context import ModifierContext
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.scaling import (
    CurveFunctions,
    TimeInterpolation,
    ValueCalculators,
)
from yuna.modifiers.stages import ScalingStage
from yuna.modifiers.types import ModificationType, ModifierPriority
from yuna.pipeline.context import PipelineContext
from yuna.types.identifiers import EntityID

fake = Faker()


def test_scaling_stage_name() -> None:
    """Test scaling stage has correct name."""
    stage = ScalingStage()

    assert stage.name == "scaling"


def test_scaling_stage_no_scaling_modifiers() -> None:
    """Test scaling stage passes through modifiers without scaling fields."""
    stage = ScalingStage()
    entity_id = EntityID(fake.uuid4())
    value = fake.pyfloat(min_value=1.0, max_value=100.0)

    modifier = Modifier(
        entity_id=entity_id,
        stat="test_stat",
        modification_type=ModificationType.FLAT,
        value=value,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    context = ModifierContext(
        modifiers=[modifier],
        config=ModifierConfig(),
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0].value == value


def test_scaling_stage_applies_value_calculator() -> None:
    """Test scaling stage applies value_calculator."""
    stage = ScalingStage()
    entity_id = EntityID(fake.uuid4())
    base_value = 10.0
    stat_value = 50.0

    calculator = ValueCalculators.scale_by_stat(
        stat_name="strength",
        multiplier=0.5,
        additive=True,
    )

    modifier = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=base_value,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        value_calculator=calculator,
    )

    world = Mock()
    world.get_stat.return_value = stat_value

    context = ModifierContext(
        modifiers=[modifier],
        config=ModifierConfig(),
        world=world,
    )
    context.entity_id = entity_id
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0].value == base_value + (stat_value * 0.5)


def test_scaling_stage_applies_curve_function() -> None:
    """Test scaling stage applies curve_function."""
    stage = ScalingStage()
    entity_id = EntityID(fake.uuid4())
    base_value = 5.0

    modifier = Modifier(
        entity_id=entity_id,
        stat="test_stat",
        modification_type=ModificationType.FLAT,
        value=base_value,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        curve_function=CurveFunctions.quadratic,
    )

    context = ModifierContext(
        modifiers=[modifier],
        config=ModifierConfig(),
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0].value == base_value * base_value


def test_scaling_stage_applies_time_interpolation() -> None:
    """Test scaling stage applies time_interpolation."""
    stage = ScalingStage()
    entity_id = EntityID(fake.uuid4())
    base_value = 100.0
    duration = 10
    current_tick = 5

    modifier = Modifier(
        entity_id=entity_id,
        stat="test_stat",
        modification_type=ModificationType.FLAT,
        value=base_value,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=duration,
        time_interpolation=TimeInterpolation.LINEAR,
    )

    context = ModifierContext(
        modifiers=[modifier],
        config=ModifierConfig(),
        current_tick=current_tick,
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    expected = base_value * (current_tick / duration)
    assert result.modifiers[0].value == expected


def test_scaling_stage_applies_all_scaling_functions() -> None:
    """Test scaling stage applies calculator, curve, and interpolation in order."""
    stage = ScalingStage()
    entity_id = EntityID(fake.uuid4())

    calculator = ValueCalculators.scale_by_stat(
        stat_name="test_stat",
        multiplier=2.0,
        additive=True,
    )

    modifier = Modifier(
        entity_id=entity_id,
        stat="output",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=10,
        value_calculator=calculator,
        curve_function=CurveFunctions.quadratic,
        time_interpolation=TimeInterpolation.LINEAR,
    )

    world = Mock()
    world.get_stat.return_value = 20.0

    context = ModifierContext(
        modifiers=[modifier],
        config=ModifierConfig(),
        world=world,
        current_tick=5,
    )
    context.entity_id = entity_id
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    expected = 0.0 + (10.0 - 0.0) * (5 / 10)

    assert len(result.modifiers) == 1
    assert result.modifiers[0].value == expected


def test_scaling_stage_preserves_unmodified_modifiers() -> None:
    """Test scaling stage preserves modifiers without scaling."""
    stage = ScalingStage()
    entity_id = EntityID(fake.uuid4())
    value = fake.pyfloat(min_value=1.0, max_value=100.0)

    modifier1 = Modifier(
        entity_id=entity_id,
        stat="stat1",
        modification_type=ModificationType.FLAT,
        value=value,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat="stat2",
        modification_type=ModificationType.FLAT,
        value=value * 2,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        curve_function=CurveFunctions.quadratic,
    )

    context = ModifierContext(
        modifiers=[modifier1, modifier2],
        config=ModifierConfig(),
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 2
    assert result.modifiers[0] is modifier1
    assert result.modifiers[1].value == (value * 2) ** 2


def test_scaling_stage_time_progress_no_duration() -> None:
    """Test time progress returns 1.0 when no duration."""
    stage = ScalingStage()
    entity_id = EntityID(fake.uuid4())

    modifier = Modifier(
        entity_id=entity_id,
        stat="test_stat",
        modification_type=ModificationType.FLAT,
        value=100.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=None,
        time_interpolation=TimeInterpolation.LINEAR,
    )

    context = ModifierContext(
        modifiers=[modifier],
        config=ModifierConfig(),
        current_tick=50,
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert result.modifiers[0].value == 100.0


def test_scaling_stage_time_progress_zero_duration() -> None:
    """Test time progress returns 1.0 when duration is zero."""
    stage = ScalingStage()
    entity_id = EntityID(fake.uuid4())

    modifier = Modifier(
        entity_id=entity_id,
        stat="test_stat",
        modification_type=ModificationType.FLAT,
        value=100.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=0,
        time_interpolation=TimeInterpolation.LINEAR,
    )

    context = ModifierContext(
        modifiers=[modifier],
        config=ModifierConfig(),
        current_tick=50,
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert result.modifiers[0].value == 100.0


def test_scaling_stage_time_progress_clamps_to_one() -> None:
    """Test time progress clamps to 1.0 when elapsed exceeds duration."""
    stage = ScalingStage()
    entity_id = EntityID(fake.uuid4())

    modifier = Modifier(
        entity_id=entity_id,
        stat="test_stat",
        modification_type=ModificationType.FLAT,
        value=100.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=10,
        time_interpolation=TimeInterpolation.LINEAR,
    )

    context = ModifierContext(
        modifiers=[modifier],
        config=ModifierConfig(),
        current_tick=20,
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert result.modifiers[0].value == 100.0


def test_scaling_stage_with_profiling_enabled() -> None:
    """Test scaling stage with profiling enabled."""
    stage = ScalingStage(profiling_enabled=True)
    entity_id = EntityID(fake.uuid4())

    modifier = Modifier(
        entity_id=entity_id,
        stat="test_stat",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    context = ModifierContext(
        modifiers=[modifier],
        config=ModifierConfig(),
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0].value == 10.0

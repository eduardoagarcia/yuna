"""Integration tests for ModifierPipeline with scaling features."""

from unittest.mock import Mock

from faker import Faker

from yuna.modifiers.config import ModifierConfig, StackingRule
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.modifiers.scaling import (
    CurveFunctions,
    TimeInterpolation,
    ValueCalculators,
)
from yuna.modifiers.types import ModificationType, ModifierPriority
from yuna.types.identifiers import EntityID

fake = Faker()


def create_test_pipeline() -> tuple[ModifierConfig, ModifierPipeline]:
    """Create pipeline with test stats registered."""
    config = ModifierConfig()
    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_stat(
        name="strength",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    return config, pipeline


def test_pipeline_processes_value_calculator() -> None:
    """Test pipeline correctly processes modifiers with value_calculator."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    base_damage = 10.0
    strength_value = 50.0

    calculator = ValueCalculators.scale_by_stat(
        stat_name="strength",
        multiplier=0.5,
        additive=True,
    )

    modifier = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=base_damage,
        priority=ModifierPriority.NORMAL,
        source="strength_scaling",
        value_calculator=calculator,
    )

    world = Mock()
    world.get_stat.return_value = strength_value

    pipeline.queue_modifier(modifier=modifier)
    results = pipeline.process(world=world, current_tick=0)

    expected = base_damage + (strength_value * 0.5)
    assert results[(entity_id, "damage")] == expected


def test_pipeline_processes_curve_function() -> None:
    """Test pipeline correctly processes modifiers with curve_function."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    base_value = 5.0

    modifier = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=base_value,
        priority=ModifierPriority.NORMAL,
        source="quadratic_scaling",
        curve_function=CurveFunctions.quadratic,
    )

    pipeline.queue_modifier(modifier=modifier)
    results = pipeline.process(current_tick=0)

    expected = base_value * base_value
    assert results[(entity_id, "damage")] == expected


def test_pipeline_processes_time_interpolation() -> None:
    """Test pipeline correctly processes modifiers with time_interpolation."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    base_value = 100.0
    duration = 10
    current_tick = 5

    modifier = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=base_value,
        priority=ModifierPriority.NORMAL,
        source="ramping_buff",
        duration_ticks=duration,
        time_interpolation=TimeInterpolation.LINEAR,
    )

    pipeline.queue_modifier(modifier=modifier)
    results = pipeline.process(current_tick=current_tick)

    expected = base_value * (current_tick / duration)
    assert results[(entity_id, "damage")] == expected


def test_pipeline_scales_then_stacks_multiple_modifiers() -> None:
    """Test pipeline applies scaling before stacking."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())

    modifier1 = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source="base_damage",
        curve_function=CurveFunctions.quadratic,
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source="bonus_damage",
    )

    pipeline.queue_modifier(modifier=modifier1)
    pipeline.queue_modifier(modifier=modifier2)
    results = pipeline.process(current_tick=0)

    expected = (10.0 * 10.0) + 5.0
    assert results[(entity_id, "damage")] == expected


def test_pipeline_applies_calculator_then_curve() -> None:
    """Test pipeline applies value_calculator before curve_function."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    base_value = 5.0
    stat_value = 10.0

    calculator = ValueCalculators.scale_by_stat(
        stat_name="strength",
        multiplier=2.0,
        additive=True,
    )

    modifier = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=base_value,
        priority=ModifierPriority.NORMAL,
        source="complex_scaling",
        value_calculator=calculator,
        curve_function=CurveFunctions.quadratic,
    )

    world = Mock()
    world.get_stat.return_value = stat_value

    pipeline.queue_modifier(modifier=modifier)
    results = pipeline.process(world=world, current_tick=0)

    after_calculator = base_value + (stat_value * 2.0)
    expected = after_calculator * after_calculator
    assert results[(entity_id, "damage")] == expected


def test_pipeline_applies_calculator_curve_then_interpolation() -> None:
    """Test pipeline applies all scaling functions in correct order."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    base_value = 10.0
    duration = 10
    current_tick = 5

    modifier = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=base_value,
        priority=ModifierPriority.NORMAL,
        source="full_scaling",
        duration_ticks=duration,
        curve_function=CurveFunctions.quadratic,
        time_interpolation=TimeInterpolation.LINEAR,
    )

    pipeline.queue_modifier(modifier=modifier)
    results = pipeline.process(current_tick=current_tick)

    progress = current_tick / duration
    expected = 0.0 + (base_value - 0.0) * progress
    assert results[(entity_id, "damage")] == expected


def test_pipeline_scales_percentage_modifiers() -> None:
    """Test pipeline correctly scales PERCENTAGE modifiers."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())

    flat_modifier = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=100.0,
        priority=ModifierPriority.NORMAL,
        source="base",
    )

    percentage_modifier = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.PERCENTAGE,
        value=0.50,
        priority=ModifierPriority.NORMAL,
        source="percentage_boost",
        curve_function=CurveFunctions.quadratic,
    )

    pipeline.queue_modifier(modifier=flat_modifier)
    pipeline.queue_modifier(modifier=percentage_modifier)
    results = pipeline.process(current_tick=0)

    scaled_percentage = 0.50 * 0.50
    expected = 100.0 + (100.0 * scaled_percentage)
    assert results[(entity_id, "damage")] == expected


def test_pipeline_diminishing_returns_with_multiple_modifiers() -> None:
    """Test pipeline applies diminishing returns correctly."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    base_value = 10.0
    diminishing_factor = 0.6

    calculator = ValueCalculators.diminishing_returns(
        base_value=base_value,
        diminishing_factor=diminishing_factor,
    )

    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.FLAT,
            value=base_value,
            priority=ModifierPriority.NORMAL,
            source=f"stack_{i}",
            value_calculator=calculator,
        )
        for i in range(3)
    ]

    for modifier in modifiers:
        pipeline.queue_modifier(modifier=modifier)

    results = pipeline.process(current_tick=0)

    expected_per_modifier = base_value * (1.0 - ((1.0 - diminishing_factor) ** 3))
    expected_total = expected_per_modifier * 3
    assert results[(entity_id, "damage")] == expected_total


def test_pipeline_time_ramping_progression() -> None:
    """Test pipeline time interpolation progresses correctly over ticks."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    base_value = 100.0
    duration = 10

    modifier = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=base_value,
        priority=ModifierPriority.NORMAL,
        source="ramping",
        duration_ticks=duration,
        time_interpolation=TimeInterpolation.LINEAR,
    )

    results_at_tick_0 = pipeline.process(current_tick=0)
    assert results_at_tick_0.get((entity_id, "damage"), 0.0) == 0.0

    pipeline.queue_modifier(modifier=modifier)
    results_at_tick_5 = pipeline.process(current_tick=5)
    assert results_at_tick_5[(entity_id, "damage")] == 50.0

    pipeline.queue_modifier(modifier=modifier)
    results_at_tick_10 = pipeline.process(current_tick=10)
    assert results_at_tick_10[(entity_id, "damage")] == 100.0


def test_pipeline_ease_in_out_interpolation() -> None:
    """Test pipeline applies ease-in-out interpolation correctly."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    base_value = 100.0
    duration = 10
    current_tick = 3

    modifier = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=base_value,
        priority=ModifierPriority.NORMAL,
        source="easing",
        duration_ticks=duration,
        time_interpolation=TimeInterpolation.EASE_IN_OUT,
    )

    pipeline.queue_modifier(modifier=modifier)
    results = pipeline.process(current_tick=current_tick)

    progress = current_tick / duration
    t = 2.0 * progress * progress
    expected = 0.0 + (base_value - 0.0) * t
    assert results[(entity_id, "damage")] == expected


def test_pipeline_isolates_entities() -> None:
    """Test pipeline correctly isolates scaling between different entities."""
    config, pipeline = create_test_pipeline()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    modifier1 = Modifier(
        entity_id=entity1,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source="entity1_damage",
        curve_function=CurveFunctions.quadratic,
    )

    modifier2 = Modifier(
        entity_id=entity2,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source="entity2_damage",
    )

    pipeline.queue_modifier(modifier=modifier1)
    pipeline.queue_modifier(modifier=modifier2)
    results = pipeline.process(current_tick=0)

    assert results[(entity1, "damage")] == 100.0
    assert results[(entity2, "damage")] == 5.0


def test_pipeline_clamps_scaled_values() -> None:
    """Test pipeline clamps scaled values to stat min/max."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())

    modifier = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=50.0,
        priority=ModifierPriority.NORMAL,
        source="huge_damage",
        curve_function=CurveFunctions.cubic,
    )

    pipeline.queue_modifier(modifier=modifier)
    results = pipeline.process(current_tick=0)

    assert results[(entity_id, "damage")] == 1000.0

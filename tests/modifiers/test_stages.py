"""Tests for modifier pipeline stages."""

from faker import Faker

from yuna.modifiers.config import (
    ModifierConfig,
    StackingRule,
)
from yuna.modifiers.context import ModifierContext
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.stages import (
    ApplyStage,
    ClampStage,
    CollectStage,
    FilterStage,
    GroupStage,
    InterceptStage,
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


def test_collect_stage_creation() -> None:
    """Test CollectStage can be instantiated."""
    stage = CollectStage()
    assert stage is not None


def test_collect_stage_has_name() -> None:
    """Test collect stage has name."""
    stage = CollectStage()
    assert stage.name == "collect"


def test_collect_stage_passes_through() -> None:
    """Test collect stage returns input unchanged."""
    stage = CollectStage()
    config = ModifierConfig()
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=1.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        )
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result is ctx


def test_filter_stage_creation() -> None:
    """Test FilterStage can be instantiated."""
    stage = FilterStage()
    assert stage is not None


def test_filter_stage_has_name() -> None:
    """Test filter stage has name."""
    stage = FilterStage()
    assert stage.name == "filter"


def test_filter_stage_removes_invalid_stats() -> None:
    """Test filter stage removes modifiers for unknown stats."""
    stage = FilterStage()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="health",
            modification_type=ModificationType.FLAT,
            value=1.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="invalid_stat",
            modification_type=ModificationType.FLAT,
            value=1.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert len(result.modifiers) == 1
    assert result.modifiers[0].stat == "health"


def test_filter_stage_keeps_all_valid() -> None:
    """Test filter stage keeps all valid modifiers."""
    stage = FilterStage()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="health",
            modification_type=ModificationType.FLAT,
            value=1.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="health",
            modification_type=ModificationType.FLAT,
            value=2.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert len(result.modifiers) == 2


def test_sort_stage_creation() -> None:
    """Test SortStage can be instantiated."""
    stage = SortStage()
    assert stage is not None


def test_sort_stage_has_name() -> None:
    """Test sort stage has name."""
    stage = SortStage()
    assert stage.name == "sort"


def test_sort_stage_sorts_by_priority() -> None:
    """Test sort stage orders modifiers by priority."""
    stage = SortStage()
    config = ModifierConfig()
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=1.0,
            priority=ModifierPriority.LOW,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=2.0,
            priority=ModifierPriority.CRITICAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=3.0,
            priority=ModifierPriority.HIGH,
            source=fake.word(),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.modifiers[0].priority == ModifierPriority.CRITICAL
    assert result.modifiers[1].priority == ModifierPriority.HIGH
    assert result.modifiers[2].priority == ModifierPriority.LOW


def test_group_stage_creation() -> None:
    """Test GroupStage can be instantiated."""
    stage = GroupStage()
    assert stage is not None


def test_group_stage_has_name() -> None:
    """Test group stage has name."""
    stage = GroupStage()
    assert stage.name == "group"


def test_group_stage_groups_by_entity_and_stat() -> None:
    """Test group stage groups modifiers by entity+stat."""
    stage = GroupStage()
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="health",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=entity_id,
            stat="health",
            modification_type=ModificationType.FLAT,
            value=5.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="health",
            modification_type=ModificationType.FLAT,
            value=3.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert len(result.grouped) == 2
    assert len(result.grouped[(entity_id, "health")]) == 2


def test_stack_stage_creation() -> None:
    """Test StackStage can be instantiated."""
    stage = StackStage()
    assert stage is not None


def test_stack_stage_has_name() -> None:
    """Test stack stage has name."""
    stage = StackStage()
    assert stage.name == "stack"


def test_stack_stage_sums_flat_modifiers() -> None:
    """Test stack stage sums FLAT modifiers."""
    stage = StackStage()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="health",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=entity_id,
            stat="health",
            modification_type=ModificationType.FLAT,
            value=5.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "health"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "health")] == 15.0


def test_stack_stage_applies_multipliers() -> None:
    """Test stack stage applies multiplier modifiers."""
    stage = StackStage()
    config = ModifierConfig()
    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.MULTIPLY,
    )
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=2.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "damage"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "damage")] == 20.0


def test_stack_stage_set_overrides_all() -> None:
    """Test SET modifier overrides all other modifiers."""
    stage = StackStage()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="health",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=entity_id,
            stat="health",
            modification_type=ModificationType.SET,
            value=50.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "health"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "health")] == 50.0


def test_clamp_stage_creation() -> None:
    """Test ClampStage can be instantiated."""
    stage = ClampStage()
    assert stage is not None


def test_clamp_stage_has_name() -> None:
    """Test clamp stage has name."""
    stage = ClampStage()
    assert stage.name == "clamp"


def test_clamp_stage_clamps_to_max() -> None:
    """Test clamp stage enforces maximum value."""
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    entity_id = EntityID(fake.uuid4())
    ctx = ModifierContext(modifiers=[], config=config)
    ctx.final_values = {(entity_id, "health"): 150.0}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "health")] == 100.0


def test_clamp_stage_clamps_to_min() -> None:
    """Test clamp stage enforces minimum value."""
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    entity_id = EntityID(fake.uuid4())
    ctx = ModifierContext(modifiers=[], config=config)
    ctx.final_values = {(entity_id, "health"): -10.0}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "health")] == 0.0


def test_clamp_stage_preserves_valid_value() -> None:
    """Test clamp stage preserves values within bounds."""
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    entity_id = EntityID(fake.uuid4())
    ctx = ModifierContext(modifiers=[], config=config)
    ctx.final_values = {(entity_id, "health"): 50.0}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "health")] == 50.0


def test_clamp_stage_rounds_with_precision() -> None:
    """Test clamp stage rounds values when precision is set."""
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="battery",
        min_value=0.0,
        max_value=1.0,
        stacking_rule=StackingRule.ADD,
        precision=4,
    )
    entity_id = EntityID(fake.uuid4())
    ctx = ModifierContext(modifiers=[], config=config)
    ctx.final_values = {(entity_id, "battery"): 0.99870000000000002}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "battery")] == 0.9987


def test_clamp_stage_no_rounding_without_precision() -> None:
    """Test clamp stage does not round when precision is None."""
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="battery",
        min_value=0.0,
        max_value=1.0,
        stacking_rule=StackingRule.ADD,
    )
    entity_id = EntityID(fake.uuid4())
    ctx = ModifierContext(modifiers=[], config=config)
    ctx.final_values = {(entity_id, "battery"): 0.99870000000000002}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "battery")] == 0.99870000000000002


def test_clamp_stage_rounds_after_clamping() -> None:
    """Test clamp stage rounds after applying min/max bounds."""
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
        precision=2,
    )
    entity_id = EntityID(fake.uuid4())
    ctx = ModifierContext(modifiers=[], config=config)
    ctx.final_values = {(entity_id, "health"): 150.123456}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "health")] == 100.0


def test_apply_stage_creation() -> None:
    """Test ApplyStage can be instantiated."""
    stage = ApplyStage()
    assert stage is not None


def test_apply_stage_has_name() -> None:
    """Test apply stage has name."""
    stage = ApplyStage()
    assert stage.name == "apply"


def test_apply_stage_returns_context() -> None:
    """Test apply stage returns context."""
    stage = ApplyStage()
    config = ModifierConfig()
    ctx = ModifierContext(modifiers=[], config=config)
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result is ctx


def test_stack_stage_percentage_modifiers_without_base_equal_zero() -> None:
    """Test percentage modifiers without base value result in zero."""
    stage = StackStage()
    config = ModifierConfig()
    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.PERCENTAGE,
            value=0.25,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.PERCENTAGE,
            value=0.15,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "damage"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "damage")] == 0.0


def test_stack_stage_multiplier_with_add_stacking() -> None:
    """Test multiplier modifiers with ADD stacking rule."""
    stage = StackStage()
    config = ModifierConfig()
    config.register_stat(
        name="speed",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="speed",
            modification_type=ModificationType.FLAT,
            value=100.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=entity_id,
            stat="speed",
            modification_type=ModificationType.MULTIPLIER,
            value=1.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=entity_id,
            stat="speed",
            modification_type=ModificationType.MULTIPLIER,
            value=0.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "speed"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "speed")] == 200.0


def test_stack_stage_multiplier_with_max_stacking() -> None:
    """Test multiplier modifiers with MAX stacking rule."""
    stage = StackStage()
    config = ModifierConfig()
    config.register_stat(
        name="armor",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.MAX,
    )
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="armor",
            modification_type=ModificationType.FLAT,
            value=50.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=entity_id,
            stat="armor",
            modification_type=ModificationType.MULTIPLIER,
            value=2.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "armor"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "armor")] == 50.0


def test_stack_stage_uses_value_reader_as_baseline() -> None:
    """Test StackStage uses value reader to get baseline value."""
    stage = StackStage()
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())

    def test_reader(entity_id: EntityID, stat: str, world: object) -> float:
        return 100.0

    config.register_stat(
        name="battery",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_value_reader(stat="battery", reader=test_reader)

    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="battery",
            modification_type=ModificationType.FLAT,
            value=-0.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config, world=object())
    ctx.grouped = {(entity_id, "battery"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "battery")] == 99.5


def test_stack_stage_defaults_to_zero_without_reader() -> None:
    """Test StackStage defaults to 0.0 baseline when no value reader registered."""
    stage = StackStage()
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())

    config.register_stat(
        name="battery",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="battery",
            modification_type=ModificationType.FLAT,
            value=-0.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "battery"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "battery")] == -0.5


def test_apply_stage_invokes_applicators() -> None:
    """Test ApplyStage invokes registered applicators."""
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())
    stat = "health"

    applied_values = {}

    def test_applicator(
        entity_id: EntityID, stat: str, value: float, world: object
    ) -> None:
        applied_values[(entity_id, stat)] = value

    config.register_stat(
        name=stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_applicator(stat=stat, applicator=test_applicator)

    ctx = ModifierContext(modifiers=[], config=config, world=object())
    ctx.final_values = {(entity_id, stat): 75.0}
    pipe_ctx = PipelineContext()
    stage = ApplyStage()

    stage.process(value=ctx, context=pipe_ctx)

    assert (entity_id, stat) in applied_values
    assert applied_values[(entity_id, stat)] == 75.0


def test_apply_stage_skips_stats_without_applicators() -> None:
    """Test ApplyStage skips stats that have no registered applicator."""
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())
    stat = "health"

    applied_values = {}

    def test_applicator(
        entity_id: EntityID, stat: str, value: float, world: object
    ) -> None:
        applied_values[(entity_id, stat)] = value

    config.register_stat(
        name=stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    ctx = ModifierContext(modifiers=[], config=config, world=object())
    ctx.final_values = {(entity_id, stat): 75.0}
    pipe_ctx = PipelineContext()
    stage = ApplyStage()

    stage.process(value=ctx, context=pipe_ctx)

    assert (entity_id, stat) not in applied_values


def test_apply_stage_skips_when_no_world() -> None:
    """Test ApplyStage does nothing when world is None."""
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())
    stat = "health"

    applied_values = {}

    def test_applicator(
        entity_id: EntityID, stat: str, value: float, world: object
    ) -> None:
        applied_values[(entity_id, stat)] = value

    config.register_stat(
        name=stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_applicator(stat=stat, applicator=test_applicator)

    ctx = ModifierContext(modifiers=[], config=config, world=None)
    ctx.final_values = {(entity_id, stat): 75.0}
    pipe_ctx = PipelineContext()
    stage = ApplyStage()

    stage.process(value=ctx, context=pipe_ctx)

    assert (entity_id, stat) not in applied_values


def test_compute_multiplier_with_add_stacking() -> None:
    """Test _compute_multiplier sums values with ADD stacking rule."""
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.MULTIPLIER,
            value=1.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.MULTIPLIER,
            value=0.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.MULTIPLIER,
            value=0.25,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    result = StackStage._compute_multiplier(
        modifiers=modifiers, stacking_rule=StackingRule.ADD
    )
    assert result == 2.25


def test_compute_multiplier_with_multiply_stacking() -> None:
    """Test _compute_multiplier multiplies values with MULTIPLY stacking rule."""
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.MULTIPLIER,
            value=2.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.MULTIPLIER,
            value=1.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.MULTIPLIER,
            value=0.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    result = StackStage._compute_multiplier(
        modifiers=modifiers, stacking_rule=StackingRule.MULTIPLY
    )
    assert result == 1.5


def test_compute_multiplier_with_max_stacking_returns_default() -> None:
    """Test _compute_multiplier returns 1.0 for non-ADD/MULTIPLY rules."""
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.MULTIPLIER,
            value=2.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.MULTIPLIER,
            value=3.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    result = StackStage._compute_multiplier(
        modifiers=modifiers, stacking_rule=StackingRule.MAX
    )
    assert result == 1.0


def test_compute_multiplier_with_empty_list() -> None:
    """Test _compute_multiplier handles empty modifier list."""
    result = StackStage._compute_multiplier(
        modifiers=[], stacking_rule=StackingRule.ADD
    )
    assert result == 0.0


def test_compute_multiplier_with_single_modifier() -> None:
    """Test _compute_multiplier handles single modifier correctly."""
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.MULTIPLIER,
            value=3.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    result = StackStage._compute_multiplier(
        modifiers=modifiers, stacking_rule=StackingRule.ADD
    )
    assert result == 3.5


def test_group_by_category_with_no_categories() -> None:
    """Test _group_by_category groups modifiers with None category."""
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=5.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    result = StackStage._group_by_category(modifiers=modifiers)
    assert len(result) == 1
    assert None in result
    assert len(result[None]) == 2


def test_group_by_category_with_single_category() -> None:
    """Test _group_by_category groups modifiers with same category."""
    category_name = fake.word()
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_name,),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=5.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_name,),
        ),
    ]
    result = StackStage._group_by_category(modifiers=modifiers)
    assert len(result) == 1
    assert category_name in result
    assert len(result[category_name]) == 2


def test_group_by_category_with_multiple_categories() -> None:
    """Test _group_by_category groups modifiers across multiple categories."""
    category_one = fake.unique.word()
    category_two = fake.unique.word()
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_one,),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=5.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_two,),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=3.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_one,),
        ),
    ]
    result = StackStage._group_by_category(modifiers=modifiers)
    assert len(result) == 2
    assert category_one in result
    assert category_two in result
    assert len(result[category_one]) == 2
    assert len(result[category_two]) == 1


def test_group_by_category_with_mixed_categories_and_none() -> None:
    """Test _group_by_category groups modifiers with mix of categories and None."""
    category_name = fake.word()
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_name,),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=5.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    result = StackStage._group_by_category(modifiers=modifiers)
    assert len(result) == 2
    assert category_name in result
    assert None in result
    assert len(result[category_name]) == 1
    assert len(result[None]) == 1


def test_group_by_category_with_empty_list() -> None:
    """Test _group_by_category handles empty modifier list."""
    result = StackStage._group_by_category(modifiers=[])
    assert len(result) == 0


def test_process_category_modifiers_with_only_flat() -> None:
    """Test _process_category_modifiers with only FLAT modifiers."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    stat_config = config.get_stat_config(name="health")
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="health",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="health",
            modification_type=ModificationType.FLAT,
            value=5.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    result, multipliers, is_set = StackStage._process_category_modifiers(
        category_mods=modifiers, category_config=None, stat_config=stat_config
    )
    assert result == 15.0
    assert len(multipliers) == 0
    assert is_set is False


def test_process_category_modifiers_with_only_multipliers() -> None:
    """Test _process_category_modifiers with only MULTIPLIER modifiers."""
    config = ModifierConfig()
    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    stat_config = config.get_stat_config(name="damage")
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=1.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=0.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    result, multipliers, is_set = StackStage._process_category_modifiers(
        category_mods=modifiers, category_config=None, stat_config=stat_config
    )
    assert result is None
    assert len(multipliers) == 2
    assert multipliers[0].value == 1.5
    assert multipliers[1].value == 0.5
    assert is_set is False


def test_process_category_modifiers_with_flat_and_multiplier() -> None:
    """Test _process_category_modifiers with FLAT and MULTIPLIER modifiers."""
    config = ModifierConfig()
    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    stat_config = config.get_stat_config(name="damage")
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=2.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    result, multipliers, is_set = StackStage._process_category_modifiers(
        category_mods=modifiers, category_config=None, stat_config=stat_config
    )
    assert result == 20.0
    assert len(multipliers) == 0
    assert is_set is False


def test_process_category_modifiers_with_set_modifier() -> None:
    """Test _process_category_modifiers with SET modifier overrides all."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    stat_config = config.get_stat_config(name="health")
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="health",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="health",
            modification_type=ModificationType.SET,
            value=50.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="health",
            modification_type=ModificationType.MULTIPLIER,
            value=2.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    result, multipliers, is_set = StackStage._process_category_modifiers(
        category_mods=modifiers, category_config=None, stat_config=stat_config
    )
    assert result == 50.0
    assert len(multipliers) == 0
    assert is_set is True


def test_process_category_modifiers_with_multiple_set_modifiers() -> None:
    """Test _process_category_modifiers picks the lowest-priority SET."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    stat_config = config.get_stat_config(name="health")
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="health",
            modification_type=ModificationType.SET,
            value=40.0,
            priority=ModifierPriority.HIGH,
            source=fake.word(),
        ),
        Modifier(
            entity_id=entity_id,
            stat="health",
            modification_type=ModificationType.SET,
            value=50.0,
            priority=ModifierPriority.LOW,
            source=fake.word(),
        ),
    ]
    result, multipliers, is_set = StackStage._process_category_modifiers(
        category_mods=modifiers, category_config=None, stat_config=stat_config
    )
    assert result == 50.0
    assert len(multipliers) == 0
    assert is_set is True


def test_process_category_modifiers_set_tie_resolves_to_max_value() -> None:
    """Test tied SET modifiers resolve to the highest value (E13)."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    stat_config = config.get_stat_config(name="health")
    shared_entity_id = EntityID(fake.uuid4())
    shared_source = fake.word()
    shared_source_id = EntityID(fake.uuid4())
    lower_set = Modifier(
        entity_id=shared_entity_id,
        stat="health",
        modification_type=ModificationType.SET,
        value=30.0,
        priority=ModifierPriority.NORMAL,
        source=shared_source,
        source_id=shared_source_id,
    )
    higher_set = Modifier(
        entity_id=shared_entity_id,
        stat="health",
        modification_type=ModificationType.SET,
        value=70.0,
        priority=ModifierPriority.NORMAL,
        source=shared_source,
        source_id=shared_source_id,
    )
    result_ascending, _, is_set_ascending = StackStage._process_category_modifiers(
        category_mods=[lower_set, higher_set],
        category_config=None,
        stat_config=stat_config,
    )
    result_descending, _, is_set_descending = StackStage._process_category_modifiers(
        category_mods=[higher_set, lower_set],
        category_config=None,
        stat_config=stat_config,
    )
    assert result_ascending == 70.0
    assert result_descending == 70.0
    assert is_set_ascending is True
    assert is_set_descending is True


def test_process_category_modifiers_set_priority_beats_value() -> None:
    """Test SET value tie-break never overrides priority precedence."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    stat_config = config.get_stat_config(name="health")
    entity_id = EntityID(fake.uuid4())
    low_priority_low_value = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.SET,
        value=10.0,
        priority=ModifierPriority.LOW,
        source=fake.word(),
    )
    high_priority_high_value = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.SET,
        value=90.0,
        priority=ModifierPriority.CRITICAL,
        source=fake.word(),
    )
    result, _, is_set = StackStage._process_category_modifiers(
        category_mods=[high_priority_high_value, low_priority_low_value],
        category_config=None,
        stat_config=stat_config,
    )
    assert result == 10.0
    assert is_set is True


def test_process_category_modifiers_with_percentage_modifiers() -> None:
    """Test _process_category_modifiers with PERCENTAGE modifiers."""
    config = ModifierConfig()
    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    stat_config = config.get_stat_config(name="damage")
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.FLAT,
            value=100.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.PERCENTAGE,
            value=0.25,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.PERCENTAGE,
            value=0.15,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    result, multipliers, is_set = StackStage._process_category_modifiers(
        category_mods=modifiers, category_config=None, stat_config=stat_config
    )
    assert result == 140.0
    assert len(multipliers) == 0
    assert is_set is False


def test_process_category_modifiers_percentage_with_multiplier() -> None:
    """Test _process_category_modifiers with PERCENTAGE and MULTIPLIER."""
    config = ModifierConfig()
    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    stat_config = config.get_stat_config(name="damage")
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.FLAT,
            value=100.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.PERCENTAGE,
            value=0.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=2.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    result, multipliers, is_set = StackStage._process_category_modifiers(
        category_mods=modifiers, category_config=None, stat_config=stat_config
    )
    assert result == 300.0
    assert len(multipliers) == 0
    assert is_set is False


def test_process_category_modifiers_uses_category_stacking_rule() -> None:
    """Test _process_category_modifiers uses category stacking rule."""
    config = ModifierConfig()
    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    category_name = fake.word()
    config.register_category_stacking(
        category=category_name, stacking_rule=StackingRule.MULTIPLY
    )
    stat_config = config.get_stat_config(name="damage")
    category_config = config.get_category_stacking(category=category_name)
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_name,),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=2.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_name,),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=1.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_name,),
        ),
    ]
    result, multipliers, is_set = StackStage._process_category_modifiers(
        category_mods=modifiers,
        category_config=category_config,
        stat_config=stat_config,
    )
    assert result == 30.0
    assert len(multipliers) == 0
    assert is_set is False


def test_process_category_modifiers_falls_back_to_stat_rule() -> None:
    """Test _process_category_modifiers falls back to stat stacking rule."""
    config = ModifierConfig()
    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.MULTIPLY,
    )
    stat_config = config.get_stat_config(name="damage")
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=2.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=1.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        ),
    ]
    result, multipliers, is_set = StackStage._process_category_modifiers(
        category_mods=modifiers, category_config=None, stat_config=stat_config
    )
    assert result == 30.0
    assert len(multipliers) == 0
    assert is_set is False


def test_execute_stack_with_multiple_categories() -> None:
    """Test _execute_stack with multiple categories stacking independently."""
    stage = StackStage()
    config = ModifierConfig()
    config.register_stat(
        name="battery",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    category_drain = "drain"
    category_regen = "regen"
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="battery",
            modification_type=ModificationType.FLAT,
            value=-10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_drain,),
        ),
        Modifier(
            entity_id=entity_id,
            stat="battery",
            modification_type=ModificationType.FLAT,
            value=-5.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_drain,),
        ),
        Modifier(
            entity_id=entity_id,
            stat="battery",
            modification_type=ModificationType.FLAT,
            value=8.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_regen,),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "battery"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "battery")] == -7.0


def test_execute_stack_category_multipliers_applied_to_category_value() -> None:
    """Test _execute_stack applies multipliers to category contribution."""
    stage = StackStage()
    config = ModifierConfig()
    config.register_stat(
        name="battery",
        min_value=-100.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    category_drain = "drain"
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="battery",
            modification_type=ModificationType.FLAT,
            value=-10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_drain,),
        ),
        Modifier(
            entity_id=entity_id,
            stat="battery",
            modification_type=ModificationType.MULTIPLIER,
            value=0.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_drain,),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "battery"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "battery")] == 0.0


def test_execute_stack_multiplier_only_category_applied_to_base() -> None:
    """Test _execute_stack applies multiplier-only categories to base stat."""
    stage = StackStage()
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())

    def test_reader(entity_id: EntityID, stat: str, world: object) -> float:
        return 100.0

    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_value_reader(stat="damage", reader=test_reader)
    category_multiplier = "buff"
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=1.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_multiplier,),
        ),
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=0.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_multiplier,),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config, world=object())
    ctx.grouped = {(entity_id, "damage"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "damage")] == 200.0


def test_execute_stack_mixed_categories_with_multipliers() -> None:
    """Test _execute_stack with mix of additive and multiplier-only categories."""
    stage = StackStage()
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())

    def test_reader(entity_id: EntityID, stat: str, world: object) -> float:
        return 100.0

    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_value_reader(stat="damage", reader=test_reader)
    category_flat = "weapon"
    category_multiplier = "buff"
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.FLAT,
            value=50.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_flat,),
        ),
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=1.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_multiplier,),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config, world=object())
    ctx.grouped = {(entity_id, "damage"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "damage")] == 225.0


def test_execute_stack_category_specific_stacking_rules() -> None:
    """Test _execute_stack uses category-specific stacking rules."""
    stage = StackStage()
    config = ModifierConfig()
    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    category_name = fake.word()
    config.register_category_stacking(
        category=category_name, stacking_rule=StackingRule.MULTIPLY
    )
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_name,),
        ),
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=2.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_name,),
        ),
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=1.5,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_name,),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "damage"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "damage")] == 30.0


def test_execute_stack_multiple_categories_sum_contributions() -> None:
    """Test _execute_stack sums contributions from multiple categories."""
    stage = StackStage()
    config = ModifierConfig()
    config.register_stat(
        name="battery",
        min_value=-100.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    category_one = "drain_one"
    category_two = "drain_two"
    category_three = "regen"
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="battery",
            modification_type=ModificationType.FLAT,
            value=-10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_one,),
        ),
        Modifier(
            entity_id=entity_id,
            stat="battery",
            modification_type=ModificationType.FLAT,
            value=-5.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_two,),
        ),
        Modifier(
            entity_id=entity_id,
            stat="battery",
            modification_type=ModificationType.FLAT,
            value=20.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_three,),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "battery"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "battery")] == 5.0


def test_execute_stack_nullify_specific_drain_category() -> None:
    """Test _execute_stack allows equipment to nullify specific drain category."""
    stage = StackStage()
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())

    def test_reader(entity_id: EntityID, stat: str, world: object) -> float:
        return 100.0

    config.register_stat(
        name="battery",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_value_reader(stat="battery", reader=test_reader)
    category_drain_shields = "shields"
    category_drain_weapons = "weapons"
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="battery",
            modification_type=ModificationType.FLAT,
            value=-10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_drain_shields,),
        ),
        Modifier(
            entity_id=entity_id,
            stat="battery",
            modification_type=ModificationType.MULTIPLIER,
            value=0.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_drain_shields,),
        ),
        Modifier(
            entity_id=entity_id,
            stat="battery",
            modification_type=ModificationType.FLAT,
            value=-5.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_drain_weapons,),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config, world=object())
    ctx.grouped = {(entity_id, "battery"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "battery")] == 95.0


def test_collect_stage_with_profiling_enabled() -> None:
    """Test CollectStage executes with profiling enabled."""
    stage = CollectStage(profiling_enabled=True)
    config = ModifierConfig()
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=1.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        )
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result is ctx


def test_filter_stage_with_profiling_enabled() -> None:
    """Test FilterStage executes with profiling enabled."""
    stage = FilterStage(profiling_enabled=True)
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="health",
            modification_type=ModificationType.FLAT,
            value=1.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        )
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert len(result.modifiers) == 1


def test_sort_stage_with_profiling_enabled() -> None:
    """Test SortStage executes with profiling enabled."""
    stage = SortStage(profiling_enabled=True)
    config = ModifierConfig()
    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=1.0,
            priority=ModifierPriority.LOW,
            source=fake.word(),
        ),
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=2.0,
            priority=ModifierPriority.HIGH,
            source=fake.word(),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.modifiers[0].priority == ModifierPriority.HIGH


def test_group_stage_with_profiling_enabled() -> None:
    """Test GroupStage executes with profiling enabled."""
    stage = GroupStage(profiling_enabled=True)
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="health",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        )
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert len(result.grouped) == 1


def test_stack_stage_with_profiling_enabled() -> None:
    """Test StackStage executes with profiling enabled."""
    stage = StackStage(profiling_enabled=True)
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="health",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        )
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "health"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "health")] == 10.0


def test_clamp_stage_with_profiling_enabled() -> None:
    """Test ClampStage executes with profiling enabled."""
    stage = ClampStage(profiling_enabled=True)
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    entity_id = EntityID(fake.uuid4())
    ctx = ModifierContext(modifiers=[], config=config)
    ctx.final_values = {(entity_id, "health"): 150.0}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "health")] == 100.0


def test_apply_stage_with_profiling_enabled() -> None:
    """Test ApplyStage executes with profiling enabled."""
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())
    stat = "health"
    applied_values = {}

    def test_applicator(
        entity_id: EntityID, stat: str, value: float, world: object
    ) -> None:
        applied_values[(entity_id, stat)] = value

    config.register_stat(
        name=stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_applicator(stat=stat, applicator=test_applicator)
    ctx = ModifierContext(modifiers=[], config=config, world=object())
    ctx.final_values = {(entity_id, stat): 75.0}
    pipe_ctx = PipelineContext()
    stage = ApplyStage(profiling_enabled=True)
    stage.process(value=ctx, context=pipe_ctx)
    assert (entity_id, stat) in applied_values


def test_group_by_category_with_modifier_in_multiple_categories() -> None:
    """Test _group_by_category includes modifier in all its categories."""
    category_one = fake.unique.word()
    category_two = fake.unique.word()
    category_three = fake.unique.word()
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(category_one, category_two, category_three),
    )
    result = StackStage._group_by_category(modifiers=[modifier])
    assert len(result) == 3
    assert category_one in result
    assert category_two in result
    assert category_three in result
    assert result[category_one][0] is modifier
    assert result[category_two][0] is modifier
    assert result[category_three][0] is modifier


def test_group_by_category_multi_category_with_other_modifiers() -> None:
    """Test multi-category modifier groups with other single-category modifiers."""
    category_one = fake.unique.word()
    category_two = fake.unique.word()
    multi_modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(category_one, category_two),
    )
    single_modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(category_one,),
    )
    result = StackStage._group_by_category(modifiers=[multi_modifier, single_modifier])
    assert len(result) == 2
    assert len(result[category_one]) == 2
    assert len(result[category_two]) == 1
    assert multi_modifier in result[category_one]
    assert single_modifier in result[category_one]
    assert multi_modifier in result[category_two]


def test_execute_stack_multi_category_modifier_contributes_to_all_groups() -> None:
    """Test multi-category modifier contributes value to all its category groups."""
    stage = StackStage()
    config = ModifierConfig()
    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    category_one = fake.unique.word()
    category_two = fake.unique.word()
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_one, category_two),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "damage"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "damage")] == 20.0


def test_execute_stack_multi_category_with_category_specific_stacking() -> None:
    """Test multi-category modifier uses category-specific stacking rules."""
    stage = StackStage()
    config = ModifierConfig()
    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    category_multiply = f"multiply_{fake.pystr(min_chars=10, max_chars=15)}"
    category_add = f"add_{fake.pystr(min_chars=10, max_chars=15)}"
    config.register_category_stacking(
        category=category_multiply,
        stacking_rule=StackingRule.MULTIPLY,
    )
    entity_id = EntityID(fake.uuid4())
    modifiers = [
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_multiply, category_add),
        ),
        Modifier(
            entity_id=entity_id,
            stat="damage",
            modification_type=ModificationType.MULTIPLIER,
            value=2.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
            categories=(category_multiply,),
        ),
    ]
    ctx = ModifierContext(modifiers=modifiers, config=config)
    ctx.grouped = {(entity_id, "damage"): modifiers}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "damage")] == 30.0


def test_intercept_stage_creation() -> None:
    """Test InterceptStage can be instantiated."""
    stage = InterceptStage()
    assert stage is not None


def test_intercept_stage_has_name() -> None:
    """Test intercept stage has name."""
    stage = InterceptStage()
    assert stage.name == "intercept"


def test_intercept_stage_returns_context_when_no_world() -> None:
    """Test intercept stage returns context unchanged when no world."""
    stage = InterceptStage()
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())
    ctx = ModifierContext(modifiers=[], config=config, world=None)
    ctx.final_values = {(entity_id, "health"): 100.0}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, "health")] == 100.0


def test_intercept_stage_invokes_interceptor() -> None:
    """Test intercept stage invokes registered interceptor."""
    stage = InterceptStage()
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())
    stat_name = fake.word()
    intercepted_value: float = fake.pyfloat(min_value=1.0, max_value=100.0)
    invocation_tracker = []

    def test_interceptor(
        entity_id: EntityID, stat: str, value: float, context: ModifierContext
    ) -> float:
        invocation_tracker.append((entity_id, stat, value))
        return intercepted_value

    config.register_interceptor(stat=stat_name, interceptor=test_interceptor)
    world = object()
    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(entity_id, stat_name): 50.0}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, stat_name)] == intercepted_value
    assert len(invocation_tracker) == 1
    assert invocation_tracker[0] == (entity_id, stat_name, 50.0)


def test_intercept_stage_skips_when_no_interceptor() -> None:
    """Test intercept stage passes value through when no interceptor registered."""
    stage = InterceptStage()
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())
    stat_name = fake.word()
    original_value = fake.pyfloat(min_value=1.0, max_value=100.0)
    world = object()
    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(entity_id, stat_name): original_value}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, stat_name)] == original_value


def test_intercept_stage_processes_multiple_stats() -> None:
    """Test intercept stage processes multiple entity stats."""
    stage = InterceptStage()
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())
    stat1 = fake.word()
    stat2 = fake.word()

    def interceptor1(
        entity_id: EntityID, stat: str, value: float, context: ModifierContext
    ) -> float:
        return value * 2

    def interceptor2(
        entity_id: EntityID, stat: str, value: float, context: ModifierContext
    ) -> float:
        return value + 10

    config.register_interceptor(stat=stat1, interceptor=interceptor1)
    config.register_interceptor(stat=stat2, interceptor=interceptor2)
    world = object()
    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(entity_id, stat1): 5.0, (entity_id, stat2): 20.0}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, stat1)] == 10.0
    assert result.final_values[(entity_id, stat2)] == 30.0


def test_intercept_stage_with_profiling_enabled() -> None:
    """Test intercept stage with profiling enabled."""
    stage = InterceptStage(profiling_enabled=True)
    config = ModifierConfig()
    entity_id = EntityID(fake.uuid4())
    stat_name = fake.word()

    def test_interceptor(
        entity_id: EntityID, stat: str, value: float, context: ModifierContext
    ) -> float:
        return value * 2

    config.register_interceptor(stat=stat_name, interceptor=test_interceptor)
    world = object()
    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(entity_id, stat_name): 50.0}
    pipe_ctx = PipelineContext()
    result = stage.process(value=ctx, context=pipe_ctx)
    assert result.final_values[(entity_id, stat_name)] == 100.0

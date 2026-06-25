"""Tests for modifier pipeline."""

from faker import Faker

from yuna.modifiers.config import (
    ModifierConfig,
    StackingRule,
)
from yuna.modifiers.context import ModifierContext
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.modifiers.types import (
    ModificationType,
    ModifierPriority,
    ModifierStage,
)
from yuna.pipeline.context import PipelineContext
from yuna.pipeline.stage import PipelineStage
from yuna.types.identifiers import EntityID

fake = Faker()


def test_modifier_pipeline_creation() -> None:
    """Test ModifierPipeline can be instantiated."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    assert pipeline is not None


def test_queue_modifier() -> None:
    """Test queuing a modifier."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    pipeline.queue_modifier(modifier=modifier)
    assert pipeline.get_queue_size() == 1


def test_queue_multiple_modifiers() -> None:
    """Test queuing multiple modifiers."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    for _ in range(5):
        modifier = Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=1.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        )
        pipeline.queue_modifier(modifier=modifier)
    assert pipeline.get_queue_size() == 5


def test_process_empty_queue() -> None:
    """Test processing empty queue returns empty dict."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    result = pipeline.process()
    assert result == {}


def test_process_clears_queue() -> None:
    """Test process clears queue after execution."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat="health",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    pipeline.queue_modifier(modifier=modifier)
    pipeline.process()
    assert pipeline.get_queue_size() == 0


def test_process_single_modifier() -> None:
    """Test processing single modifier."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    entity_id = EntityID(fake.uuid4())
    modifier = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    pipeline.queue_modifier(modifier=modifier)
    result = pipeline.process()
    assert result[(entity_id, "health")] == 10.0


def test_process_multiple_modifiers_same_stat() -> None:
    """Test processing multiple modifiers for same stat."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    entity_id = EntityID(fake.uuid4())
    modifier_1 = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    modifier_2 = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    pipeline.queue_modifier(modifier=modifier_1)
    pipeline.queue_modifier(modifier=modifier_2)
    result = pipeline.process()
    assert result[(entity_id, "health")] == 15.0


def test_process_filters_invalid_stats() -> None:
    """Test process filters out modifiers for unregistered stats."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    entity_id = EntityID(fake.uuid4())
    valid_modifier = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    invalid_modifier = Modifier(
        entity_id=entity_id,
        stat="invalid_stat",
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    pipeline.queue_modifier(modifier=valid_modifier)
    pipeline.queue_modifier(modifier=invalid_modifier)
    result = pipeline.process()
    assert result[(entity_id, "health")] == 10.0
    assert len(result) == 1


def test_process_clamps_to_max() -> None:
    """Test process clamps final value to maximum."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    entity_id = EntityID(fake.uuid4())
    modifier = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=150.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    pipeline.queue_modifier(modifier=modifier)
    result = pipeline.process()
    assert result[(entity_id, "health")] == 100.0


def test_process_clamps_to_min() -> None:
    """Test process clamps final value to minimum."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    entity_id = EntityID(fake.uuid4())
    modifier = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=-50.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    pipeline.queue_modifier(modifier=modifier)
    result = pipeline.process()
    assert result[(entity_id, "health")] == 0.0


def test_process_sorts_by_priority() -> None:
    """Test process respects priority ordering."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    entity_id = EntityID(fake.uuid4())
    low_priority = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.SET,
        value=50.0,
        priority=ModifierPriority.LOW,
        source=fake.word(),
    )
    high_priority = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.SET,
        value=75.0,
        priority=ModifierPriority.CRITICAL,
        source=fake.word(),
    )
    pipeline.queue_modifier(modifier=low_priority)
    pipeline.queue_modifier(modifier=high_priority)
    result = pipeline.process()
    assert result[(entity_id, "health")] == 50.0


def test_clear_queue() -> None:
    """Test clearing queue without processing."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    for _ in range(3):
        modifier = Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat=fake.word(),
            modification_type=ModificationType.FLAT,
            value=1.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        )
        pipeline.queue_modifier(modifier=modifier)
    pipeline.clear_queue()
    assert pipeline.get_queue_size() == 0


def test_get_queue_size() -> None:
    """Test getting queue size."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    assert pipeline.get_queue_size() == 0
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    pipeline.queue_modifier(modifier=modifier)
    assert pipeline.get_queue_size() == 1


def test_process_with_multipliers() -> None:
    """Test processing modifiers with multipliers."""
    config = ModifierConfig()
    config.register_stat(
        name="damage",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.MULTIPLY,
    )
    pipeline = ModifierPipeline(config=config)
    entity_id = EntityID(fake.uuid4())
    flat_mod = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    mult_mod = Modifier(
        entity_id=entity_id,
        stat="damage",
        modification_type=ModificationType.MULTIPLIER,
        value=2.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    pipeline.queue_modifier(modifier=flat_mod)
    pipeline.queue_modifier(modifier=mult_mod)
    result = pipeline.process()
    assert result[(entity_id, "damage")] == 20.0


def test_process_multiple_entities() -> None:
    """Test processing modifiers for multiple entities."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    entity_1 = EntityID(fake.uuid4())
    entity_2 = EntityID(fake.uuid4())
    modifier_1 = Modifier(
        entity_id=entity_1,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    modifier_2 = Modifier(
        entity_id=entity_2,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    pipeline.queue_modifier(modifier=modifier_1)
    pipeline.queue_modifier(modifier=modifier_2)
    result = pipeline.process()
    assert result[(entity_1, "health")] == 10.0
    assert result[(entity_2, "health")] == 20.0


def test_process_multiple_times() -> None:
    """Test pipeline can process multiple batches."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    entity_id = EntityID(fake.uuid4())
    modifier_1 = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    pipeline.queue_modifier(modifier=modifier_1)
    result_1 = pipeline.process()
    assert result_1[(entity_id, "health")] == 10.0
    modifier_2 = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    pipeline.queue_modifier(modifier=modifier_2)
    result_2 = pipeline.process()
    assert result_2[(entity_id, "health")] == 5.0


def test_process_with_duration_ticks() -> None:
    """Test processing modifiers with duration tracking."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    entity_id = EntityID(fake.uuid4())
    modifier = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        duration_ticks=50,
    )
    pipeline.queue_modifier(modifier=modifier)
    result = pipeline.process(current_tick=100)
    assert result[(entity_id, "health")] == 10.0
    assert pipeline.tracker.get_tracked_count() == 1


def test_tracker_property() -> None:
    """Test accessing tracker property."""
    config = ModifierConfig()
    pipeline = ModifierPipeline(config=config)
    tracker = pipeline.tracker
    assert tracker is not None
    assert tracker.get_tracked_count() == 0


def test_config_property() -> None:
    """Test accessing config property."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    pipeline_config = pipeline.config
    assert pipeline_config is config
    assert pipeline_config.has_stat(name="health")


class TestStage(PipelineStage[ModifierContext, ModifierContext, PipelineContext]):
    """Test stage for insertion tests."""

    def __init__(self, stage_name: str) -> None:
        self._stage_name = stage_name
        self.process_count = 0

    @property
    def name(self) -> str:
        return self._stage_name

    def process(
        self,
        value: ModifierContext,
        context: PipelineContext,
    ) -> ModifierContext:
        self.process_count += 1
        return value


def test_insert_stage_before() -> None:
    """Test inserting custom stage before named stage."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    custom_stage = TestStage(stage_name="custom_before_clamp")

    pipeline.insert_stage_before(before=ModifierStage.CLAMP, stage=custom_stage)

    entity_id = EntityID(fake.uuid4())
    pipeline.queue_modifier(
        modifier=Modifier(
            entity_id=entity_id,
            stat="health",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source="test",
        )
    )
    pipeline.process(world=None, current_tick=0)

    assert custom_stage.process_count == 1


def test_insert_stage_after() -> None:
    """Test inserting custom stage after named stage."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    custom_stage = TestStage(stage_name="custom_after_stack")

    pipeline.insert_stage_after(after=ModifierStage.STACK, stage=custom_stage)

    entity_id = EntityID(fake.uuid4())
    pipeline.queue_modifier(
        modifier=Modifier(
            entity_id=entity_id,
            stat="health",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source="test",
        )
    )
    pipeline.process(world=None, current_tick=0)

    assert custom_stage.process_count == 1

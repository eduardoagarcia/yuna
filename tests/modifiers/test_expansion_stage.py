"""Tests for ExpansionStage pipeline stage."""

from unittest.mock import Mock

from faker import Faker

from yuna.modifiers.config import ModifierConfig
from yuna.modifiers.context import ModifierContext
from yuna.modifiers.modifier import Modifier, StatEffect
from yuna.modifiers.stages import ExpansionStage
from yuna.modifiers.types import (
    ModificationType,
    ModifierPriority,
)
from yuna.pipeline.context import PipelineContext
from yuna.types.identifiers import EntityID

fake = Faker()


def test_expansion_stage_has_name() -> None:
    """Test ExpansionStage has correct name."""
    stage = ExpansionStage()
    assert stage.name == "expansion"


def test_expansion_stage_passes_through_modifiers_without_effects() -> None:
    """Test stage passes modifiers with no secondary effects or cascades."""
    entity_id = EntityID(fake.uuid4())
    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    config = ModifierConfig()
    context = ModifierContext(modifiers=[modifier], config=config, world=None)
    pipe_context = PipelineContext()

    stage = ExpansionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] == modifier


def test_expansion_stage_expands_secondary_effects() -> None:
    """Test stage expands modifiers with secondary effects."""
    entity_id = EntityID(fake.uuid4())
    stat1 = fake.word()
    stat2 = fake.word()

    secondary_effect = StatEffect(
        stat=stat2,
        value=5.0,
        modification_type=ModificationType.PERCENTAGE,
    )

    modifier = Modifier(
        entity_id=entity_id,
        stat=stat1,
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source="test_source",
        secondary_effects=(secondary_effect,),
    )

    config = ModifierConfig()
    context = ModifierContext(modifiers=[modifier], config=config, world=None)
    pipe_context = PipelineContext()

    stage = ExpansionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 2
    assert result.modifiers[0] == modifier
    assert result.modifiers[1].stat == stat2
    assert result.modifiers[1].value == 5.0
    assert result.modifiers[1].modification_type == ModificationType.PERCENTAGE


def test_expansion_stage_creates_secondary_with_correct_attributes() -> None:
    """Test secondary modifiers inherit attributes from primary."""
    entity_id = EntityID(fake.uuid4())
    source = fake.word()
    tags = frozenset({fake.word(), fake.word()})
    categories = (fake.word(), fake.word())

    secondary_effect = StatEffect(
        stat=fake.word(),
        value=5.0,
        modification_type=ModificationType.FLAT,
    )

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.HIGH,
        source=source,
        duration_ticks=100,
        tags=tags,
        categories=categories,
        secondary_effects=(secondary_effect,),
    )

    config = ModifierConfig()
    context = ModifierContext(modifiers=[modifier], config=config, world=None)
    pipe_context = PipelineContext()

    stage = ExpansionStage()
    result = stage.process(value=context, context=pipe_context)

    secondary = result.modifiers[1]
    assert secondary.entity_id == entity_id
    assert secondary.priority == ModifierPriority.HIGH
    assert secondary.source == f"{source}:secondary"
    assert secondary.duration_ticks == 100
    assert secondary.tags == tags
    assert secondary.categories == categories


def test_expansion_stage_expands_multiple_secondary_effects() -> None:
    """Test stage expands multiple secondary effects."""
    entity_id = EntityID(fake.uuid4())

    effect1 = StatEffect(
        stat=fake.word(),
        value=5.0,
        modification_type=ModificationType.FLAT,
    )
    effect2 = StatEffect(
        stat=fake.word(),
        value=10.0,
        modification_type=ModificationType.PERCENTAGE,
    )

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        secondary_effects=(effect1, effect2),
    )

    config = ModifierConfig()
    context = ModifierContext(modifiers=[modifier], config=config, world=None)
    pipe_context = PipelineContext()

    stage = ExpansionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 3
    assert result.modifiers[0] == modifier
    assert result.modifiers[1].value == 5.0
    assert result.modifiers[2].value == 10.0


def test_expansion_stage_applies_scaling_from_stat_value() -> None:
    """Test stage scales secondary effect value based on source stat."""
    entity_id = EntityID(fake.uuid4())
    source_stat = fake.word()
    source_value = 100.0
    scaling_factor = 0.15

    world = Mock()
    world.get_stat.return_value = source_value

    secondary_effect = StatEffect(
        stat=fake.word(),
        value=0.0,
        modification_type=ModificationType.FLAT,
        scaling_stat=source_stat,
        scaling_factor=scaling_factor,
    )

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        secondary_effects=(secondary_effect,),
    )

    config = ModifierConfig()
    context = ModifierContext(modifiers=[modifier], config=config, world=world)
    pipe_context = PipelineContext()

    stage = ExpansionStage()
    result = stage.process(value=context, context=pipe_context)

    secondary = result.modifiers[1]
    expected_value = source_value * scaling_factor
    assert secondary.value == expected_value
    world.get_stat.assert_called_once_with(entity_id=entity_id, stat=source_stat)


def test_expansion_stage_combines_base_value_and_scaling() -> None:
    """Test stage combines base value with scaled value."""
    entity_id = EntityID(fake.uuid4())
    base_value = 5.0
    source_value = 100.0
    scaling_factor = 0.10

    world = Mock()
    world.get_stat.return_value = source_value

    secondary_effect = StatEffect(
        stat=fake.word(),
        value=base_value,
        modification_type=ModificationType.FLAT,
        scaling_stat=fake.word(),
        scaling_factor=scaling_factor,
    )

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        secondary_effects=(secondary_effect,),
    )

    config = ModifierConfig()
    context = ModifierContext(modifiers=[modifier], config=config, world=world)
    pipe_context = PipelineContext()

    stage = ExpansionStage()
    result = stage.process(value=context, context=pipe_context)

    secondary = result.modifiers[1]
    expected_value = base_value + (source_value * scaling_factor)
    assert secondary.value == expected_value


def test_expansion_stage_skips_scaling_when_no_world() -> None:
    """Test stage uses only base value when world not available."""
    entity_id = EntityID(fake.uuid4())
    base_value = 5.0

    secondary_effect = StatEffect(
        stat=fake.word(),
        value=base_value,
        modification_type=ModificationType.FLAT,
        scaling_stat=fake.word(),
        scaling_factor=0.5,
    )

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        secondary_effects=(secondary_effect,),
    )

    config = ModifierConfig()
    context = ModifierContext(modifiers=[modifier], config=config, world=None)
    pipe_context = PipelineContext()

    stage = ExpansionStage()
    result = stage.process(value=context, context=pipe_context)

    secondary = result.modifiers[1]
    assert secondary.value == base_value


def test_expansion_stage_injects_cascade_modifiers() -> None:
    """Test stage injects cascade modifiers."""
    entity_id = EntityID(fake.uuid4())

    cascade_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.PERCENTAGE,
        value=15.0,
        priority=ModifierPriority.HIGH,
        source="cascade_source",
    )

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        cascade_modifiers=(cascade_modifier,),
    )

    config = ModifierConfig()
    context = ModifierContext(modifiers=[modifier], config=config, world=None)
    pipe_context = PipelineContext()

    stage = ExpansionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 2
    assert result.modifiers[0] == modifier
    assert result.modifiers[1] == cascade_modifier


def test_expansion_stage_injects_multiple_cascade_modifiers() -> None:
    """Test stage injects multiple cascade modifiers."""
    entity_id = EntityID(fake.uuid4())

    cascade1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source="cascade1",
    )
    cascade2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source="cascade2",
    )

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        cascade_modifiers=(cascade1, cascade2),
    )

    config = ModifierConfig()
    context = ModifierContext(modifiers=[modifier], config=config, world=None)
    pipe_context = PipelineContext()

    stage = ExpansionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 3
    assert result.modifiers[0] == modifier
    assert result.modifiers[1] == cascade1
    assert result.modifiers[2] == cascade2


def test_expansion_stage_expands_both_effects_and_cascades() -> None:
    """Test stage expands both secondary effects and cascade modifiers."""
    entity_id = EntityID(fake.uuid4())

    secondary_effect = StatEffect(
        stat=fake.word(),
        value=5.0,
        modification_type=ModificationType.FLAT,
    )

    cascade_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=15.0,
        priority=ModifierPriority.NORMAL,
        source="cascade",
    )

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        secondary_effects=(secondary_effect,),
        cascade_modifiers=(cascade_modifier,),
    )

    config = ModifierConfig()
    context = ModifierContext(modifiers=[modifier], config=config, world=None)
    pipe_context = PipelineContext()

    stage = ExpansionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 3
    assert result.modifiers[0] == modifier
    assert result.modifiers[1].source.endswith(":secondary")
    assert result.modifiers[2].source == "cascade"


def test_expansion_stage_processes_multiple_modifiers() -> None:
    """Test stage processes multiple modifiers with effects."""
    entity_id = EntityID(fake.uuid4())

    effect1 = StatEffect(
        stat=fake.word(),
        value=5.0,
        modification_type=ModificationType.FLAT,
    )
    effect2 = StatEffect(
        stat=fake.word(),
        value=10.0,
        modification_type=ModificationType.FLAT,
    )

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        secondary_effects=(effect1,),
    )
    modifier2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        secondary_effects=(effect2,),
    )

    config = ModifierConfig()
    context = ModifierContext(
        modifiers=[modifier1, modifier2], config=config, world=None
    )
    pipe_context = PipelineContext()

    stage = ExpansionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 4
    assert result.modifiers[0] == modifier1
    assert result.modifiers[1].value == 5.0
    assert result.modifiers[2] == modifier2
    assert result.modifiers[3].value == 10.0

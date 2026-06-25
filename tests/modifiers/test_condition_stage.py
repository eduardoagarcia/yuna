"""Tests for ConditionStage."""

from unittest.mock import Mock

from faker import Faker

from yuna.modifiers.conditions import Conditions
from yuna.modifiers.config import ModifierConfig, StackingRule
from yuna.modifiers.context import ModifierContext
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.stages import ConditionStage
from yuna.modifiers.types import (
    ModificationType,
    ModifierPriority,
)
from yuna.pipeline.context import PipelineContext
from yuna.types.identifiers import EntityID

fake = Faker()


def test_condition_stage_has_name() -> None:
    """Test ConditionStage has correct name."""
    stage = ConditionStage()
    assert stage.name == "condition"


def test_condition_stage_passes_through_modifiers_without_conditions() -> None:
    """Test stage passes modifiers with no conditions."""
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
    config.register_stat(
        name=modifier.stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    context = ModifierContext(modifiers=[modifier], config=config, world=None)
    pipe_context = PipelineContext()

    stage = ConditionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] == modifier


def test_condition_stage_filters_when_activation_condition_fails() -> None:
    """Test stage filters modifier when activation condition returns False."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 30.0

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        activation_condition=Conditions.stat_above("health", 50.0),
    )

    config = ModifierConfig()
    config.register_stat(
        name=modifier.stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    context = ModifierContext(modifiers=[modifier], config=config, world=world)
    pipe_context = PipelineContext()

    stage = ConditionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 0


def test_condition_stage_keeps_modifier_when_activation_condition_succeeds() -> None:
    """Test stage keeps modifier when activation condition returns True."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 75.0

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        activation_condition=Conditions.stat_above("health", 50.0),
    )

    config = ModifierConfig()
    config.register_stat(
        name=modifier.stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    context = ModifierContext(modifiers=[modifier], config=config, world=world)
    pipe_context = PipelineContext()

    stage = ConditionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] == modifier


def test_condition_stage_filters_when_deactivation_condition_succeeds() -> None:
    """Test stage filters modifier when deactivation condition returns True."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_entity_tags.return_value = frozenset({"disabled"})

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        deactivation_condition=Conditions.has_tag("disabled"),
    )

    config = ModifierConfig()
    config.register_stat(
        name=modifier.stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    context = ModifierContext(modifiers=[modifier], config=config, world=world)
    pipe_context = PipelineContext()

    stage = ConditionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 0


def test_condition_stage_keeps_modifier_when_deactivation_condition_fails() -> None:
    """Test stage keeps modifier when deactivation condition returns False."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_entity_tags.return_value = frozenset({"active"})

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        deactivation_condition=Conditions.has_tag("disabled"),
    )

    config = ModifierConfig()
    config.register_stat(
        name=modifier.stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    context = ModifierContext(modifiers=[modifier], config=config, world=world)
    pipe_context = PipelineContext()

    stage = ConditionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] == modifier


def test_condition_stage_with_both_conditions() -> None:
    """Test stage with both activation and deactivation conditions."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 75.0
    world.get_entity_tags.return_value = frozenset({"active"})

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        activation_condition=Conditions.stat_above("health", 50.0),
        deactivation_condition=Conditions.has_tag("disabled"),
    )

    config = ModifierConfig()
    config.register_stat(
        name=modifier.stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    context = ModifierContext(modifiers=[modifier], config=config, world=world)
    pipe_context = PipelineContext()

    stage = ConditionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1


def test_condition_stage_filters_when_activation_passes_but_deactivation_fails() -> (
    None
):
    """Test stage filters when activation passes but deactivation triggers."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 75.0
    world.get_entity_tags.return_value = frozenset({"disabled"})

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        activation_condition=Conditions.stat_above("health", 50.0),
        deactivation_condition=Conditions.has_tag("disabled"),
    )

    config = ModifierConfig()
    config.register_stat(
        name=modifier.stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    context = ModifierContext(modifiers=[modifier], config=config, world=world)
    pipe_context = PipelineContext()

    stage = ConditionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 0


def test_condition_stage_sets_entity_id_on_context_during_evaluation() -> None:
    """Test stage sets entity_id on context for condition evaluation."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 75.0

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        activation_condition=Conditions.stat_above("health", 50.0),
    )

    config = ModifierConfig()
    config.register_stat(
        name=modifier.stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    context = ModifierContext(modifiers=[modifier], config=config, world=world)
    pipe_context = PipelineContext()

    stage = ConditionStage()
    result = stage.process(value=context, context=pipe_context)

    world.get_stat.assert_called_once_with(entity_id=entity_id, stat="health")
    assert result.entity_id is None


def test_condition_stage_processes_multiple_modifiers() -> None:
    """Test stage processes multiple modifiers correctly."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()

    modifier_active = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        activation_condition=Conditions.stat_above("health", 50.0),
    )

    modifier_inactive = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        activation_condition=Conditions.stat_above("energy", 50.0),
    )

    modifier_no_condition = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=15.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    config = ModifierConfig()
    config.register_stat(
        name=modifier_active.stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_stat(
        name=modifier_inactive.stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    config.register_stat(
        name=modifier_no_condition.stat,
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    def get_stat_side_effect(entity_id: EntityID, stat: str) -> float:
        if stat == "health":
            return 75.0
        elif stat == "energy":
            return 30.0
        return 0.0

    world.get_stat.side_effect = get_stat_side_effect

    context = ModifierContext(
        modifiers=[modifier_active, modifier_inactive, modifier_no_condition],
        config=config,
        world=world,
    )
    pipe_context = PipelineContext()

    stage = ConditionStage()
    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 2
    assert modifier_active in result.modifiers
    assert modifier_no_condition in result.modifiers
    assert modifier_inactive not in result.modifiers

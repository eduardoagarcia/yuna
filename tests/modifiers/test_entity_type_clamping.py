"""Tests for entity-type specific clamping via ConfigNamespaceComponent."""

from faker import Faker

from yuna.config.component import ConfigNamespaceComponent
from yuna.config.schema import ConfigSchema
from yuna.config.types import ConfigConstraints
from yuna.ecs.world import ECSWorld
from yuna.modifiers.config import (
    ModifierConfig,
    StackingRule,
)
from yuna.modifiers.context import ModifierContext
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.modifiers.stages import ClampStage
from yuna.pipeline.context import PipelineContext
from yuna.spatial.collision import CollisionMode
from yuna.spatial.grid import SpatialGrid
from yuna.spatial.integration import SpatialSystem
from yuna.state.manager import StateManager
from yuna.state.serializer import SnapshotSerializer
from yuna.types.identifiers import EntityID

fake = Faker()


def create_test_world() -> ECSWorld:
    """Create test world with bot and deployable temperature configs."""
    schema = ConfigSchema()

    schema.define(
        key="bot.temperature",
        value_type=float,
        value=0.1,
        constraints=ConfigConstraints(min_value=0.1, max_value=1.0),
    )
    schema.define(
        key="deployment.deployable.temperature",
        value_type=float,
        value=0.05,
        constraints=ConfigConstraints(min_value=0.05, max_value=1.0),
    )
    schema.define(
        key="bot.health",
        value_type=float,
        value=1.0,
        constraints=ConfigConstraints(min_value=0.0, max_value=1.0),
    )
    schema.define(
        key="deployment.deployable.health",
        value_type=float,
        value=1.0,
        constraints=ConfigConstraints(min_value=0.0, max_value=1.0),
    )
    schema.define(
        key="bot.battery",
        value_type=float,
        value=1.0,
        constraints=ConfigConstraints(min_value=0.0, max_value=1.0),
    )
    schema.define(
        key="deployment.deployable.battery",
        value_type=float,
        value=1.0,
        constraints=ConfigConstraints(min_value=0.0, max_value=1.0),
    )

    modifier_pipeline = ModifierPipeline(config=ModifierConfig())
    state_manager = StateManager(serializer=SnapshotSerializer())
    spatial_grid = SpatialGrid(cell_size=10)

    world = ECSWorld(
        config_schema=schema,
        state_manager=state_manager,
        modifier_pipeline=modifier_pipeline,
        spatial_grid=spatial_grid,
    )

    spatial_system = SpatialSystem(
        cell_size=10,
        collision_mode=CollisionMode.GRID_BOX,
    )
    world.register_system(system=spatial_system)

    return world


def test_clamp_bot_temperature_to_bot_minimum() -> None:
    """Test bot temperature is clamped to 0.1 not 0.0."""
    world = create_test_world()
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="temperature",
        min_value=0.0,
        max_value=1.0,
        stacking_rule=StackingRule.ADD,
    )

    bot_id = world.create_entity()
    world.add_component(
        entity_id=bot_id,
        component=ConfigNamespaceComponent(namespace="bot"),
    )

    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(bot_id, "temperature"): -0.25}
    pipe_ctx = PipelineContext()

    result = stage.process(value=ctx, context=pipe_ctx)

    assert result.final_values[(bot_id, "temperature")] == 0.1


def test_clamp_deployable_temperature_to_deployable_minimum() -> None:
    """Test deployable temperature is clamped to 0.05 not 0.1."""
    world = create_test_world()
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="temperature",
        min_value=0.0,
        max_value=1.0,
        stacking_rule=StackingRule.ADD,
    )

    deployable_id = world.create_entity()
    world.add_component(
        entity_id=deployable_id,
        component=ConfigNamespaceComponent(namespace="deployment.deployable"),
    )

    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(deployable_id, "temperature"): -0.25}
    pipe_ctx = PipelineContext()

    result = stage.process(value=ctx, context=pipe_ctx)

    assert result.final_values[(deployable_id, "temperature")] == 0.05


def test_clamp_bot_negative_temperature_to_minimum() -> None:
    """Test negative bot temperature values are clamped to 0.1."""
    world = create_test_world()
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="temperature",
        min_value=0.0,
        max_value=1.0,
        stacking_rule=StackingRule.ADD,
    )

    bot_id = world.create_entity()
    world.add_component(
        entity_id=bot_id,
        component=ConfigNamespaceComponent(namespace="bot"),
    )

    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(bot_id, "temperature"): -10.0}
    pipe_ctx = PipelineContext()

    result = stage.process(value=ctx, context=pipe_ctx)

    assert result.final_values[(bot_id, "temperature")] == 0.1


def test_clamp_deployable_temperature_preserves_valid_value() -> None:
    """Test deployable temperature at 0.05 is preserved."""
    world = create_test_world()
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="temperature",
        min_value=0.0,
        max_value=1.0,
        stacking_rule=StackingRule.ADD,
    )

    deployable_id = world.create_entity()
    world.add_component(
        entity_id=deployable_id,
        component=ConfigNamespaceComponent(namespace="deployment.deployable"),
    )

    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(deployable_id, "temperature"): 0.05}
    pipe_ctx = PipelineContext()

    result = stage.process(value=ctx, context=pipe_ctx)

    assert result.final_values[(deployable_id, "temperature")] == 0.05


def test_clamp_unknown_entity_type_uses_stat_config_bounds() -> None:
    """Test unknown entity types fall back to stat_config bounds."""
    world = create_test_world()
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="temperature",
        min_value=0.0,
        max_value=1.0,
        stacking_rule=StackingRule.ADD,
    )

    entity_id = world.create_entity()

    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(entity_id, "temperature"): -0.25}
    pipe_ctx = PipelineContext()

    result = stage.process(value=ctx, context=pipe_ctx)

    assert result.final_values[(entity_id, "temperature")] == 0.0


def test_clamp_bot_health_works_normally() -> None:
    """Test bot health clamping works normally with same bounds."""
    world = create_test_world()
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=1.0,
        stacking_rule=StackingRule.ADD,
    )

    bot_id = world.create_entity()
    world.add_component(
        entity_id=bot_id,
        component=ConfigNamespaceComponent(namespace="bot"),
    )

    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(bot_id, "health"): -0.5}
    pipe_ctx = PipelineContext()

    result = stage.process(value=ctx, context=pipe_ctx)

    assert result.final_values[(bot_id, "health")] == 0.0


def test_clamp_deployable_health_works_normally() -> None:
    """Test deployable health clamping works normally with same bounds."""
    world = create_test_world()
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=1.0,
        stacking_rule=StackingRule.ADD,
    )

    deployable_id = world.create_entity()
    world.add_component(
        entity_id=deployable_id,
        component=ConfigNamespaceComponent(namespace="deployment.deployable"),
    )

    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(deployable_id, "health"): -0.5}
    pipe_ctx = PipelineContext()

    result = stage.process(value=ctx, context=pipe_ctx)

    assert result.final_values[(deployable_id, "health")] == 0.0


def test_clamp_bot_battery_works_normally() -> None:
    """Test bot battery clamping works normally with same bounds."""
    world = create_test_world()
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="battery",
        min_value=0.0,
        max_value=1.0,
        stacking_rule=StackingRule.ADD,
    )

    bot_id = world.create_entity()
    world.add_component(
        entity_id=bot_id,
        component=ConfigNamespaceComponent(namespace="bot"),
    )

    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(bot_id, "battery"): 1.5}
    pipe_ctx = PipelineContext()

    result = stage.process(value=ctx, context=pipe_ctx)

    assert result.final_values[(bot_id, "battery")] == 1.0


def test_clamp_deployable_battery_works_normally() -> None:
    """Test deployable battery clamping works normally with same bounds."""
    world = create_test_world()
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="battery",
        min_value=0.0,
        max_value=1.0,
        stacking_rule=StackingRule.ADD,
    )

    deployable_id = world.create_entity()
    world.add_component(
        entity_id=deployable_id,
        component=ConfigNamespaceComponent(namespace="deployment.deployable"),
    )

    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(deployable_id, "battery"): 1.5}
    pipe_ctx = PipelineContext()

    result = stage.process(value=ctx, context=pipe_ctx)

    assert result.final_values[(deployable_id, "battery")] == 1.0


def test_clamp_without_world_uses_stat_config_bounds() -> None:
    """Test clamping without world falls back to stat_config bounds."""
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="temperature",
        min_value=0.0,
        max_value=1.0,
        stacking_rule=StackingRule.ADD,
    )

    entity_id = EntityID(fake.uuid4())

    ctx = ModifierContext(modifiers=[], config=config, world=None)
    ctx.final_values = {(entity_id, "temperature"): -0.25}
    pipe_ctx = PipelineContext()

    result = stage.process(value=ctx, context=pipe_ctx)

    assert result.final_values[(entity_id, "temperature")] == 0.0


def test_clamp_entity_without_namespace_component_uses_stat_config() -> None:
    """Test entity without ConfigNamespaceComponent uses stat_config bounds."""
    world = create_test_world()
    stage = ClampStage()
    config = ModifierConfig()
    config.register_stat(
        name="temperature",
        min_value=0.0,
        max_value=1.0,
        stacking_rule=StackingRule.ADD,
    )

    entity_id = world.create_entity()

    ctx = ModifierContext(modifiers=[], config=config, world=world)
    ctx.final_values = {(entity_id, "temperature"): -0.25}
    pipe_ctx = PipelineContext()

    result = stage.process(value=ctx, context=pipe_ctx)

    assert result.final_values[(entity_id, "temperature")] == 0.0

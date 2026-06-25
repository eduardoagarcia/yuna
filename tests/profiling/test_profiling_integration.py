"""Integration tests for profiling across all components."""

from dataclasses import dataclass

from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.system import System
from yuna.ecs.world import ECSWorld
from yuna.modifiers.config import ModifierConfig, StackingRule
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.modifiers.types import ModificationType, ModifierPriority
from yuna.profiling.monitor import (
    PerformanceMonitor,
    reset_performance_monitor,
)
from yuna.spatial.grid import SpatialGrid
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

fake = Faker()


@dataclass
class TestComponent(Component):
    """Test component for integration tests."""

    value: int = 0


def test_world_profiling_integration() -> None:
    """Test ECSWorld with profiling enabled."""
    reset_performance_monitor()
    world = ECSWorld(profiling_enabled=True)
    monitor = world._monitor
    assert monitor is not None

    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=TestComponent(value=42))

    class TestSystem(System):
        @property
        def priority(self) -> int:
            return 100

        def update(self, world: ECSWorld, delta_time: float) -> None:
            pass

    system = TestSystem()
    world.register_system(system=system)
    world.update(delta_time=0.016)

    stats = monitor.get_timing_stats(category="systems", name="TestSystem")
    assert stats is not None
    assert stats.count == 1


def test_query_profiling_integration() -> None:
    """Test Query with profiling enabled."""
    reset_performance_monitor()
    monitor = PerformanceMonitor()
    world = ECSWorld()

    entity_id = world.create_entity()
    world.add_component(entity_id=entity_id, component=TestComponent(value=42))

    query = world.query()
    query = query.with_components(TestComponent)
    query._profiling_enabled = True
    query._monitor = monitor

    entities = query.get_entities()
    assert entity_id in entities

    stats = monitor.get_timing_stats(category="queries", name="get_entities")
    assert stats is not None
    assert stats.count == 1


def test_modifier_pipeline_profiling_integration() -> None:
    """Test ModifierPipeline with profiling enabled."""
    reset_performance_monitor()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )

    pipeline = ModifierPipeline(config=config, profiling_enabled=True)
    monitor = pipeline._monitor
    assert monitor is not None

    modifier = Modifier(
        entity_id=EntityID("test-entity"),
        stat="health",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source="test",
    )
    pipeline.queue_modifier(modifier=modifier)
    pipeline.process(world=None, current_tick=0)

    stats = monitor.get_timing_stats(category="pipeline", name="modifiers")
    assert stats is not None
    assert stats.count == 1


def test_spatial_grid_profiling_integration() -> None:
    """Test SpatialGrid with profiling enabled."""
    reset_performance_monitor()
    grid = SpatialGrid(cell_size=10, profiling_enabled=True)
    monitor = grid._monitor
    assert monitor is not None

    entity1 = EntityID("entity1")
    entity2 = EntityID("entity2")
    entity3 = EntityID("entity3")

    grid.add(entity_id=entity1, position=Vector2(x=0.0, y=0.0))
    grid.add(entity_id=entity2, position=Vector2(x=5.0, y=5.0))
    grid.add(entity_id=entity3, position=Vector2(x=10.0, y=10.0))

    nearest = grid.get_nearest(position=Vector2(x=0.0, y=0.0), count=2)
    assert len(nearest) == 2
    assert entity1 in nearest

    stats = monitor.get_timing_stats(category="spatial", name="get_nearest")
    assert stats is not None
    assert stats.count == 1

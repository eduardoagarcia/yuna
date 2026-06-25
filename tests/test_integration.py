"""Integration tests for engine core patterns."""

from dataclasses import dataclass

from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.system import System
from yuna.ecs.world import ECSWorld
from yuna.events.bus import EventBus
from yuna.events.event import Event
from yuna.loop.game_loop import GameLoop
from yuna.loop.scheduler import SystemScheduler
from yuna.loop.time import TimeManager
from yuna.modifiers.config import ModifierConfig, StackingRule
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.modifiers.types import (
    ModificationType,
    ModifierPriority,
)
from yuna.resources.flyweight import FlyweightFactory
from yuna.resources.pool import ObjectPool
from yuna.services.locator import ServiceLocator
from yuna.spatial.grid import SpatialGrid
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

fake = Faker()


@dataclass
class Position(Component):
    """Position component."""

    x: float
    y: float


@dataclass
class Health(Component):
    """Health component."""

    value: float


@dataclass
class Velocity(Component):
    """Velocity component."""

    dx: float
    dy: float


@dataclass(frozen=True)
class EntityMovedEvent(Event):
    """Event emitted when entity moves."""

    entity_id: EntityID
    old_position: Vector2
    new_position: Vector2


def test_ecs_entity_component_query_integration() -> None:
    """Test entity creation, component addition, and querying."""
    world = ECSWorld()
    entity1 = world.create_entity()
    entity2 = world.create_entity()
    entity3 = world.create_entity()
    world.add_component(entity_id=entity1, component=Position(x=1.0, y=2.0))
    world.add_component(entity_id=entity1, component=Health(value=100.0))
    world.add_component(entity_id=entity2, component=Position(x=3.0, y=4.0))
    world.add_component(entity_id=entity3, component=Health(value=50.0))
    entities_with_position = world.query().with_components(Position).get_entities()
    entities_with_health = world.query().with_components(Health).get_entities()
    entities_with_both = world.query().with_components(Position, Health).get_entities()
    assert len(entities_with_position) == 2
    assert len(entities_with_health) == 2
    assert len(entities_with_both) == 1
    assert entity1 in entities_with_both


def test_modifier_pipeline_integration() -> None:
    """Test modifier pipeline processing with config."""
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    entity_id = EntityID("test-entity")
    modifier1 = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source="healing",
    )
    modifier2 = Modifier(
        entity_id=entity_id,
        stat="health",
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source="healing",
    )
    pipeline.queue_modifier(modifier=modifier1)
    pipeline.queue_modifier(modifier=modifier2)
    result = pipeline.process()
    assert (entity_id, "health") in result
    assert result[(entity_id, "health")] == 15.0


def test_event_bus_integration() -> None:
    """Test event emission and subscription."""
    bus = EventBus()
    events_received: list[Event] = []

    def handler(event: Event) -> None:
        events_received.append(event)

    bus.subscribe(event_type="EntityMovedEvent", handler=handler)
    event = EntityMovedEvent(
        timestamp=0.0,
        tick=0,
        entity_id=EntityID("test-entity"),
        old_position=Vector2(x=0.0, y=0.0),
        new_position=Vector2(x=1.0, y=1.0),
    )
    bus.emit(event=event)
    bus.process_events()
    assert len(events_received) == 1
    assert events_received[0] == event


def test_spatial_grid_integration() -> None:
    """Test spatial grid with entity positions."""
    grid = SpatialGrid(cell_size=10)
    entity1 = EntityID("entity-1")
    entity2 = EntityID("entity-2")
    entity3 = EntityID("entity-3")
    grid.add(entity_id=entity1, position=Vector2(x=5.0, y=5.0))
    grid.add(entity_id=entity2, position=Vector2(x=15.0, y=15.0))
    grid.add(entity_id=entity3, position=Vector2(x=7.0, y=7.0))
    entities_at_5_5 = grid.get_at(position=Vector2(x=5.0, y=5.0))
    entities_in_radius = grid.get_in_radius(position=Vector2(x=5.0, y=5.0), radius=5.0)
    assert entity1 in entities_at_5_5
    assert entity3 in entities_at_5_5
    assert entity2 not in entities_at_5_5
    assert entity1 in entities_in_radius
    assert entity3 in entities_in_radius
    grid.move(entity_id=entity1, new_position=Vector2(x=25.0, y=25.0))
    entities_at_5_5_after = grid.get_at(position=Vector2(x=5.0, y=5.0))
    assert entity1 not in entities_at_5_5_after


def test_service_locator_integration() -> None:
    """Test service locator registration and retrieval."""
    locator = ServiceLocator()

    class TestService:
        def __init__(self, value: str):
            self.value = value

    service = TestService(value="test")
    locator.register(interface=TestService, factory=lambda: service)
    retrieved = locator.resolve(interface=TestService)
    assert retrieved is service
    assert retrieved.value == "test"


def test_object_pool_integration() -> None:
    """Test object pool with factory and reset."""
    call_count = {"factory": 0, "reset": 0}

    def factory() -> dict[str, int]:
        call_count["factory"] += 1
        return {"value": 0}

    def reset(obj: dict[str, int]) -> None:
        call_count["reset"] += 1
        obj["value"] = 0

    pool = ObjectPool[dict[str, int]](factory=factory, reset=reset, max_size=5)
    obj1 = pool.acquire()
    obj1["value"] = 10
    assert call_count["factory"] == 1
    pool.release(obj=obj1)
    assert call_count["reset"] == 1
    assert obj1["value"] == 0
    obj2 = pool.acquire()
    assert obj2 is obj1
    assert call_count["factory"] == 1


def test_flyweight_integration() -> None:
    """Test flyweight factory for shared instances."""
    factory = FlyweightFactory[str, dict[str, str]]()
    instance1 = factory.get(key="config-a", factory=lambda: {"name": "config-a"})
    instance2 = factory.get(key="config-a", factory=lambda: {"name": "different"})
    instance3 = factory.get(key="config-b", factory=lambda: {"name": "config-b"})
    assert instance1 is instance2
    assert instance1 is not instance3
    assert instance1["name"] == "config-a"
    assert instance3["name"] == "config-b"


def test_full_tick_cycle_integration() -> None:
    """Test complete tick cycle with all subsystems."""
    world = ECSWorld()
    event_bus = EventBus()
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    modifier_pipeline = ModifierPipeline(config=config)
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        event_bus=event_bus,
        modifier_pipeline=modifier_pipeline,
    )
    execution_order: list[str] = []

    class TestSystem(System):
        @property
        def priority(self) -> int:
            return 100

        def update(self, world: ECSWorld, delta_time: float) -> None:
            execution_order.append("system")

    def event_handler(event: Event) -> None:
        execution_order.append("event")

    event_bus.subscribe(event_type="TestEvent", handler=event_handler)
    scheduler.register(system=TestSystem())
    event_bus.emit(event=TestEvent(timestamp=0.0, tick=0))
    modifier = Modifier(
        entity_id=EntityID("test-entity"),
        stat="health",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source="test",
    )
    modifier_pipeline.queue_modifier(modifier=modifier)
    game_loop.tick()
    assert execution_order == ["event", "system"]
    assert modifier_pipeline.get_queue_size() == 0


def test_ecs_with_spatial_grid_integration() -> None:
    """Test ECS world with spatial grid for position tracking."""
    world = ECSWorld()
    grid = SpatialGrid(cell_size=10)
    entity1 = world.create_entity()
    entity2 = world.create_entity()
    pos1 = Position(x=5.0, y=5.0)
    pos2 = Position(x=15.0, y=15.0)
    world.add_component(entity_id=entity1, component=pos1)
    world.add_component(entity_id=entity2, component=pos2)
    grid.add(entity_id=entity1, position=Vector2(x=pos1.x, y=pos1.y))
    grid.add(entity_id=entity2, position=Vector2(x=pos2.x, y=pos2.y))
    entities_with_position = world.query().with_components(Position).get_entities()
    for entity_id in entities_with_position:
        position_component = world.get_component(
            entity_id=entity_id, component_type=Position
        )
        assert isinstance(position_component, Position)
        entities_at_pos = grid.get_at(
            position=Vector2(x=position_component.x, y=position_component.y)
        )
        assert entity_id in entities_at_pos


def test_system_with_modifier_integration() -> None:
    """Test system that queues modifiers during update."""
    world = ECSWorld()
    scheduler = SystemScheduler()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    modifier_pipeline = ModifierPipeline(config=config)
    modifiers_queued: list[Modifier] = []

    class ModifierQueuingSystem(System):
        @property
        def priority(self) -> int:
            return 100

        def update(self, world: ECSWorld, delta_time: float) -> None:
            modifier = Modifier(
                entity_id=EntityID("test-entity"),
                stat="health",
                modification_type=ModificationType.FLAT,
                value=5.0,
                priority=ModifierPriority.NORMAL,
                source="system",
            )
            modifiers_queued.append(modifier)
            modifier_pipeline.queue_modifier(modifier=modifier)

    scheduler.register(system=ModifierQueuingSystem())
    for system in scheduler.get_ordered_systems():
        system.update(world=world, delta_time=0.016)
    assert len(modifiers_queued) == 1
    assert modifier_pipeline.get_queue_size() == 1
    result = modifier_pipeline.process()
    assert (EntityID("test-entity"), "health") in result


def test_system_with_event_integration() -> None:
    """Test system that emits events during update."""
    world = ECSWorld()
    scheduler = SystemScheduler()
    event_bus = EventBus()
    events_emitted: list[Event] = []

    class EventEmittingSystem(System):
        @property
        def priority(self) -> int:
            return 100

        def update(self, world: ECSWorld, delta_time: float) -> None:
            event = TestEvent(timestamp=0.0, tick=0)
            events_emitted.append(event)
            event_bus.emit(event=event)

    def handler(event: Event) -> None:
        pass

    event_bus.subscribe(event_type="TestEvent", handler=handler)
    scheduler.register(system=EventEmittingSystem())
    for system in scheduler.get_ordered_systems():
        system.update(world=world, delta_time=0.016)
    assert len(events_emitted) == 1
    assert event_bus._queue.count_current() == 1


def test_multiple_systems_with_queries_integration() -> None:
    """Test multiple systems querying and updating entities."""
    world = ECSWorld()
    scheduler = SystemScheduler()
    entity1 = world.create_entity()
    entity2 = world.create_entity()
    world.add_component(entity_id=entity1, component=Position(x=0.0, y=0.0))
    world.add_component(entity_id=entity1, component=Velocity(dx=1.0, dy=0.0))
    world.add_component(entity_id=entity2, component=Position(x=5.0, y=5.0))
    world.add_component(entity_id=entity2, component=Velocity(dx=0.0, dy=1.0))
    updates: list[str] = []

    class MovementSystem(System):
        @property
        def priority(self) -> int:
            return 100

        def update(self, world: ECSWorld, delta_time: float) -> None:
            entities = world.query().with_components(Position, Velocity).get_entities()
            for entity_id in entities:
                updates.append(f"move-{entity_id}")

    class HealthSystem(System):
        @property
        def priority(self) -> int:
            return 200

        def update(self, world: ECSWorld, delta_time: float) -> None:
            entities = world.query().with_components(Health).get_entities()
            for entity_id in entities:
                updates.append(f"health-{entity_id}")

    scheduler.register(system=MovementSystem())
    scheduler.register(system=HealthSystem())
    for system in scheduler.get_ordered_systems():
        system.update(world=world, delta_time=0.016)
    assert len(updates) == 2
    assert f"move-{entity1}" in updates
    assert f"move-{entity2}" in updates


def test_entity_destruction_integration() -> None:
    """Test entity destruction removes components and clears from queries."""
    world = ECSWorld()
    entity = world.create_entity()
    world.add_component(entity_id=entity, component=Position(x=1.0, y=2.0))
    world.add_component(entity_id=entity, component=Health(value=100.0))
    entities_before = world.query().with_components(Position).get_entities()
    assert entity in entities_before
    world.destroy_entity(entity_id=entity)
    world.update(delta_time=0.016)
    entities_after = world.query().with_components(Position).get_entities()
    assert entity not in entities_after
    position = world.get_component(entity_id=entity, component_type=Position)
    assert position is None


def test_service_locator_with_game_loop_integration() -> None:
    """Test service locator providing services to systems."""
    locator = ServiceLocator()
    world = ECSWorld()
    scheduler = SystemScheduler()
    time_manager = TimeManager(fixed_delta=0.016)
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )

    class GameConfig:
        def __init__(self) -> None:
            self.gravity = 9.8

    config = GameConfig()
    locator.register(interface=GameConfig, factory=lambda: config)
    service_calls: list[float] = []

    class PhysicsSystem(System):
        @property
        def priority(self) -> int:
            return 100

        def update(self, world: ECSWorld, delta_time: float) -> None:
            game_config = locator.resolve(interface=GameConfig)
            service_calls.append(game_config.gravity)

    scheduler.register(system=PhysicsSystem())
    game_loop.tick()
    assert len(service_calls) == 1
    assert service_calls[0] == 9.8


def test_object_pool_with_spatial_grid_integration() -> None:
    """Test object pool for position data with spatial grid."""
    pool = ObjectPool[dict[str, float]](
        factory=lambda: {"x": 0.0, "y": 0.0},
        reset=lambda v: v.update({"x": 0.0, "y": 0.0}),
        max_size=10,
    )
    grid = SpatialGrid(cell_size=10)
    entity = EntityID("test-entity")
    position_data = pool.acquire()
    position_data["x"] = 5.0
    position_data["y"] = 5.0
    grid.add(
        entity_id=entity, position=Vector2(x=position_data["x"], y=position_data["y"])
    )
    entities = grid.get_at(position=Vector2(x=position_data["x"], y=position_data["y"]))
    assert entity in entities
    pool.release(obj=position_data)
    reused = pool.acquire()
    assert reused is position_data


def test_complex_workflow_integration() -> None:
    """Test complex workflow with all patterns working together."""
    locator = ServiceLocator()
    world = ECSWorld()
    event_bus = EventBus()
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    config = ModifierConfig()
    config.register_stat(
        name="health",
        min_value=0.0,
        max_value=100.0,
        stacking_rule=StackingRule.ADD,
    )
    modifier_pipeline = ModifierPipeline(config=config)
    grid = SpatialGrid(cell_size=10)
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        event_bus=event_bus,
        modifier_pipeline=modifier_pipeline,
    )
    locator.register(interface=SpatialGrid, factory=lambda: grid)
    entity1 = world.create_entity()
    entity2 = world.create_entity()
    world.add_component(entity_id=entity1, component=Position(x=5.0, y=5.0))
    world.add_component(entity_id=entity1, component=Health(value=100.0))
    world.add_component(entity_id=entity2, component=Position(x=15.0, y=15.0))
    world.add_component(entity_id=entity2, component=Health(value=50.0))
    grid.add(entity_id=entity1, position=Vector2(x=5.0, y=5.0))
    grid.add(entity_id=entity2, position=Vector2(x=15.0, y=15.0))
    events_received: list[Event] = []

    def movement_handler(event: Event) -> None:
        events_received.append(event)

    event_bus.subscribe(event_type="EntityMovedEvent", handler=movement_handler)

    class SpatialUpdateSystem(System):
        @property
        def priority(self) -> int:
            return 100

        def update(self, world: ECSWorld, delta_time: float) -> None:
            entities = world.query().with_components(Position).get_entities()
            spatial_grid = locator.resolve(interface=SpatialGrid)
            for entity_id in entities:
                position_component = world.get_component(
                    entity_id=entity_id,
                    component_type=Position,
                )
                assert isinstance(position_component, Position)
                nearby = spatial_grid.get_in_radius(
                    position=Vector2(x=position_component.x, y=position_component.y),
                    radius=3.0,
                )
                if len(nearby) > 1:
                    modifier = Modifier(
                        entity_id=entity_id,
                        stat="health",
                        modification_type=ModificationType.FLAT,
                        value=-10.0,
                        priority=ModifierPriority.NORMAL,
                        source="collision",
                    )
                    modifier_pipeline.queue_modifier(modifier=modifier)

    scheduler.register(system=SpatialUpdateSystem())
    game_loop.update(elapsed=0.016)
    assert modifier_pipeline.get_queue_size() == 0


class TestEvent(Event):
    """Test event implementation."""

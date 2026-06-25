"""Tests for game loop implementation."""

import pytest
from faker import Faker

from yuna.ecs.system import System
from yuna.ecs.world import ECSWorld
from yuna.events.bus import EventBus
from yuna.events.event import Event
from yuna.exceptions import StateError
from yuna.loop.game_loop import GameLoop
from yuna.loop.scheduler import SystemScheduler
from yuna.loop.time import TimeManager
from yuna.modifiers.config import ModifierConfig
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.modifiers.types import (
    ModificationType,
    ModifierPriority,
)
from yuna.profiling.monitor import PerformanceMonitor
from yuna.types.identifiers import EntityID

fake = Faker()


class TestSystem(System):
    """Test system implementation."""

    def __init__(self, priority_value: int, name: str = ""):
        self._priority = priority_value
        self.name = name
        self.update_count = 0
        self.update_order: list[int] = []

    @property
    def priority(self) -> int:
        return self._priority

    def update(self, world: ECSWorld, delta_time: float) -> None:
        self.update_count += 1
        self.update_order.append(len(self.update_order))


def test_game_loop_creation() -> None:
    """Test GameLoop can be created with minimal components."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    assert game_loop.fixed_delta == 0.016
    assert game_loop.accumulator == 0.0


def test_game_loop_with_all_components() -> None:
    """Test GameLoop can be created with all optional components."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    event_bus = EventBus()
    config = ModifierConfig()
    modifier_pipeline = ModifierPipeline(config=config)
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        event_bus=event_bus,
        modifier_pipeline=modifier_pipeline,
    )
    assert game_loop.fixed_delta == 0.016


def test_single_tick_execution() -> None:
    """Test executing single tick."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    system = TestSystem(priority_value=100)
    scheduler.register(system=system)
    game_loop.tick()
    assert system.update_count == 1


def test_multiple_ticks_via_update() -> None:
    """Test update executes multiple ticks based on elapsed time."""
    fixed_delta = 0.016
    time_manager = TimeManager(fixed_delta=fixed_delta)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    system = TestSystem(priority_value=100)
    scheduler.register(system=system)
    ticks = game_loop.update(elapsed=fixed_delta * 3)
    assert ticks == 3
    assert system.update_count == 3


def test_update_with_partial_tick() -> None:
    """Test update with partial tick preserves accumulator."""
    fixed_delta = 0.016
    time_manager = TimeManager(fixed_delta=fixed_delta)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    system = TestSystem(priority_value=100)
    scheduler.register(system=system)
    ticks = game_loop.update(elapsed=fixed_delta * 2.5)
    assert ticks == 2
    assert system.update_count == 2
    assert game_loop.accumulator == fixed_delta * 0.5


def test_system_execution_order() -> None:
    """Test systems execute in priority order."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    system_high = TestSystem(priority_value=300, name="high")
    system_low = TestSystem(priority_value=100, name="low")
    system_mid = TestSystem(priority_value=200, name="mid")
    scheduler.register(system=system_high)
    scheduler.register(system=system_low)
    scheduler.register(system=system_mid)
    game_loop.tick()
    assert system_low.update_count == 1
    assert system_mid.update_count == 1
    assert system_high.update_count == 1


def test_event_processing_in_tick() -> None:
    """Test events are processed during tick."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    event_bus = EventBus()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        event_bus=event_bus,
    )
    events_processed: list[str] = []

    def handler(event: Event) -> None:
        events_processed.append(event.event_type)

    event_bus.subscribe(event_type="TestEvent", handler=handler)
    test_event = TestEvent(timestamp=0.0, tick=0)
    event_bus.emit(event=test_event)
    game_loop.tick()
    assert len(events_processed) == 1
    assert events_processed[0] == "TestEvent"


def test_event_bus_end_tick_called() -> None:
    """Test event bus end_tick is called after systems update."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    event_bus = EventBus()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        event_bus=event_bus,
    )
    delayed_event = TestEvent(timestamp=0.0, tick=0)
    event_bus.emit(event=delayed_event, delay_frames=1)
    assert event_bus._queue.count_next() == 1
    game_loop.tick()
    assert event_bus._queue.count_current() == 1


def test_modifier_pipeline_processing() -> None:
    """Test modifier pipeline is processed during tick."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    config = ModifierConfig()
    modifier_pipeline = ModifierPipeline(config=config)
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        modifier_pipeline=modifier_pipeline,
    )
    modifier = Modifier(
        entity_id=EntityID("test-entity"),
        stat="test_stat",
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source="test",
    )
    modifier_pipeline.queue_modifier(modifier=modifier)
    assert modifier_pipeline.get_queue_size() == 1
    game_loop.tick()
    assert modifier_pipeline.get_queue_size() == 0


def test_processing_order() -> None:
    """Test modifiers process before events before systems."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    event_bus = EventBus()
    config = ModifierConfig()
    modifier_pipeline = ModifierPipeline(config=config)
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        event_bus=event_bus,
        modifier_pipeline=modifier_pipeline,
    )
    execution_order: list[str] = []

    class OrderTrackingSystem(System):
        @property
        def priority(self) -> int:
            return 100

        def update(self, world: ECSWorld, delta_time: float) -> None:
            execution_order.append("system")

    def event_handler(event: Event) -> None:
        execution_order.append("event")

    event_bus.subscribe(event_type="TestEvent", handler=event_handler)
    event_bus.emit(event=TestEvent(timestamp=0.0, tick=0))
    modifier = Modifier(
        entity_id=EntityID("test-entity"),
        stat="test_stat",
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source="test",
    )
    modifier_pipeline.queue_modifier(modifier=modifier)
    scheduler.register(system=OrderTrackingSystem())
    game_loop.tick()
    assert execution_order == ["event", "system"]


def test_reset_time() -> None:
    """Test reset_time clears accumulator."""
    fixed_delta = 0.016
    time_manager = TimeManager(fixed_delta=fixed_delta)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    game_loop.update(elapsed=0.01)
    assert game_loop.accumulator == 0.01
    game_loop.reset_time()
    assert game_loop.accumulator == 0.0


def test_fixed_delta_property() -> None:
    """Test fixed_delta property returns correct value."""
    fixed_delta = fake.pyfloat(min_value=0.001, max_value=1.0)
    time_manager = TimeManager(fixed_delta=fixed_delta)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    assert game_loop.fixed_delta == fixed_delta


def test_accumulator_property() -> None:
    """Test accumulator property returns current value."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    assert game_loop.accumulator == 0.0
    game_loop.update(elapsed=0.01)
    assert game_loop.accumulator == 0.01


def test_update_with_zero_elapsed() -> None:
    """Test update with zero elapsed time executes no ticks."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    system = TestSystem(priority_value=100)
    scheduler.register(system=system)
    ticks = game_loop.update(elapsed=0.0)
    assert ticks == 0
    assert system.update_count == 0


def test_multiple_systems_all_update() -> None:
    """Test all systems update during tick."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    systems = [TestSystem(priority_value=i * 100) for i in range(5)]
    for system in systems:
        scheduler.register(system=system)
    game_loop.tick()
    for system in systems:
        assert system.update_count == 1


def test_consecutive_ticks() -> None:
    """Test consecutive ticks increment system update counts."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    system = TestSystem(priority_value=100)
    scheduler.register(system=system)
    game_loop.tick()
    game_loop.tick()
    game_loop.tick()
    assert system.update_count == 3


def test_no_systems_registered() -> None:
    """Test tick executes without systems registered."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    game_loop.tick()
    ticks = game_loop.update(elapsed=0.016)
    assert ticks == 1


def test_systems_receive_correct_delta_time() -> None:
    """Test systems receive fixed delta time during update."""
    fixed_delta = 0.016

    class DeltaTrackingSystem(System):
        def __init__(self) -> None:
            self.received_delta: float | None = None

        @property
        def priority(self) -> int:
            return 100

        def update(self, world: ECSWorld, delta_time: float) -> None:
            self.received_delta = delta_time

    time_manager = TimeManager(fixed_delta=fixed_delta)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    system = DeltaTrackingSystem()
    scheduler.register(system=system)
    game_loop.tick()
    assert system.received_delta == fixed_delta


def test_event_processing_without_events() -> None:
    """Test event bus processes without queued events."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    event_bus = EventBus()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        event_bus=event_bus,
    )
    game_loop.tick()


def test_modifier_pipeline_without_modifiers() -> None:
    """Test modifier pipeline processes without queued modifiers."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    config = ModifierConfig()
    modifier_pipeline = ModifierPipeline(config=config)
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        modifier_pipeline=modifier_pipeline,
    )
    game_loop.tick()


def test_update_accumulates_across_frames() -> None:
    """Test update accumulates partial time across multiple calls."""
    fixed_delta = 0.016
    time_manager = TimeManager(fixed_delta=fixed_delta)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    system = TestSystem(priority_value=100)
    scheduler.register(system=system)
    ticks1 = game_loop.update(elapsed=0.01)
    assert ticks1 == 0
    assert system.update_count == 0
    ticks2 = game_loop.update(elapsed=0.01)
    assert ticks2 == 1
    assert system.update_count == 1


def test_large_elapsed_time() -> None:
    """Test update handles large elapsed time correctly."""
    fixed_delta = 0.016
    time_manager = TimeManager(fixed_delta=fixed_delta)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    system = TestSystem(priority_value=100)
    scheduler.register(system=system)
    ticks = game_loop.update(elapsed=1.0)
    assert ticks == 62
    assert system.update_count == 62


def test_game_loop_with_monitor() -> None:
    """Test GameLoop can be created with performance monitor."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    monitor = PerformanceMonitor()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        monitor=monitor,
    )
    assert game_loop.fixed_delta == 0.016


def test_monitor_profiles_modifier_pipeline() -> None:
    """Test monitor profiles modifier pipeline execution."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    config = ModifierConfig()
    modifier_pipeline = ModifierPipeline(config=config)
    monitor = PerformanceMonitor()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        modifier_pipeline=modifier_pipeline,
        monitor=monitor,
    )
    modifier = Modifier(
        entity_id=EntityID("test-entity"),
        stat="test_stat",
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source="test",
    )
    modifier_pipeline.queue_modifier(modifier=modifier)
    game_loop.tick()
    stats = monitor.get_timing_stats(category="loop", name="ModifierPipeline")
    assert stats is not None
    assert stats.count == 1


def test_monitor_profiles_event_processing() -> None:
    """Test monitor profiles event processing execution."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    event_bus = EventBus()
    monitor = PerformanceMonitor()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        event_bus=event_bus,
        monitor=monitor,
    )

    def handler(event: Event) -> None:
        pass

    event_bus.subscribe(event_type="TestEvent", handler=handler)
    test_event = TestEvent(timestamp=0.0, tick=0)
    event_bus.emit(event=test_event)
    game_loop.tick()
    stats = monitor.get_timing_stats(category="loop", name="EventProcessing")
    assert stats is not None
    assert stats.count == 1


def test_monitor_profiles_individual_systems() -> None:
    """Test monitor profiles each system with System:{ClassName} label."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    monitor = PerformanceMonitor()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        monitor=monitor,
    )
    system1 = TestSystem(priority_value=100, name="system1")
    system2 = TestSystem(priority_value=200, name="system2")
    scheduler.register(system=system1)
    scheduler.register(system=system2)
    game_loop.tick()
    stats = monitor.get_timing_stats(category="systems", name="TestSystem")
    assert stats is not None
    assert stats.count == 2


def test_monitor_profiles_multiple_ticks() -> None:
    """Test monitor accumulates stats across multiple ticks."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    monitor = PerformanceMonitor()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        monitor=monitor,
    )
    system = TestSystem(priority_value=100)
    scheduler.register(system=system)
    game_loop.tick()
    game_loop.tick()
    game_loop.tick()
    stats = monitor.get_timing_stats(category="systems", name="TestSystem")
    assert stats is not None
    assert stats.count == 3


def test_get_performance_stats() -> None:
    """Test get_performance_stats returns all statistics."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    event_bus = EventBus()
    config = ModifierConfig()
    modifier_pipeline = ModifierPipeline(config=config)
    monitor = PerformanceMonitor()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
        event_bus=event_bus,
        modifier_pipeline=modifier_pipeline,
        monitor=monitor,
    )
    system = TestSystem(priority_value=100)
    scheduler.register(system=system)
    modifier = Modifier(
        entity_id=EntityID("test-entity"),
        stat="test_stat",
        modification_type=ModificationType.FLAT,
        value=1.0,
        priority=ModifierPriority.NORMAL,
        source="test",
    )
    modifier_pipeline.queue_modifier(modifier=modifier)

    def handler(event: Event) -> None:
        pass

    event_bus.subscribe(event_type="TestEvent", handler=handler)
    test_event = TestEvent(timestamp=0.0, tick=0)
    event_bus.emit(event=test_event)
    game_loop.tick()
    stats = game_loop.get_performance_stats()
    assert len(stats) == 2
    assert "loop" in stats
    assert "systems" in stats
    assert "ModifierPipeline" in stats["loop"]
    assert "EventProcessing" in stats["loop"]
    assert "TestSystem" in stats["systems"]


def test_get_performance_stats_without_monitor_raises_error() -> None:
    """Test get_performance_stats raises error when no monitor configured."""
    time_manager = TimeManager(fixed_delta=0.016)
    scheduler = SystemScheduler()
    world = ECSWorld()
    game_loop = GameLoop(
        time_manager=time_manager,
        scheduler=scheduler,
        world=world,
    )
    with pytest.raises(StateError, match="No monitor configured"):
        game_loop.get_performance_stats()


class TestEvent(Event):
    """Test event implementation."""

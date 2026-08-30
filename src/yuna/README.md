# Engine Core v3

A high-performance Entity Component System (ECS) game engine with advanced patterns for game development.

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Core Patterns](#core-patterns)
- [API Reference](#api-reference)
- [Integration Examples](#integration-examples)
- [Performance Characteristics](#performance-characteristics)

## Quick Start

### Creating Your First Game Loop

```python
from yuna.ecs.world import ECSWorld
from yuna.loop.game_loop import GameLoop
from yuna.loop.scheduler import SystemScheduler
from yuna.loop.time import TimeManager

time_manager = TimeManager(fixed_delta=1/60)
scheduler = SystemScheduler()
world = ECSWorld()

game_loop = GameLoop(
    time_manager=time_manager,
    scheduler=scheduler,
    world=world,
)

while running:
    elapsed = get_frame_time()
    game_loop.update(elapsed=elapsed)
```

### Creating Entities and Components

```python
from dataclasses import dataclass
from yuna.ecs.component import Component

@dataclass
class Position(Component):
    x: float
    y: float

@dataclass
class Velocity(Component):
    dx: float
    dy: float

entity = world.create_entity()
world.add_component(entity_id=entity, component=Position(x=0.0, y=0.0))
world.add_component(entity_id=entity, component=Velocity(dx=1.0, dy=0.0))
```

### Creating Systems

```python
from yuna.ecs.system import System

class MovementSystem(System):
    @property
    def priority(self) -> int:
        return 100

    def update(self, world: ECSWorld, delta_time: float) -> None:
        for entity_id, (pos, vel) in world.query().with_components(Position, Velocity).iterator():
            pos.x += vel.dx * delta_time
            pos.y += vel.dy * delta_time

scheduler.register(system=MovementSystem())
```

## Architecture Overview

The engine core v3 is built on a modular architecture with 11 core patterns:

1. **Foundation**: Core types (Vector2, EntityID) and utilities
2. **Service Locator**: Dependency injection with singleton/transient lifetimes
3. **Entity Component System**: Data-oriented design for game entities
4. **Event System**: Double-buffered event queue with priority ordering
5. **Command Pattern**: Undo/redo support with validation
6. **Pipeline Pattern**: Composable processing stages
7. **Modifier Pipeline**: Stat modification with stacking rules
8. **Spatial Indexing**: O(1) spatial queries with grid-based hashing
9. **Resource Management**: Object pooling and flyweight pattern
10. **Game Loop**: Fixed timestep with accumulator pattern
11. **Integration**: All patterns working together

## Core Patterns

### Entity Component System (ECS)

The ECS pattern separates data (Components) from logic (Systems) for better performance and maintainability.

**Key Classes:**
- `ECSWorld`: Central coordinator for entities and components
- `Component`: Base class for data containers
- `System`: Base class for game logic
- `Query`: Efficient entity filtering by component composition

**Benefits:**
- Data locality for cache-friendly iteration
- Easy to add/remove functionality
- Natural parallelization opportunities

### Event System

Double-buffered event queue with priority-based ordering ensures deterministic event processing.

**Key Classes:**
- `Event`: Immutable event data with timestamp and tick
- `EventBus`: Unified event queue and dispatcher
- `EventQueue`: Double-buffered priority queue
- `EventDispatcher`: Type-based event routing

**Features:**
- Frame-based event delays
- Priority ordering within frames
- Type-safe event subscriptions

### Command Pattern

Encapsulates actions with validation, execution, and optional undo support.

**Key Classes:**
- `Command`: Abstract base for all commands
- `CommandInvoker`: Execution with history tracking
- `CommandMacro`: Batch multiple commands

**Use Cases:**
- User input handling
- AI decision execution
- Network command replication

### Modifier Pipeline

Processes stat modifications through configurable pipeline stages.

**Key Classes:**
- `ModifierPipeline`: Orchestrates all pipeline stages
- `Modifier`: Immutable modification data
- `ModifierConfig`: Stat definitions and constraints

**Pipeline Stages:**
1. Collect: Gather all queued modifiers
2. Filter: Remove invalid modifiers
3. Sort: Order by priority
4. Group: Group by target stat
5. Stack: Apply stacking rules (add/multiply/max/min)
6. Clamp: Enforce min/max constraints
7. Apply: Write final values

### Spatial Indexing

Grid-based spatial indexing provides O(1) point queries and efficient radius searches.

**Key Classes:**
- `SpatialGrid`: Cell-based entity positioning
- `SpatialQuery`: Protocol for spatial queries

**Performance:**
- O(1) point queries
- O(k) radius queries where k = entities in nearby cells
- Efficient updates when entities move

### Resource Management

Object pooling and flyweight patterns reduce allocations.

**Key Classes:**
- `ObjectPool`: Reusable object instances
- `FlyweightFactory`: Shared instances by key

**Benefits:**
- Reduced garbage collection pressure
- Consistent allocation patterns
- Memory efficiency through sharing

### Game Loop

Fixed timestep game loop with accumulator pattern ensures deterministic simulation.

**Key Classes:**
- `GameLoop`: Main loop orchestrator
- `TimeManager`: Fixed timestep with accumulator
- `SystemScheduler`: Priority-based system ordering

**Execution Order:**
1. Modifier pipeline processing
2. Event processing
3. System updates (by priority)
4. Event bus tick finalization

## API Reference

### ECS World

#### ECSWorld

Central coordinator for the Entity Component System.

```python
world = ECSWorld()
```

**Methods:**

```python
def create_entity() -> EntityID:
    """Create a new entity."""

def destroy_entity(entity_id: EntityID) -> None:
    """Mark entity for destruction at end of update cycle."""

def add_component(entity_id: EntityID, component: Component) -> None:
    """Add component to entity."""

def get_component(entity_id: EntityID, component_type: type[Component]) -> Component | None:
    """Get component from entity."""

def has_component(entity_id: EntityID, component_type: type[Component]) -> bool:
    """Check if entity has component."""

def remove_component(entity_id: EntityID, component_type: type[Component]) -> None:
    """Remove component from entity."""

def query() -> Query:
    """Create a new component query."""

def register_system(system: System) -> None:
    """Register system for execution."""

def update(delta_time: float) -> None:
    """Update all systems and flush destroyed entities."""
```

#### Query

Filters entities based on component composition.

```python
query = world.query()
```

**Methods:**

```python
def with_components(*component_types: type[Component]) -> Query:
    """Filter for entities that have all specified components."""

def without_components(*component_types: type[Component]) -> Query:
    """Filter for entities that don't have any specified components."""

def iterator() -> Iterator[tuple[EntityID, tuple[Component, ...]]]:
    """Iterate over entities matching the query with their components."""

def get_entities() -> set[EntityID]:
    """Get all entity IDs matching the query."""

def count() -> int:
    """Count number of entities matching the query."""
```

**Examples:**

```python
entities = world.query().with_components(Position).get_entities()

entities = world.query().with_components(Position, Velocity).without_components(Dead).get_entities()

for entity_id, (pos, vel) in world.query().with_components(Position, Velocity).iterator():
    pos.x += vel.dx
    pos.y += vel.dy
```

### Event System

#### EventBus

Unified event bus combining queue and dispatcher.

```python
bus = EventBus()
```

**Methods:**

```python
def emit(event: Event, delay_frames: int = 0) -> None:
    """Emit event with optional frame delay."""

def emit_priority(event: Event, priority: int, delay_frames: int = 0) -> None:
    """Emit event with specific priority."""

def subscribe(event_type: str, handler: Callable[[Event], None]) -> None:
    """Subscribe handler to specific event type."""

def subscribe_all(handler: Callable[[Event], None]) -> None:
    """Subscribe handler to all event types."""

def unsubscribe(event_type: str, handler: Callable[[Event], None]) -> None:
    """Unsubscribe handler from specific event type."""

def process_events() -> None:
    """Process all events in current frame."""

def end_tick() -> None:
    """End current tick and move delayed events to current frame."""
```

**Example:**

```python
from dataclasses import dataclass
from yuna.events.event import Event

@dataclass(frozen=True)
class PlayerDiedEvent(Event):
    player_id: EntityID

def on_player_died(event: Event) -> None:
    print(f"Player {event.player_id} died!")

bus.subscribe(event_type="PlayerDiedEvent", handler=on_player_died)
bus.emit(event=PlayerDiedEvent(timestamp=0.0, tick=100, player_id=player_id))
bus.process_events()
```

### Modifier Pipeline

#### ModifierPipeline

Pipeline for processing stat modifications.

```python
from yuna.modifiers.config import ModifierConfig, StackingRule
from yuna.modifiers.pipeline import ModifierPipeline

config = ModifierConfig()
config.register_stat(
    name="health",
    min_value=0.0,
    max_value=100.0,
    stacking_rule=StackingRule.ADD,
)

pipeline = ModifierPipeline(config=config)
```

**Methods:**

```python
def queue_modifier(modifier: Modifier) -> None:
    """Add modifier to processing queue."""

def process(world: Any | None = None) -> dict[tuple, float]:
    """Process all queued modifiers through pipeline."""

def clear_queue() -> None:
    """Clear all queued modifiers without processing."""

def get_queue_size() -> int:
    """Get number of queued modifiers."""
```

**Example:**

```python
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.types import ModificationType, ModifierPriority

modifier = Modifier(
    entity_id=player_id,
    stat="health",
    modification_type=ModificationType.FLAT,
    value=10.0,
    priority=ModifierPriority.NORMAL,
    source="healing_potion",
)

pipeline.queue_modifier(modifier=modifier)
result = pipeline.process()
final_health = result[(player_id, "health")]
```

### Spatial Indexing

#### SpatialGrid

Grid-based spatial index for fast entity position queries.

```python
from yuna.spatial.grid import SpatialGrid

grid = SpatialGrid(cell_size=10)
```

**Methods:**

```python
def add(entity_id: EntityID, position: Vector2) -> None:
    """Add entity to spatial grid at position."""

def remove(entity_id: EntityID) -> None:
    """Remove entity from spatial grid."""

def move(entity_id: EntityID, new_position: Vector2) -> None:
    """Update entity position in spatial grid."""

def get_at(position: Vector2) -> set[EntityID]:
    """Get all entities at a specific position (O(1) lookup)."""

def get_in_radius(position: Vector2, radius: float) -> set[EntityID]:
    """Get all entities within radius of position."""
```

**Example:**

```python
grid.add(entity_id=enemy_id, position=Vector2(x=50.0, y=50.0))

nearby = grid.get_in_radius(position=player_pos, radius=10.0)
for enemy_id in nearby:
    attack(enemy_id)

grid.move(entity_id=enemy_id, new_position=Vector2(x=55.0, y=55.0))
```

### Resource Management

#### ObjectPool

Reusable object pool to reduce allocations.

```python
from yuna.resources.pool import ObjectPool

def factory() -> dict:
    return {"x": 0.0, "y": 0.0}

def reset(obj: dict) -> None:
    obj["x"] = 0.0
    obj["y"] = 0.0

pool = ObjectPool[dict](factory=factory, reset=reset, max_size=100)
```

**Methods:**

```python
def acquire() -> T:
    """Get object from pool or create new one."""

def release(obj: T) -> None:
    """Return object to pool after reset."""

def clear() -> None:
    """Remove all objects from pool."""

def count() -> int:
    """Get number of objects in pool."""
```

**Example:**

```python
obj = pool.acquire()
obj["x"] = 10.0
obj["y"] = 20.0
pool.release(obj=obj)
```

#### FlyweightFactory

Shared instance caching by key.

```python
from yuna.resources.flyweight import FlyweightFactory

factory = FlyweightFactory[str, dict]()
```

**Methods:**

```python
def get(key: K, factory: Callable[[], T]) -> T:
    """Get shared instance for key, creating if needed."""

def clear() -> None:
    """Remove all cached instances."""

def count() -> int:
    """Get number of cached instances."""
```

**Example:**

```python
config_a = factory.get(key="level_1", factory=lambda: load_level_config("level_1"))
config_b = factory.get(key="level_1", factory=lambda: load_level_config("level_1"))
assert config_a is config_b
```

### Game Loop

#### GameLoop

Orchestrates game loop with fixed timestep execution.

```python
from yuna.loop.game_loop import GameLoop

game_loop = GameLoop(
    time_manager=time_manager,
    scheduler=scheduler,
    world=world,
    event_bus=event_bus,
    modifier_pipeline=modifier_pipeline,
)
```

**Methods:**

```python
def tick() -> None:
    """Execute one game tick."""

def update(elapsed: float) -> int:
    """Update game loop with elapsed time, returns number of ticks executed."""

def reset_time() -> None:
    """Reset time manager accumulator to zero."""
```

**Properties:**

```python
@property
def fixed_delta() -> float:
    """Get fixed timestep value."""

@property
def accumulator() -> float:
    """Get current time accumulator."""
```

#### TimeManager

Manages fixed timestep game loop timing.

```python
from yuna.loop.time import TimeManager

time_manager = TimeManager(fixed_delta=1/60)
```

**Methods:**

```python
def update(elapsed: float) -> int:
    """Update accumulator and calculate ticks to execute."""

def reset() -> None:
    """Reset accumulator to zero."""
```

**Properties:**

```python
@property
def fixed_delta() -> float:
    """Get fixed timestep value."""

@property
def accumulator() -> float:
    """Get current accumulator value."""
```

#### SystemScheduler

Manages system registration and execution ordering.

```python
from yuna.loop.scheduler import SystemScheduler

scheduler = SystemScheduler()
```

**Methods:**

```python
def register(system: System) -> None:
    """Register system for execution."""

def get_ordered_systems() -> list[System]:
    """Get systems in priority order."""

def clear() -> None:
    """Remove all systems from scheduler."""
```

**Properties:**

```python
@property
def count() -> int:
    """Get number of registered systems."""
```

### Service Locator

#### ServiceLocator

Central registry for dependency injection.

```python
from yuna.services.locator import ServiceLocator

locator = ServiceLocator()
```

**Methods:**

```python
def register(interface: type[T], factory: Callable[[], T], lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
    """Register a service with its factory and lifetime."""

def resolve(interface: type[T]) -> T:
    """Resolve service instance by interface type."""

def clear() -> None:
    """Clear all registrations and singletons."""
```

**Example:**

```python
from yuna.services.lifetime import ServiceLifetime

class Logger:
    def log(self, message: str) -> None:
        print(message)

locator.register(
    interface=Logger,
    factory=lambda: Logger(),
    lifetime=ServiceLifetime.SINGLETON,
)

logger = locator.resolve(interface=Logger)
logger.log("Hello, world!")
```

## Integration Examples

### Complete Game Loop with All Systems

```python
from yuna.ecs.world import ECSWorld
from yuna.events.bus import EventBus
from yuna.loop.game_loop import GameLoop
from yuna.loop.scheduler import SystemScheduler
from yuna.loop.time import TimeManager
from yuna.modifiers.config import ModifierConfig, StackingRule
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.spatial.grid import SpatialGrid
from yuna.services.locator import ServiceLocator

world = ECSWorld()
event_bus = EventBus()
time_manager = TimeManager(fixed_delta=1/60)
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

locator = ServiceLocator()
locator.register(interface=SpatialGrid, factory=lambda: grid)

game_loop = GameLoop(
    time_manager=time_manager,
    scheduler=scheduler,
    world=world,
    event_bus=event_bus,
    modifier_pipeline=modifier_pipeline,
)

scheduler.register(system=MovementSystem())
scheduler.register(system=CombatSystem())
scheduler.register(system=RenderSystem())

while running:
    elapsed = get_frame_time()
    game_loop.update(elapsed=elapsed)
```

### Movement System with Spatial Grid

```python
class MovementSystem(System):
    @property
    def priority(self) -> int:
        return 100

    def update(self, world: ECSWorld, delta_time: float) -> None:
        spatial_grid = locator.resolve(interface=SpatialGrid)

        for entity_id, (pos, vel) in world.query().with_components(Position, Velocity).iterator():
            old_pos = Vector2(x=pos.x, y=pos.y)
            pos.x += vel.dx * delta_time
            pos.y += vel.dy * delta_time

            spatial_grid.move(
                entity_id=entity_id,
                new_position=Vector2(x=pos.x, y=pos.y),
            )

            event_bus.emit(event=EntityMovedEvent(
                timestamp=time.time(),
                tick=current_tick,
                entity_id=entity_id,
                old_position=old_pos,
                new_position=Vector2(x=pos.x, y=pos.y),
            ))
```

### Combat System with Modifiers

```python
class CombatSystem(System):
    @property
    def priority(self) -> int:
        return 200

    def update(self, world: ECSWorld, delta_time: float) -> None:
        spatial_grid = locator.resolve(interface=SpatialGrid)

        for entity_id, (pos, attack) in world.query().with_components(Position, Attack).iterator():
            nearby = spatial_grid.get_in_radius(
                position=Vector2(x=pos.x, y=pos.y),
                radius=attack.range,
            )

            for target_id in nearby:
                if target_id == entity_id:
                    continue

                if world.has_component(entity_id=target_id, component_type=Health):
                    modifier = Modifier(
                        entity_id=target_id,
                        stat="health",
                        modification_type=ModificationType.FLAT,
                        value=-attack.damage,
                        priority=ModifierPriority.NORMAL,
                        source=f"attack_{entity_id}",
                    )
                    modifier_pipeline.queue_modifier(modifier=modifier)
```

### Event-Driven System

```python
class DeathSystem(System):
    @property
    def priority(self) -> int:
        return 300

    def update(self, world: ECSWorld, delta_time: float) -> None:
        for entity_id, health in world.query().with_components(Health).iterator():
            if health.value <= 0:
                event_bus.emit(event=EntityDiedEvent(
                    timestamp=time.time(),
                    tick=current_tick,
                    entity_id=entity_id,
                ))
                world.destroy_entity(entity_id=entity_id)

def on_entity_died(event: Event) -> None:
    print(f"Entity {event.entity_id} died!")
    spawn_death_particles(event.entity_id)
    play_death_sound()

event_bus.subscribe(event_type="EntityDiedEvent", handler=on_entity_died)
```

## Performance Characteristics

### ECS World

- **Entity Creation**: O(1)
- **Component Add/Remove**: O(1)
- **Component Get**: O(1)
- **Query (single component)**: O(n) where n = entities with that component
- **Query (multiple components)**: O(k) where k = entities with least common component

### Spatial Grid

- **Point Query**: O(1) - constant time cell lookup
- **Radius Query**: O(k) where k = entities in nearby cells
- **Insert**: O(1)
- **Move**: O(1) if same cell, O(2) if different cell
- **Remove**: O(1)

### Event System

- **Emit**: O(log n) for priority queue insertion
- **Process**: O(n) where n = events in current frame
- **Subscribe**: O(1)

### Modifier Pipeline

- **Queue**: O(1)
- **Process**: O(n log n) where n = queued modifiers (dominated by sorting)

### Resource Management

- **ObjectPool Acquire**: O(1) from pool, O(k) if creating new (k = factory time)
- **ObjectPool Release**: O(1)
- **Flyweight Get**: O(1) hash lookup

### Benchmark Results

Tested on 1000 entities with multiple components:

- Entity creation with 3 components: < 1.0s
- Query iteration: < 0.1s
- Spatial grid point queries (10,000 iterations): < 1.0s
- Spatial grid radius queries vs linear search: 2-5x faster
- Component add/remove (10,000 iterations): < 1.0s
- Entity destruction (1000 entities): < 1.0s

## Best Practices

### Component Design

- Keep components as pure data containers
- Use frozen dataclasses for immutability where possible
- Avoid circular references between components

```python
@dataclass
class Position(Component):
    x: float
    y: float
```

### System Design

- Systems should be stateless where possible
- Use service locator for shared resources
- Keep systems focused on single responsibility
- Use priority to control execution order

```python
class MovementSystem(System):
    @property
    def priority(self) -> int:
        return 100

    def update(self, world: ECSWorld, delta_time: float) -> None:
        pass
```

### Event Handling

- Events should be immutable (frozen dataclasses)
- Include timestamp and tick for debugging
- Use specific event types rather than generic events

```python
@dataclass(frozen=True)
class CollisionEvent(Event):
    entity_a: EntityID
    entity_b: EntityID
    position: Vector2
```

### Modifier Usage

- Register all stats in config before using pipeline
- Use appropriate stacking rules for each stat
- Set min/max constraints to prevent invalid values

```python
config.register_stat(
    name="speed",
    min_value=0.0,
    max_value=100.0,
    stacking_rule=StackingRule.MULTIPLY,
)
```

### Spatial Grid Configuration

- Choose cell size based on average query radius
- Generally: cell_size = 2 * average_query_radius
- Larger cells reduce overhead but less precision
- Smaller cells improve precision but more overhead

```python
grid = SpatialGrid(cell_size=10)
```

## Testing

The engine core v3 includes comprehensive test coverage:

- **Unit Tests**: Individual module functionality
- **Integration Tests**: All patterns working together
- **Performance Tests**: Benchmark critical operations

Run tests:

```bash
pytest tests/services/engine/core/
```

Run with coverage:

```bash
pytest tests/services/engine/core/ --cov=yuna --cov-report=term-missing
```

## License

Hello Yuna LLC

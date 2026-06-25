<div align="center">

<img src="assets/yuna.svg" alt="Yuna" width="160" />

# Yuna Python Game Engine

Fast, dependency-light ECS game engine for Python.

</div>

## Features

- **AI**: behavior trees, blackboards, pathfinding, perception, and steering for game agents.
- **Commands**: a command pattern with validation, permissions, macros, and undoable results.
- **Config**: data-driven schemas, formula patterns, and validators for tunable game data.
- **ECS**: an archetype-backed Entity Component System with fast component queries.
- **Events**: an event bus with dispatching, queuing, filtering, and consumption control.
- **FSM**: finite state machines with states, transitions, and a driving system.
- **Game loop**: a fixed-timestep loop with an accumulator and dependency-aware scheduling.
- **Modifiers**: a staged pipeline for stacking, scaling, and expiring stat modifiers.
- **Networking**: state replication with authority, delta compression, and interest management.
- **Physics**: a 2D physics engine with rigid bodies, shapes, and a stepping system.
- **Prefabs**: reusable entity templates instantiated into any world.
- **Profiling**: a performance monitor with per-system stats and timing decorators.
- **Replay**: deterministic recording and playback with incremental snapshots.
- **Resources**: object pooling and flyweight sharing to cut allocation churn.
- **Scene**: chunked scene streaming with transitions for large or open worlds.
- **Scripting**: a compact bytecode compiler and VM for in-game scripts.
- **Services**: a service locator with provider registration and lifetime control.
- **Spatial**: spatial partitioning via grids, quadtrees, and BVH for fast collision queries.
- **State**: snapshotting, serialization, versioning, and migrations for save/load.

## Install

```bash
uv add yuna-engine
```

## Quick start

One entity, two components, one system. A star falls under gravity:

```python
from dataclasses import dataclass

from yuna import Component, ECSWorld, System


@dataclass
class Position(Component):
    x: float
    y: float


@dataclass
class Velocity(Component):
    dx: float
    dy: float


class GravitySystem(System):
    @property
    def priority(self) -> int:
        return 100

    def update(self, world: ECSWorld, delta_time: float) -> None:
        for _entity, (pos, vel) in world.query().with_components(Position, Velocity).iterator():
            vel.dy += 9.8 * delta_time
            pos.x += vel.dx * delta_time
            pos.y += vel.dy * delta_time


world = ECSWorld()
world.register_system(system=GravitySystem())

star = world.create_entity()
world.add_component(entity_id=star, component=Position(x=0.0, y=100.0))
world.add_component(entity_id=star, component=Velocity(dx=0.0, dy=0.0))

for _ in range(60):
    world.update(delta_time=1 / 60)

pos = world.get_component(entity_id=star, component_type=Position)
print(pos.x, pos.y) # print position
```

Sixty ticks is one second at 60 fps. The star falls ~5 units, to `y≈105`.

## License

MIT. See [`LICENSE`](LICENSE).

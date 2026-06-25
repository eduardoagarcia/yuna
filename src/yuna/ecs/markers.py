"""Marker components for ECS entity classification."""

from dataclasses import dataclass

from yuna.ecs.component import Component


@dataclass(frozen=True)
class StaticComponent(Component):
    """Marks entity as static (never moves after creation).

    Presence-based component - exists = static, absent = dynamic.

    Static entities:
    - Never update position in spatial grid after initial placement
    - Examples: walls, stations, terrain, fixed obstacles
    - Optimization for spatial grid updates (skip these entities)
    - Typically added during world setup/initialization

    Usage:
        entity_id = world.create_entity()
        world.add_component(
            entity_id=entity_id,
            component=Position(position=Vector2(x=5, y=5)),
        )
        world.add_component(entity_id=entity_id, component=StaticComponent())
    """

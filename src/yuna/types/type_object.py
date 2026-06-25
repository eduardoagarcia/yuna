"""Entity type definitions for data-driven entity creation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from yuna.exceptions import ValidationError


@dataclass
class EntityType:
    """Defines an entity type as data instead of code.

    Responsibilities:
    - Define entity template with components and behaviors
    - Provide default component values
    - Enable data-driven entity creation from config

    The Type Object pattern separates entity definition from implementation,
    allowing game designers to create new entity types without writing code.

    Usage:
        player_type = EntityType(
            name="player",
            components={
                "Position": {"x": 0.0, "y": 0.0},
                "Health": {"current": 100, "maximum": 100},
                "Sprite": {"texture": "player.png"}
            },
            behaviors=["movement", "combat", "inventory"]
        )

        # Create entities from type definition
        entity_id = registry.create_entity(type_name="player")
    """

    name: str
    components: dict[str, Any] = field(default_factory=dict)
    behaviors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate entity type definition."""
        if not self.name:
            raise ValidationError(
                reason="EntityType name cannot be empty",
                field="name",
                value=str(self.name),
            )

        if not isinstance(self.components, dict):
            raise ValidationError(
                reason="components must be a dictionary",
                field="components",
                value=str(type(self.components)),
            )

        if not isinstance(self.behaviors, list):
            raise ValidationError(
                reason="behaviors must be a list",
                field="behaviors",
                value=str(type(self.behaviors)),
            )

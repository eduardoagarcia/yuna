"""Prefab definition for entity templates."""

from dataclasses import dataclass, field
from typing import Any

from yuna.exceptions import ValidationError


@dataclass
class Prefab:
    """Template for creating entities with predefined components.

    Prefabs are reusable entity templates that define default components,
    behaviors, and hierarchy structure. Think Unity prefabs or Unreal blueprints.

    Attributes:
        name: Unique prefab identifier
        components: Component type name -> default values dict
        behaviors: List of behavior names (game-defined systems)
        children: List of child prefab names for hierarchies
        metadata: Additional custom data for game logic

    Usage:
        player_prefab = Prefab(
            name="player",
            components={
                "Position": {"x": 0.0, "y": 0.0},
                "Health": {"max_hp": 100.0, "current_hp": 100.0},
                "Sprite": {"texture": "player.png"},
            },
            behaviors=["PlayerController", "CameraFollow"],
            children=[],
            metadata={"tags": ["player", "controllable"]},
        )
    """

    name: str
    components: dict[str, dict[str, Any]] = field(default_factory=dict)
    behaviors: list[str] = field(default_factory=list)
    children: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate prefab definition."""
        if not self.name:
            raise ValidationError(
                reason="Prefab name cannot be empty",
                field="name",
                value=str(self.name),
            )

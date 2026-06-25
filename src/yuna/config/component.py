"""ECS component for entity configuration.

Stores entity-specific config overrides as a component.
Optional: Games can use this for ECS-based config management.
"""

from dataclasses import dataclass, field
from typing import Any

from yuna.ecs.component import Component


@dataclass(frozen=True)
class ConfigComponent(Component):
    """Stores entity-specific configuration overrides.

    This is OPTIONAL - games can use ConfigStore directly
    or use this component for ECS integration.

    Example:
        world.add_component(
            entity_id=bot_id,
            component=ConfigComponent(
                overrides={"cache.size": 64, "sensor.range": 25.0}
            ),
        )
    """

    overrides: dict[str, Any] = field(default_factory=dict)

    def get_override(self, key: str) -> Any | None:
        """Get override value for key."""
        return self.overrides.get(key)

    def has_override(self, key: str) -> bool:
        """Check if override exists."""
        return key in self.overrides

    def with_override(self, key: str, value: Any) -> ConfigComponent:
        """Return new component with added override."""
        new_overrides = dict(self.overrides)
        new_overrides[key] = value
        return ConfigComponent(overrides=new_overrides)

    def without_override(self, key: str) -> ConfigComponent:
        """Return new component with removed override."""
        new_overrides = dict(self.overrides)
        new_overrides.pop(key, None)
        return ConfigComponent(overrides=new_overrides)


@dataclass(frozen=True)
class ConfigNamespaceComponent(Component):
    """Stores entity's config namespace for stat bound lookups.

    Used by modifier pipeline to look up entity-specific min/max bounds.
    Games populate this with entity-type namespaces.

    Examples:
        - Bot: ConfigNamespaceComponent(namespace="bot")
        - Deployable: ConfigNamespaceComponent(namespace="deployment.deployable")
        - Turret: ConfigNamespaceComponent(namespace="turret")

    ClampStage uses this to look up bounds from config:
        config_key = f"{namespace}.{stat}"  # e.g., "bot.temperature"
        min_value = world.config.get_min(key=config_key)
    """

    namespace: str

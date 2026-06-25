"""Manages global defaults and per-entity overrides with type-safe access."""

from dataclasses import dataclass, field
from typing import Any, cast

from yuna.config.schema import ConfigSchema
from yuna.config.types import ConfigValue, DerivedConfigKey
from yuna.exceptions import ConfigValidationError
from yuna.types.identifiers import EntityID

_UNRESOLVED = object()


@dataclass
class ConfigStore:
    """Centralized configuration storage.

    Stores:
    - Global defaults (override schema defaults)
    - Per-entity overrides
    - Resolved global cache (memoizes derived and static values alike;
      one dict lookup on repeat reads)

    Access pattern:
        store.get("board.width")
        store.get("cache.size", entity_id=bot_id)

    Fallback chain: entity override → global default → derived/static value
    """

    schema: ConfigSchema
    _global_defaults: dict[str, Any] = field(default_factory=dict)
    _entity_overrides: dict[EntityID, dict[str, Any]] = field(default_factory=dict)
    _resolved_globals: dict[str, ConfigValue] = field(default_factory=dict)

    def set(
        self,
        key: str,
        value: ConfigValue,
        entity_id: EntityID | None = None,
    ) -> None:
        """Set config value.

        Without entity_id: Sets global default (invalidates cache)
        With entity_id: Sets entity-specific override

        Example:
            store.set("board.width", 32)
            store.set("cache.size", 64, entity_id=bot_id)
        """
        config_key = self.schema.get_key(name=key)

        valid, reason = config_key.validate(value=value)
        if not valid:
            raise ConfigValidationError(f"Invalid value for {key}: {reason}")

        if entity_id is None:
            self._global_defaults[key] = value
            self.invalidate_cache()
        else:
            if entity_id not in self._entity_overrides:
                self._entity_overrides[entity_id] = {}
            self._entity_overrides[entity_id][key] = value

    def invalidate_cache(self, key: str | None = None) -> None:
        """Invalidate resolved value cache.

        Args:
            key: Specific key to invalidate, or None to clear all
        """
        if key is None:
            self._resolved_globals.clear()
        else:
            self._resolved_globals.pop(key, None)

    def get(self, key: str, entity_id: EntityID | None = None) -> ConfigValue:
        """Get config value with fallback chain + lazy evaluation.

        For derived keys: Evaluates formula lazily with memoization.
        For static keys: Uses existing fallback chain.

        Repeat global reads resolve via a flat cache that set(), merge(),
        and invalidate_cache() clear.

        Fallback chain: entity override → global default → derived/static value

        Example:
            width = store.get(key="board.width")
            cache_size = store.get(key="cache.size", entity_id=bot_id)
        """
        if entity_id is not None:
            self.schema.get_key(name=key)
            entity_value = self._get_entity_override(
                entity_id=entity_id,
                key=key,
            )
            if entity_value is not None:
                return entity_value

        resolved = self._resolved_globals.get(key, _UNRESOLVED)
        if resolved is not _UNRESOLVED:
            return cast(ConfigValue, resolved)

        value = self._resolve_global(key=key)
        self._resolved_globals[key] = value
        return value

    def _resolve_global(self, key: str) -> ConfigValue:
        """Resolve a key through the global fallback chain."""
        config_key = self.schema.get_key(name=key)

        if key in self._global_defaults:
            return cast(ConfigValue, self._global_defaults[key])

        if isinstance(config_key, DerivedConfigKey):
            return cast(ConfigValue, config_key.evaluate(resolver=self))
        return cast(ConfigValue, config_key.value)

    def get_min(self, key: str) -> ConfigValue | None:
        """Get minimum constraint value for a config key.

        Returns:
            Min value if constraints exist, None otherwise

        Example:
            min_cache = store.get_min(key="cache.size")
        """
        config_key = self.schema.get_key(name=key)
        if config_key.constraints is not None:
            return config_key.constraints.min_value
        return None

    def get_max(self, key: str) -> ConfigValue | None:
        """Get maximum constraint value for a config key.

        Returns:
            Max value if constraints exist, None otherwise

        Example:
            max_cache = store.get_max(key="cache.size")
        """
        config_key = self.schema.get_key(name=key)
        if config_key.constraints is not None:
            return config_key.constraints.max_value
        return None

    def clear_entity_override(self, entity_id: EntityID, key: str) -> None:
        """Remove entity-specific override."""
        self.schema.get_key(name=key)

        if entity_id in self._entity_overrides:
            self._entity_overrides[entity_id].pop(key, None)

    def clear_all_entity_overrides(self, entity_id: EntityID) -> None:
        """Remove all overrides for an entity."""
        self._entity_overrides.pop(entity_id, None)

    def get_all_entity_overrides(self, entity_id: EntityID) -> dict[str, Any]:
        """Get all overrides for an entity."""
        return dict(self._entity_overrides.get(entity_id, {}))

    def has_entity_override(self, entity_id: EntityID, key: str) -> bool:
        """Check if entity has override for key."""
        return (
            entity_id in self._entity_overrides
            and key in self._entity_overrides[entity_id]
        )

    def _get_entity_override(
        self,
        entity_id: EntityID,
        key: str,
    ) -> ConfigValue | None:
        """Get entity-specific override if exists."""
        if entity_id not in self._entity_overrides:
            return None
        return self._entity_overrides[entity_id].get(key)

    def merge(self, other: ConfigStore) -> None:
        """Merge another ConfigStore into this one.

        Copies both schema definitions AND runtime values (global defaults).
        This ensures that values set in the source config (like board dimensions)
        are available in the destination config.

        Example:
            board_config = ConfigStore(schema=board_schema)
            board_config.set(key="board.width", value=32)

            world_config = ConfigStore(schema=world_schema)
            world_config.merge(other=board_config)

            world_config.get(key="board.width")  # Returns 32, not schema default

        Args:
            other: ConfigStore to merge from
        """
        self.schema.merge(other.schema)

        for key, value in other._global_defaults.items():
            self._global_defaults[key] = value

        self.invalidate_cache()

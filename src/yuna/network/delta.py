"""Delta serialization for efficient state updates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from yuna.state.snapshot import WorldSnapshot
from yuna.types.identifiers import EntityID


@dataclass(frozen=True)
class Delta:
    """Represents changes between two snapshots.

    Responsibilities:
    - Track added entities and their components
    - Track removed entities
    - Track modified components
    - Store tick number for ordering

    Usage:
        delta = Delta(
            tick=101,
            added_entities={entity_id: {"Position": {"x": 10, "y": 20}}},
            removed_entities={old_entity_id},
            modified_components={entity_id: {"Health": {"current": 80}}},
        )
    """

    tick: int
    added_entities: dict[EntityID, dict[str, Any]] = field(default_factory=dict)
    removed_entities: set[EntityID] = field(default_factory=set)
    modified_components: dict[EntityID, dict[str, Any]] = field(default_factory=dict)


class DeltaSerializer:
    """Computes and applies deltas between world snapshots.

    Responsibilities:
    - Compute minimal delta between snapshots
    - Apply delta to base snapshot to produce new snapshot
    - Track only changed data for bandwidth efficiency

    Usage:
        serializer = DeltaSerializer()
        delta = serializer.compute_delta(
            old_snapshot=snapshot1,
            new_snapshot=snapshot2,
        )
        new_snapshot = serializer.apply_delta(
            base_snapshot=snapshot1,
            delta=delta,
        )
    """

    def compute_delta(
        self,
        old_snapshot: WorldSnapshot,
        new_snapshot: WorldSnapshot,
    ) -> Delta:
        """Compute delta between two snapshots.

        Args:
            old_snapshot: Previous snapshot
            new_snapshot: Current snapshot

        Returns:
            Delta containing only changes
        """
        added_entities: dict[EntityID, dict[str, Any]] = {}
        modified_components: dict[EntityID, dict[str, Any]] = {}

        old_entities = set(old_snapshot.entities.keys())
        new_entities = set(new_snapshot.entities.keys())

        added_entity_ids = new_entities - old_entities
        for entity_id in added_entity_ids:
            added_entities[entity_id] = new_snapshot.entities[entity_id]

        removed_entities = old_entities - new_entities

        existing_entities = old_entities & new_entities
        for entity_id in existing_entities:
            old_components = old_snapshot.entities[entity_id]
            new_components = new_snapshot.entities[entity_id]

            changed_components = self._find_changed_components(
                old_components=old_components,
                new_components=new_components,
            )

            if changed_components:
                modified_components[entity_id] = changed_components

        return Delta(
            tick=new_snapshot.tick,
            added_entities=added_entities,
            removed_entities=removed_entities,
            modified_components=modified_components,
        )

    @staticmethod
    def apply_delta(
        base_snapshot: WorldSnapshot,
        delta: Delta,
    ) -> WorldSnapshot:
        """Apply delta to base snapshot to produce new snapshot.

        Args:
            base_snapshot: Base snapshot to apply delta to
            delta: Delta containing changes

        Returns:
            New snapshot with delta applied
        """
        new_entities: dict[EntityID, dict[str, Any]] = {}

        for entity_id, components in base_snapshot.entities.items():
            if entity_id in delta.removed_entities:
                continue

            if entity_id in delta.modified_components:
                updated_components = dict(components)
                for component_type, component_data in delta.modified_components[
                    entity_id
                ].items():
                    if component_data is None:
                        updated_components.pop(component_type, None)
                    else:
                        updated_components[component_type] = component_data
                new_entities[entity_id] = updated_components
            else:
                new_entities[entity_id] = components

        for entity_id, components in delta.added_entities.items():
            new_entities[entity_id] = components

        return WorldSnapshot(
            tick=delta.tick,
            timestamp=base_snapshot.timestamp,
            entities=new_entities,
            metadata=base_snapshot.metadata,
        )

    @staticmethod
    def _find_changed_components(
        old_components: dict[str, Any],
        new_components: dict[str, Any],
    ) -> dict[str, Any]:
        """Find components that changed between snapshots.

        Args:
            old_components: Components from old snapshot
            new_components: Components from new snapshot

        Returns:
            Dictionary of changed components
        """
        changed: dict[str, Any] = {}

        all_component_types = set(old_components.keys()) | set(new_components.keys())

        for component_type in all_component_types:
            old_component = old_components.get(component_type)
            new_component = new_components.get(component_type)

            if old_component != new_component:
                changed[component_type] = new_component

        return changed

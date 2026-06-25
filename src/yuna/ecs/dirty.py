"""Dirty flag tracking for ECS components."""

from __future__ import annotations

from yuna.types.identifiers import EntityID


class DirtyFlag:
    """Tracks which components have been modified.

    Responsibilities:
    - Mark components as dirty when modified
    - Check dirty status for specific components
    - Clear dirty flags after processing
    - Query all dirty entities for a component type

    The dirty flag pattern allows systems to skip processing
    entities whose components haven't changed since last update.

    Usage:
        dirty = DirtyFlag()
        dirty.mark_dirty(entity_id=entity_id, component_type=Position)

        if dirty.is_dirty(entity_id=entity_id, component_type=Position):
            # Process this entity
            pass

        dirty.clear_dirty(entity_id=entity_id, component_type=Position)
    """

    def __init__(self) -> None:
        self._dirty: dict[type, set[EntityID]] = {}

    def mark_dirty(self, entity_id: EntityID, component_type: type) -> None:
        """Mark a component as dirty.

        Args:
            entity_id: Entity whose component changed
            component_type: Type of component that changed
        """
        if component_type not in self._dirty:
            self._dirty[component_type] = set()
        self._dirty[component_type].add(entity_id)

    def is_dirty(self, entity_id: EntityID, component_type: type) -> bool:
        """Check if a component is dirty.

        Args:
            entity_id: Entity to check
            component_type: Type of component to check

        Returns:
            True if component is dirty, False otherwise
        """
        if component_type not in self._dirty:
            return False
        return entity_id in self._dirty[component_type]

    def clear_dirty(self, entity_id: EntityID, component_type: type) -> None:
        """Clear dirty flag for a specific component.

        Args:
            entity_id: Entity whose flag to clear
            component_type: Type of component to clear
        """
        if component_type in self._dirty:
            self._dirty[component_type].discard(entity_id)

    def clear_all(self) -> None:
        """Clear all dirty flags."""
        self._dirty.clear()

    def get_dirty_entities(self, component_type: type) -> set[EntityID]:
        """Get all entities with dirty components of a specific type.

        Args:
            component_type: Type of component to query

        Returns:
            Set of entity IDs with dirty components (copy to prevent modification)
        """
        if component_type not in self._dirty:
            return set()
        return self._dirty[component_type].copy()

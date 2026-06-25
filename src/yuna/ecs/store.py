"""Component storage with data locality optimization."""

from __future__ import annotations

from typing import Any, TypeVar

from yuna.ecs.component import Component
from yuna.ecs.dirty import DirtyFlag
from yuna.ecs.lifecycle import ComponentLifecycle
from yuna.types.identifiers import EntityID

T = TypeVar("T", bound=Component)


class ComponentStore:
    """Stores components grouped by type for data locality.

    Responsibilities:
    - Store components organized by type
    - Add/remove components for entities
    - Query components by entity and type
    - Provide efficient iteration over component types

    Data locality: Components of same type stored together
    for better cache performance when processing systems.

    Usage:
        store = ComponentStore()
        store.add(entity_id=entity1, component=Position(x=10, y=20))
        position = store.get(entity_id=entity1, component_type=Position)
        all_positions = store.get_all(component_type=Position)
    """

    def __init__(
        self,
        dirty_flag: DirtyFlag | None = None,
        lifecycle: ComponentLifecycle | None = None,
    ) -> None:
        self._components: dict[type, dict[EntityID, Any]] = {}
        self._dirty_flag = dirty_flag if dirty_flag is not None else DirtyFlag()
        self._lifecycle = lifecycle if lifecycle is not None else ComponentLifecycle()

    def add(self, entity_id: EntityID, component: Component) -> None:
        """Add a component to an entity.

        Automatically marks the component as dirty and triggers lifecycle callbacks.

        Args:
            entity_id: Entity to add component to
            component: Component instance to add
        """
        component_type = type(component)
        if component_type not in self._components:
            self._components[component_type] = {}
        self._components[component_type][entity_id] = component

        self._dirty_flag.mark_dirty(entity_id=entity_id, component_type=component_type)

        self._lifecycle.on_component_added(
            entity_id=entity_id,
            component_type=component_type,
            component=component,
        )

    def remove(self, entity_id: EntityID, component_type: type[T]) -> None:
        """Remove a component from an entity.

        Triggers lifecycle callbacks before removal.

        Args:
            entity_id: Entity to remove component from
            component_type: Type of component to remove
        """
        if component_type in self._components:
            component = self._components[component_type].get(entity_id)
            if component is not None:
                self._lifecycle.on_component_removed(
                    entity_id=entity_id,
                    component_type=component_type,
                    component=component,
                )
            self._components[component_type].pop(entity_id, None)

    def get(self, entity_id: EntityID, component_type: type[T]) -> T | None:
        """Get a component from an entity.

        Args:
            entity_id: Entity to get component from
            component_type: Type of component to get

        Returns:
            Component instance or None if not found
        """
        if component_type not in self._components:
            return None
        return self._components[component_type].get(entity_id)

    def has(self, entity_id: EntityID, component_type: type[Component]) -> bool:
        """Check if entity has a component type.

        Args:
            entity_id: Entity to check
            component_type: Type of component to check for

        Returns:
            True if entity has component, False otherwise
        """
        if component_type not in self._components:
            return False
        return entity_id in self._components[component_type]

    def get_all(self, component_type: type[T]) -> dict[EntityID, T]:
        """Get all components of a specific type.

        Args:
            component_type: Type of components to get

        Returns:
            Dictionary mapping entity IDs to component instances
        """
        if component_type not in self._components:
            return {}
        return self._components[component_type].copy()

    def iter_items(self, component_type: type[T]) -> list[tuple[EntityID, T]]:
        """Get all components of a type as entity/component pairs.

        Cheaper than get_all() for read-only iteration: one list construction
        instead of a dict copy, preserving insertion order.

        Args:
            component_type: Type of components to get

        Returns:
            List of (entity ID, component) pairs
        """
        if component_type not in self._components:
            return []
        return list(self._components[component_type].items())

    def get_entity_ids(self, component_type: type[Component]) -> list[EntityID]:
        """Get IDs of all entities holding a component type.

        Args:
            component_type: Type of component to look up

        Returns:
            List of entity IDs in insertion order
        """
        if component_type not in self._components:
            return []
        return list(self._components[component_type])

    def get_map(self, component_type: type[T]) -> dict[EntityID, T]:
        """Get the live entity-to-component mapping for a type.

        Returns the internal storage dict for read-only access; callers
        must never mutate it. Mutations through add/remove stay visible
        to holders, matching repeated get() call semantics.

        Free-threading: only atomic per-entity lookups (`in`, `.get()`)
        are safe on the returned live dict during the kernel phase. Never
        Python-iterate it (`for ... in`) while kernels run, a concurrent
        add/remove can corrupt the iteration or crash the interpreter; use
        a snapshot (`iter_items`/`get_all`) instead.

        Args:
            component_type: Type of components to view

        Returns:
            Live mapping of entity IDs to component instances
        """
        if component_type not in self._components:
            return {}
        return self._components[component_type]

    def remove_all(self, entity_id: EntityID) -> None:
        """Remove all components from an entity.

        Triggers lifecycle callbacks for each component before removal.

        Args:
            entity_id: Entity to remove all components from
        """
        for component_type, components_by_entity in self._components.items():
            component = components_by_entity.get(entity_id)
            if component is not None:
                self._lifecycle.on_component_removed(
                    entity_id=entity_id,
                    component_type=component_type,
                    component=component,
                )
            components_by_entity.pop(entity_id, None)

    def get_component_types(self) -> set[type[Component]]:
        """Get all registered component types.

        Returns:
            Set of component types that have been added
        """
        return set(self._components.keys())

    def count(self, component_type: type[Component]) -> int:
        """Count number of entities with a specific component type.

        Args:
            component_type: Type of component to count

        Returns:
            Number of entities with this component type
        """
        if component_type not in self._components:
            return 0
        return len(self._components[component_type])

    def get_dirty_components(self, component_type: type[T]) -> dict[EntityID, T]:
        """Get only dirty components of a specific type.

        Args:
            component_type: Type of components to get

        Returns:
            Dictionary mapping entity IDs to dirty component instances
        """
        if component_type not in self._components:
            return {}

        dirty_entities = self._dirty_flag.get_dirty_entities(
            component_type=component_type
        )
        return {
            entity_id: component
            for entity_id, component in self._components[component_type].items()
            if entity_id in dirty_entities
        }

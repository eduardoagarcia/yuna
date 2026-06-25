"""Archetype-based component storage for high-performance ECS."""

from __future__ import annotations

from typing import TypeVar

from yuna.ecs.archetype import Archetype
from yuna.ecs.component import Component
from yuna.ecs.dirty import DirtyFlag
from yuna.ecs.lifecycle import ComponentLifecycle
from yuna.types.identifiers import EntityID

T = TypeVar("T", bound=Component)


class ArchetypeStore:
    """Manages archetypes for cache-friendly component storage.

    Responsibilities:
    - Create and manage archetypes by component signature
    - Handle entity migration between archetypes when components change
    - Provide efficient component lookup and queries
    - Optimize for cache-friendly iteration patterns

    Archetype approach groups entities with identical component sets together.
    When an entity's components change, it migrates to a different archetype.
    This enables extremely fast queries and iteration.

    Usage:
        store = ArchetypeStore()
        store.add(entity_id=entity_id, component=Position(x=0, y=0))
        store.add(entity_id=entity_id, component=Velocity(x=1, y=1))
        position = store.get(entity_id=entity_id, component_type=Position)
        archetypes = store.query_archetypes(component_types={Position, Velocity})
    """

    def __init__(
        self,
        dirty_flag: DirtyFlag | None = None,
        lifecycle: ComponentLifecycle | None = None,
    ) -> None:
        """Initialize archetype store.

        Args:
            dirty_flag: Optional dirty flag tracker for change detection
            lifecycle: Optional lifecycle hook manager for component events
        """
        self._archetypes: dict[frozenset[type], Archetype] = {}
        self._entity_to_archetype: dict[EntityID, Archetype] = {}
        self._entity_components: dict[EntityID, dict[type, Component]] = {}
        self._dirty_flag = dirty_flag if dirty_flag is not None else DirtyFlag()
        self._lifecycle = lifecycle if lifecycle is not None else ComponentLifecycle()

    def add(self, entity_id: EntityID, component: Component) -> None:
        """Add component to entity.

        Migrates entity to new archetype if component signature changes.

        Args:
            entity_id: Entity to add component to
            component: Component instance to add
        """
        component_type = type(component)

        if entity_id not in self._entity_components:
            self._entity_components[entity_id] = {}

        if component_type in self._entity_components[entity_id]:
            self._entity_components[entity_id][component_type] = component
            current_archetype = self._entity_to_archetype.get(entity_id)
            if current_archetype is not None:
                index = current_archetype._entity_to_index[entity_id]
                current_archetype._components[component_type][index] = component
        else:
            old_archetype = self._entity_to_archetype.get(entity_id)
            old_components = {}

            if old_archetype is not None:
                old_components = old_archetype.remove_entity(entity_id=entity_id)

            self._entity_components[entity_id][component_type] = component
            all_components = {**old_components, component_type: component}

            new_signature = frozenset(all_components.keys())
            new_archetype = self._get_or_create_archetype(component_types=new_signature)

            new_archetype.add_entity(entity_id=entity_id, components=all_components)
            self._entity_to_archetype[entity_id] = new_archetype

        self._dirty_flag.mark_dirty(entity_id=entity_id, component_type=component_type)

        self._lifecycle.on_component_added(
            entity_id=entity_id,
            component_type=component_type,
            component=component,
        )

    def remove(self, entity_id: EntityID, component_type: type[T]) -> None:
        """Remove component from entity.

        Migrates entity to new archetype without this component type.

        Args:
            entity_id: Entity to remove component from
            component_type: Type of component to remove
        """
        if entity_id not in self._entity_components:
            return

        if component_type not in self._entity_components[entity_id]:
            return

        component = self._entity_components[entity_id][component_type]
        self._lifecycle.on_component_removed(
            entity_id=entity_id,
            component_type=component_type,
            component=component,
        )

        old_archetype = self._entity_to_archetype.get(entity_id)
        if old_archetype is not None:
            old_components = old_archetype.remove_entity(entity_id=entity_id)
            del old_components[component_type]
        else:
            old_components = {**self._entity_components[entity_id]}
            del old_components[component_type]

        del self._entity_components[entity_id][component_type]

        if len(old_components) > 0:
            new_signature = frozenset(old_components.keys())
            new_archetype = self._get_or_create_archetype(component_types=new_signature)
            new_archetype.add_entity(entity_id=entity_id, components=old_components)
            self._entity_to_archetype[entity_id] = new_archetype
        elif entity_id in self._entity_to_archetype:
            del self._entity_to_archetype[entity_id]

    def get(self, entity_id: EntityID, component_type: type[T]) -> T | None:
        """Get component from entity.

        Args:
            entity_id: Entity to get component from
            component_type: Type of component to get

        Returns:
            Component instance or None if not found
        """
        if entity_id not in self._entity_components:
            return None

        return self._entity_components[entity_id].get(component_type)  # type: ignore[return-value]

    def has(self, entity_id: EntityID, component_type: type[Component]) -> bool:
        """Check if entity has component type.

        Args:
            entity_id: Entity to check
            component_type: Type of component to check for

        Returns:
            True if entity has component, False otherwise
        """
        if entity_id not in self._entity_components:
            return False

        return component_type in self._entity_components[entity_id]

    def get_all(self, component_type: type[T]) -> dict[EntityID, T]:
        """Get all components of a specific type.

        Args:
            component_type: Type of components to get

        Returns:
            Dictionary mapping entity IDs to component instances
        """
        result: dict[EntityID, T] = {}
        for entity_id, components in self._entity_components.items():
            if component_type in components:
                result[entity_id] = components[component_type]  # type: ignore[assignment]

        return result

    def iter_items(self, component_type: type[T]) -> list[tuple[EntityID, T]]:
        """Get all components of a type as entity/component pairs.

        Args:
            component_type: Type of components to get

        Returns:
            List of (entity ID, component) pairs
        """
        return [
            (entity_id, components[component_type])  # type: ignore[misc]
            for entity_id, components in self._entity_components.items()
            if component_type in components
        ]

    def get_entity_ids(self, component_type: type[Component]) -> list[EntityID]:
        """Get IDs of all entities holding a component type.

        Args:
            component_type: Type of component to look up

        Returns:
            List of entity IDs in insertion order
        """
        return [
            entity_id
            for entity_id, components in self._entity_components.items()
            if component_type in components
        ]

    def get_map(self, component_type: type[T]) -> dict[EntityID, T]:
        """Get the entity-to-component mapping for a type.

        Built per call because archetype storage is entity-major; treat
        the result as read-only for parity with ComponentStore.get_map.

        Args:
            component_type: Type of components to view

        Returns:
            Mapping of entity IDs to component instances
        """
        return self.get_all(component_type=component_type)

    def remove_all(self, entity_id: EntityID) -> None:
        """Remove all components from entity.

        Args:
            entity_id: Entity to remove all components from
        """
        if entity_id not in self._entity_components:
            return

        for component_type, component in list(
            self._entity_components[entity_id].items()
        ):
            self._lifecycle.on_component_removed(
                entity_id=entity_id,
                component_type=component_type,
                component=component,
            )

        archetype = self._entity_to_archetype.get(entity_id)
        if archetype is not None:
            archetype.remove_entity(entity_id=entity_id)
            del self._entity_to_archetype[entity_id]

        del self._entity_components[entity_id]

    def get_component_types(self) -> set[type[Component]]:
        """Get all registered component types.

        Returns:
            Set of component types that have been added
        """
        types: set[type[Component]] = set()
        for components in self._entity_components.values():
            types.update(components.keys())

        return types

    def count(self, component_type: type[Component]) -> int:
        """Count number of entities with a specific component type.

        Args:
            component_type: Type of component to count

        Returns:
            Number of entities with this component type
        """
        count = 0
        for components in self._entity_components.values():
            if component_type in components:
                count += 1

        return count

    def get_dirty_components(self, component_type: type[T]) -> dict[EntityID, T]:
        """Get only dirty components of a specific type.

        Args:
            component_type: Type of components to get

        Returns:
            Dictionary mapping entity IDs to dirty component instances
        """
        dirty_entities = self._dirty_flag.get_dirty_entities(
            component_type=component_type
        )
        result: dict[EntityID, T] = {}

        for entity_id in dirty_entities:
            if entity_id in self._entity_components:
                if component_type in self._entity_components[entity_id]:
                    result[entity_id] = self._entity_components[entity_id][
                        component_type
                    ]  # type: ignore[assignment]

        return result

    def query_archetypes(
        self,
        component_types: set[type],
    ) -> list[Archetype]:
        """Find all archetypes containing specified component types.

        This is the key optimization: instead of filtering entities one by one,
        we filter archetypes. An archetype with 1000 entities is a single check.

        Matching archetypes are sorted by their component signature so iteration
        order is deterministic regardless of dict insertion order.

        Args:
            component_types: Set of component types to query for

        Returns:
            List of archetypes that contain all specified component types
        """
        matching_archetypes: list[Archetype] = []

        for signature in sorted(
            self._archetypes.keys(),
            key=lambda types: sorted(comp_type.__name__ for comp_type in types),
        ):
            archetype = self._archetypes[signature]
            if component_types.issubset(archetype.component_types):
                matching_archetypes.append(archetype)

        return matching_archetypes

    def get_archetype(
        self,
        entity_id: EntityID,
    ) -> Archetype | None:
        """Get archetype containing entity.

        Args:
            entity_id: Entity to find archetype for

        Returns:
            Archetype containing entity or None if entity has no components
        """
        return self._entity_to_archetype.get(entity_id)

    def _get_or_create_archetype(
        self,
        component_types: frozenset[type],
    ) -> Archetype:
        """Get existing archetype or create new one for component signature.

        Args:
            component_types: Component types defining the archetype

        Returns:
            Archetype for this component signature
        """
        if component_types not in self._archetypes:
            self._archetypes[component_types] = Archetype(
                component_types=component_types
            )

        return self._archetypes[component_types]

    @property
    def archetype_count(self) -> int:
        """Get number of unique archetypes.

        Returns:
            Number of archetypes in the store
        """
        return len(self._archetypes)

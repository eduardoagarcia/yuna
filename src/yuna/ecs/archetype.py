"""Archetype storage for cache-friendly component iteration."""

from __future__ import annotations

from yuna.ecs.component import Component
from yuna.exceptions import StateError, ValidationError
from yuna.types.identifiers import EntityID


class Archetype:
    """Groups entities with identical component signatures.

    Responsibilities:
    - Store entities sharing the same component types
    - Organize components in columnar layout for cache locality
    - Add/remove entities maintaining data layout
    - Provide efficient component access and iteration

    Data locality: All Position components stored contiguously in memory,
    all Velocity components together, etc. Enables efficient iteration.

    Usage:
        archetype = Archetype(component_types=frozenset({Position, Velocity}))
        archetype.add_entity(
            entity_id=entity_id,
            components={Position: Position(x=0, y=0), Velocity: Velocity(x=1, y=1)},
        )
        position = archetype.get_component(entity_id=entity_id, component_type=Position)
    """

    def __init__(self, component_types: frozenset[type]) -> None:
        """Initialize archetype with component signature.

        Args:
            component_types: Frozenset of component types defining this archetype
        """
        self._component_types = component_types
        self._entities: list[EntityID] = []
        self._components: dict[type, list[Component]] = {
            comp_type: [] for comp_type in component_types
        }
        self._entity_to_index: dict[EntityID, int] = {}

    @property
    def component_types(self) -> frozenset[type]:
        """Get component types defining this archetype.

        Returns:
            Frozenset of component types
        """
        return self._component_types

    @property
    def entities(self) -> list[EntityID]:
        """Get all entities in this archetype.

        Returns:
            List of entity IDs (do not modify directly)
        """
        return self._entities.copy()

    @property
    def entity_count(self) -> int:
        """Get number of entities in this archetype.

        Returns:
            Entity count
        """
        return len(self._entities)

    def add_entity(
        self,
        entity_id: EntityID,
        components: dict[type, Component],
    ) -> None:
        """Add entity to archetype with its components.

        Args:
            entity_id: Entity to add
            components: Dictionary mapping component types to instances

        Raises:
            ValidationError: If components don't match archetype signature
            StateError: If entity already in archetype
        """
        if frozenset(components.keys()) != self._component_types:
            raise ValidationError(
                reason=(
                    f"Components {set(components.keys())} don't match archetype "
                    f"signature {self._component_types}"
                ),
                field="components",
                value=str(set(components.keys())),
            )

        if entity_id in self._entity_to_index:
            raise StateError(
                operation="add_entity",
                reason=f"Entity {entity_id} already in archetype",
            )

        index = len(self._entities)
        self._entities.append(entity_id)
        self._entity_to_index[entity_id] = index

        for comp_type in self._component_types:
            self._components[comp_type].append(components[comp_type])

    def remove_entity(self, entity_id: EntityID) -> dict[type, Component]:
        """Remove entity from archetype.

        Uses swap-and-pop for O(1) removal while maintaining data locality.

        Args:
            entity_id: Entity to remove

        Returns:
            Dictionary of removed components

        Raises:
            ValidationError: If entity not in archetype
        """
        if entity_id not in self._entity_to_index:
            raise ValidationError(
                reason=f"Entity {entity_id} not in archetype",
                field="entity_id",
                value=entity_id,
            )

        index = self._entity_to_index[entity_id]
        last_index = len(self._entities) - 1

        removed_components: dict[type, Component] = {}
        for comp_type in self._component_types:
            removed_components[comp_type] = self._components[comp_type][index]
            if index != last_index:
                self._components[comp_type][index] = self._components[comp_type][
                    last_index
                ]
            self._components[comp_type].pop()

        if index != last_index:
            last_entity = self._entities[last_index]
            self._entities[index] = last_entity
            self._entity_to_index[last_entity] = index

        self._entities.pop()
        del self._entity_to_index[entity_id]

        return removed_components

    def get_component(
        self,
        entity_id: EntityID,
        component_type: type,
    ) -> Component | None:
        """Get component from entity in this archetype.

        Args:
            entity_id: Entity to get component from
            component_type: Type of component to retrieve

        Returns:
            Component instance or None if entity not in archetype or type not
            in signature
        """
        if entity_id not in self._entity_to_index:
            return None

        if component_type not in self._component_types:
            return None

        index = self._entity_to_index[entity_id]
        return self._components[component_type][index]

    def has_entity(self, entity_id: EntityID) -> bool:
        """Check if entity is in this archetype.

        Args:
            entity_id: Entity to check

        Returns:
            True if entity is in this archetype
        """
        return entity_id in self._entity_to_index

    def get_components_column(self, component_type: type) -> list[Component]:
        """Get all components of a specific type (columnar access).

        Provides direct access to component column for efficient iteration.

        Args:
            component_type: Type of components to get

        Returns:
            List of all components of this type (do not modify directly)

        Raises:
            ValidationError: If component type not in archetype signature
        """
        if component_type not in self._component_types:
            raise ValidationError(
                reason=f"Component type {component_type} not in archetype signature",
                field="component_type",
                value=str(component_type),
            )

        return self._components[component_type].copy()

    def iter_components(
        self,
        component_types: list[type],
    ) -> list[tuple[EntityID, tuple[Component, ...]]]:
        """Iterate over entities with selected components.

        Args:
            component_types: List of component types to retrieve (must be subset of
            archetype)

        Returns:
            List of tuples (entity_id, (component1, component2, ...))

        Raises:
            ValidationError: If requested types not in archetype signature
        """
        for comp_type in component_types:
            if comp_type not in self._component_types:
                raise ValidationError(
                    reason=f"Component type {comp_type} not in archetype signature",
                    field="component_type",
                    value=str(comp_type),
                )

        result: list[tuple[EntityID, tuple[Component, ...]]] = []
        for i, entity_id in enumerate(self._entities):
            components = tuple(
                self._components[comp_type][i] for comp_type in component_types
            )
            result.append((entity_id, components))

        return result

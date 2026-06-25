"""Prototype pattern for cloning entities."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from yuna.exceptions import EntityNotFoundError, StateError

if TYPE_CHECKING:
    from yuna.ecs.world import ECSWorld

from yuna.types.identifiers import EntityID


class PrototypeManager:
    """Manages entity prototypes and cloning.

    Responsibilities:
    - Register entities as reusable templates
    - Clone entities from registered prototypes
    - Clone arbitrary entities
    - Deep copy all components to prevent shared state

    The Prototype pattern allows creating new entities by copying existing ones,
    avoiding the need to manually reconstruct complex entity configurations.

    Usage:
        manager = PrototypeManager(world=world)

        # Create and configure an entity
        template_entity = world.create_entity()
        world.add_component(entity_id=template_entity, component=Position(x=0, y=0))
        world.add_component(entity_id=template_entity, component=Health(hp=100))

        # Register as prototype
        manager.register_prototype(name="soldier", entity_id=template_entity)

        # Clone from prototype
        soldier1 = manager.clone(prototype_name="soldier")
        soldier2 = manager.clone(prototype_name="soldier")

        # Clone any entity (doesn't need to be registered)
        copy = manager.clone_entity(entity_id=soldier1)
    """

    def __init__(self, world: ECSWorld) -> None:
        self._world = world
        self._prototypes: dict[str, EntityID] = {}

    def register_prototype(self, name: str, entity_id: EntityID) -> None:
        """Register an entity as a prototype template.

        Args:
            name: Name to identify this prototype
            entity_id: Entity to use as template

        Raises:
            StateError: If prototype name already exists
            EntityNotFoundError: If entity does not exist
        """
        if name in self._prototypes:
            raise StateError(
                operation="register_prototype",
                reason=f"Prototype '{name}' is already registered",
            )

        if entity_id not in self._world.get_all_entities():
            raise EntityNotFoundError(
                entity_id=entity_id,
                message="Cannot register prototype for non-existent entity",
            )

        self._prototypes[name] = entity_id

    def has_prototype(self, name: str) -> bool:
        """Check if prototype exists.

        Args:
            name: Prototype name to check

        Returns:
            True if prototype is registered, False otherwise
        """
        return name in self._prototypes

    def get_prototype(self, name: str) -> EntityID:
        """Get prototype entity ID by name.

        Args:
            name: Prototype name

        Returns:
            Entity ID of the prototype

        Raises:
            KeyError: If prototype does not exist
        """
        if name not in self._prototypes:
            raise KeyError(f"Prototype '{name}' not found")

        return self._prototypes[name]

    def unregister_prototype(self, name: str) -> None:
        """Remove prototype from registry.

        Args:
            name: Prototype name to remove

        Raises:
            KeyError: If prototype does not exist
        """
        if name not in self._prototypes:
            raise KeyError(f"Prototype '{name}' not found")

        del self._prototypes[name]

    def get_all_prototypes(self) -> dict[str, EntityID]:
        """Get all registered prototypes.

        Returns:
            Dictionary mapping prototype names to entity IDs
        """
        return self._prototypes.copy()

    def clone(self, prototype_name: str) -> EntityID:
        """Create a new entity by cloning a registered prototype.

        Args:
            prototype_name: Name of prototype to clone

        Returns:
            New entity ID with copied components

        Raises:
            KeyError: If prototype does not exist
        """
        if prototype_name not in self._prototypes:
            raise KeyError(f"Prototype '{prototype_name}' not found")

        source_entity = self._prototypes[prototype_name]
        return self.clone_entity(entity_id=source_entity)

    def clone_entity(self, entity_id: EntityID) -> EntityID:
        """Clone any entity, creating a deep copy.

        Args:
            entity_id: Entity to clone

        Returns:
            New entity ID with copied components

        Raises:
            EntityNotFoundError: If entity does not exist
        """
        if entity_id not in self._world.get_all_entities():
            raise EntityNotFoundError(
                entity_id=entity_id,
                message="Cannot clone non-existent entity",
            )

        new_entity = self._world.create_entity()

        for component_type in self._world.get_component_types():
            component = self._world.get_component(
                entity_id=entity_id, component_type=component_type
            )

            if component is not None:
                cloned_component = deepcopy(component)
                self._world.add_component(
                    entity_id=new_entity, component=cloned_component
                )

        return new_entity

    def clear(self) -> None:
        """Remove all registered prototypes."""
        self._prototypes.clear()

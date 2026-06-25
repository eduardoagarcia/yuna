"""Entity relationship management."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yuna.types.identifiers import EntityID


class RelationshipManager:
    """Manages relationships between entities.

    Responsibilities:
    - Track arbitrary relationships between entities
    - Support bidirectional queries
    - Clean up relationships when entities destroyed
    - Support multiple relationship types

    Usage:
        manager = RelationshipManager()
        manager.add_relationship(
            from_entity=entity_a,
            to_entity=entity_b,
            relationship_type="targets",
        )
        targets = manager.get_relationships(
            entity_id=entity_a,
            relationship_type="targets",
        )
    """

    def __init__(self) -> None:
        self._forward: dict[str, dict[EntityID, set[EntityID]]] = {}
        self._reverse: dict[str, dict[EntityID, set[EntityID]]] = {}

    def add_relationship(
        self,
        from_entity: EntityID,
        to_entity: EntityID,
        relationship_type: str,
    ) -> None:
        """Create relationship between entities.

        Args:
            from_entity: Source entity
            to_entity: Target entity
            relationship_type: Type of relationship (arbitrary string)
        """
        if relationship_type not in self._forward:
            self._forward[relationship_type] = {}
        if relationship_type not in self._reverse:
            self._reverse[relationship_type] = {}

        if from_entity not in self._forward[relationship_type]:
            self._forward[relationship_type][from_entity] = set()
        if to_entity not in self._reverse[relationship_type]:
            self._reverse[relationship_type][to_entity] = set()

        self._forward[relationship_type][from_entity].add(to_entity)
        self._reverse[relationship_type][to_entity].add(from_entity)

    def remove_relationship(
        self,
        from_entity: EntityID,
        to_entity: EntityID,
        relationship_type: str,
    ) -> None:
        """Remove relationship between entities.

        Args:
            from_entity: Source entity
            to_entity: Target entity
            relationship_type: Type of relationship
        """
        if relationship_type not in self._forward:
            return

        if from_entity in self._forward[relationship_type]:
            self._forward[relationship_type][from_entity].discard(to_entity)
            if not self._forward[relationship_type][from_entity]:
                del self._forward[relationship_type][from_entity]

        if to_entity in self._reverse[relationship_type]:
            self._reverse[relationship_type][to_entity].discard(from_entity)
            if not self._reverse[relationship_type][to_entity]:
                del self._reverse[relationship_type][to_entity]

    def get_relationships(
        self,
        entity_id: EntityID,
        relationship_type: str,
        direction: str = "forward",
    ) -> set[EntityID]:
        """Get all entities related to given entity.

        Args:
            entity_id: Entity to query
            relationship_type: Type of relationship
            direction: "forward" for outgoing, "reverse" for incoming

        Returns:
            Set of related entity IDs
        """
        if direction == "forward":
            if relationship_type not in self._forward:
                return set()
            return self._forward[relationship_type].get(entity_id, set()).copy()

        if relationship_type not in self._reverse:
            return set()
        return self._reverse[relationship_type].get(entity_id, set()).copy()

    def has_relationship(
        self,
        from_entity: EntityID,
        to_entity: EntityID,
        relationship_type: str,
    ) -> bool:
        """Check if relationship exists.

        Args:
            from_entity: Source entity
            to_entity: Target entity
            relationship_type: Type of relationship

        Returns:
            True if relationship exists
        """
        if relationship_type not in self._forward:
            return False
        if from_entity not in self._forward[relationship_type]:
            return False
        return to_entity in self._forward[relationship_type][from_entity]

    def remove_all_relationships(self, entity_id: EntityID) -> None:
        """Remove all relationships involving entity.

        Called when entity is destroyed.

        Args:
            entity_id: Entity being destroyed
        """
        for relationship_type in list(self._forward.keys()):
            if entity_id in self._forward[relationship_type]:
                to_entities = list(self._forward[relationship_type][entity_id])
                for to_entity in to_entities:
                    self.remove_relationship(
                        from_entity=entity_id,
                        to_entity=to_entity,
                        relationship_type=relationship_type,
                    )

        for relationship_type in list(self._reverse.keys()):
            if entity_id in self._reverse[relationship_type]:
                from_entities = list(self._reverse[relationship_type][entity_id])
                for from_entity in from_entities:
                    self.remove_relationship(
                        from_entity=from_entity,
                        to_entity=entity_id,
                        relationship_type=relationship_type,
                    )

    def get_all_relationship_types(self) -> set[str]:
        """Get all registered relationship types.

        Returns:
            Set of relationship type strings
        """
        return set(self._forward.keys()) | set(self._reverse.keys())

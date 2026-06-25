"""Entity management for the ECS system."""

from __future__ import annotations

import threading
import uuid

from yuna.exceptions import StateError
from yuna.types.identifiers import EntityID


class EntityManager:
    """Manages entity lifecycle in the ECS.

    Responsibilities:
    - Create unique entity identifiers (deterministically based on seed)
    - Track entity existence
    - Mark entities for destruction
    - Flush destroyed entities at end of frame

    Usage:
        manager = EntityManager(seed=42)
        entity_id = manager.create(name="player")
        manager.destroy(entity_id=entity_id)
        destroyed = manager.flush_destroyed()
    """

    def __init__(self, seed: int = 0) -> None:
        self._entities: set[EntityID] = set()
        self._destroyed: set[EntityID] = set()
        self._names: dict[EntityID, str] = {}
        self._namespace = uuid.uuid5(uuid.NAMESPACE_OID, f"ecs_seed_{seed}")
        self._creation_counter = 0
        self._creation_lock = threading.Lock()

    def create(
        self,
        name: str | None = None,
        entity_id: EntityID | None = None,
    ) -> EntityID:
        """Create a new entity.

        When entity_id is provided, uses that ID directly (for external IDs).
        Otherwise generates a deterministic ID based on seed and counter;
        counter-derived IDs are only deterministic when creations happen in
        a deterministic order (single-threaded game phases). Concurrent
        callers must pre-derive their IDs via derive_id() instead.

        Args:
            name: Optional human-readable name for debugging
            entity_id: Optional explicit ID to use instead of generating one

        Returns:
            Unique entity identifier

        Raises:
            StateError: If an explicit entity_id is already registered
        """
        with self._creation_lock:
            if entity_id is None:
                entity_id = EntityID(
                    str(uuid.uuid5(self._namespace, str(self._creation_counter)))
                )
            elif entity_id in self._entities:
                raise StateError(
                    operation="create_entity",
                    state="duplicate",
                    reason=f"Entity {entity_id} already exists",
                )
            self._creation_counter += 1
            self._entities.add(entity_id)
        if name is not None:
            self._names[entity_id] = name
        return entity_id

    def derive_id(self, name: str) -> EntityID:
        """Derive a deterministic entity ID from a caller-provided name.

        The ID is a pure function of the manager's seed namespace and the
        name, independent of creation order, so concurrent callers get
        scheduling-independent IDs. The name must be unique per entity.

        Args:
            name: Unique derivation name for the entity

        Returns:
            Deterministic entity identifier (not yet registered)
        """
        return EntityID(str(uuid.uuid5(self._namespace, f"derived:{name}")))

    def destroy(self, entity_id: EntityID) -> None:
        """Mark entity for destruction.

        Entity is not immediately removed but marked for cleanup
        at end of frame via flush_destroyed().

        Args:
            entity_id: Entity to mark for destruction
        """
        if entity_id in self._entities:
            self._destroyed.add(entity_id)

    def exists(self, entity_id: EntityID) -> bool:
        """Check if entity exists and is not marked for destruction.

        Args:
            entity_id: Entity to check

        Returns:
            True if entity exists and is not destroyed
        """
        return entity_id in self._entities and entity_id not in self._destroyed

    def flush_destroyed(self) -> set[EntityID]:
        """Remove all destroyed entities and return their IDs.

        Returns:
            Set of entity IDs that were destroyed
        """
        destroyed_copy = self._destroyed.copy()
        for entity_id in sorted(destroyed_copy):
            self._entities.discard(entity_id)
            self._names.pop(entity_id, None)
        self._destroyed.clear()
        return destroyed_copy

    def get_name(self, entity_id: EntityID) -> str | None:
        """Get the name of an entity if it has one.

        Args:
            entity_id: Entity to get name for

        Returns:
            Entity name or None if unnamed
        """
        return self._names.get(entity_id)

    def count(self) -> int:
        """Get total number of active entities.

        Returns:
            Number of entities (excluding destroyed)
        """
        return len(self._entities) - len(self._destroyed)

    def add_existing(self, entity_id: EntityID) -> None:
        """Add an existing entity ID (used for deserialization).

        Args:
            entity_id: Entity ID to add
        """
        self._entities.add(entity_id)

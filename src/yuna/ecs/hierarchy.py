"""Entity hierarchy management."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yuna.types.identifiers import EntityID


class CircularHierarchyError(Exception):
    """Raised when attempting to create circular hierarchy."""


class HierarchyManager:
    """Manages parent-child hierarchies between entities.

    Responsibilities:
    - Track parent-child relationships
    - Enforce single-parent constraint
    - Prevent circular hierarchies
    - Provide recursive queries (ancestors, descendants)
    - Support recursive destruction

    Usage:
        manager = HierarchyManager()
        manager.set_parent(child_id=entity_b, parent_id=entity_a)
        children = manager.get_children(entity_id=entity_a)
        descendants = manager.get_descendants(entity_id=entity_a)
    """

    def __init__(self) -> None:
        self._parent: dict[EntityID, EntityID] = {}
        self._children: dict[EntityID, list[EntityID]] = {}

    def set_parent(self, child_id: EntityID, parent_id: EntityID) -> None:
        """Establish parent-child relationship.

        Enforces single-parent constraint and prevents cycles.

        Args:
            child_id: Child entity
            parent_id: Parent entity

        Raises:
            CircularHierarchyError: If setting parent would create cycle
        """
        if self._would_create_cycle(child_id=child_id, parent_id=parent_id):
            raise CircularHierarchyError(
                f"Setting parent {parent_id} for {child_id} would create cycle"
            )

        old_parent = self._parent.get(child_id)
        if old_parent is not None:
            self._children[old_parent].remove(child_id)
            if not self._children[old_parent]:
                del self._children[old_parent]

        self._parent[child_id] = parent_id

        if parent_id not in self._children:
            self._children[parent_id] = []
        self._children[parent_id].append(child_id)

    def remove_parent(self, child_id: EntityID) -> None:
        """Remove parent from child.

        Args:
            child_id: Child entity
        """
        parent_id = self._parent.get(child_id)
        if parent_id is None:
            return

        del self._parent[child_id]

        if parent_id in self._children:
            self._children[parent_id].remove(child_id)
            if not self._children[parent_id]:
                del self._children[parent_id]

    def get_parent(self, entity_id: EntityID) -> EntityID | None:
        """Get parent entity.

        Args:
            entity_id: Entity to query

        Returns:
            Parent entity ID or None if no parent
        """
        return self._parent.get(entity_id)

    def get_children(self, entity_id: EntityID) -> list[EntityID]:
        """Get all direct children.

        Args:
            entity_id: Entity to query

        Returns:
            List of child entity IDs
        """
        return self._children.get(entity_id, []).copy()

    def get_descendants(self, entity_id: EntityID) -> list[EntityID]:
        """Get all descendants recursively.

        Args:
            entity_id: Entity to query

        Returns:
            List of all descendant entity IDs (depth-first order)
        """
        descendants: list[EntityID] = []
        children = self.get_children(entity_id=entity_id)

        for child_id in children:
            descendants.append(child_id)
            descendants.extend(self.get_descendants(entity_id=child_id))

        return descendants

    def get_ancestors(self, entity_id: EntityID) -> list[EntityID]:
        """Get all ancestors recursively.

        Args:
            entity_id: Entity to query

        Returns:
            List of all ancestor entity IDs (root last)
        """
        ancestors: list[EntityID] = []
        current_id = entity_id

        while True:
            parent_id = self.get_parent(entity_id=current_id)
            if parent_id is None:
                break
            ancestors.append(parent_id)
            current_id = parent_id

        return ancestors

    def get_root(self, entity_id: EntityID) -> EntityID:
        """Find root of hierarchy.

        Args:
            entity_id: Entity to query

        Returns:
            Root entity ID (topmost ancestor or self if no parent)
        """
        ancestors = self.get_ancestors(entity_id=entity_id)
        if not ancestors:
            return entity_id
        return ancestors[-1]

    def get_entities_to_destroy(self, entity_id: EntityID) -> list[EntityID]:
        """Get entity and all descendants for recursive destruction.

        Args:
            entity_id: Root entity to destroy

        Returns:
            List of entity IDs to destroy (descendants first, then root)
        """
        descendants = self.get_descendants(entity_id=entity_id)
        descendants.reverse()
        descendants.append(entity_id)
        return descendants

    def remove_entity(self, entity_id: EntityID) -> None:
        """Remove entity from hierarchy.

        Called when entity is destroyed. Orphans children.

        Args:
            entity_id: Entity being destroyed
        """
        self.remove_parent(child_id=entity_id)

        children = self.get_children(entity_id=entity_id)
        for child_id in children:
            del self._parent[child_id]

        if entity_id in self._children:
            del self._children[entity_id]

    def _would_create_cycle(self, child_id: EntityID, parent_id: EntityID) -> bool:
        """Check if setting parent would create circular hierarchy.

        Args:
            child_id: Proposed child
            parent_id: Proposed parent

        Returns:
            True if would create cycle
        """
        if child_id == parent_id:
            return True

        current_id = parent_id
        while True:
            parent = self.get_parent(entity_id=current_id)
            if parent is None:
                return False
            if parent == child_id:
                return True
            current_id = parent

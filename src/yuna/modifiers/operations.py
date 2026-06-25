"""Bulk operations on modifier collections."""

from yuna.modifiers.pipeline import ModifierPipeline
from yuna.modifiers.query import ModifierQuery
from yuna.types.identifiers import EntityID


class ModifierOperations:
    """Bulk operations on modifier collections.

    Provides high-level operations for manipulating groups of modifiers
    based on semantic properties (tags, categories).

    Usage:
        operations = ModifierOperations(pipeline=modifier_pipeline)

        operations.remove_by_tag(entity_id=player_id, tag="temporary")

        total = operations.get_stat_total_by_category(
            entity_id=player_id,
            stat="damage",
            category="equipment",
        )

        has_immunity = operations.has_modifier_with_tag(
            entity_id=player_id,
            tag="immunity",
        )
    """

    def __init__(self, pipeline: ModifierPipeline) -> None:
        """Initialize operations with pipeline reference.

        Args:
            pipeline: ModifierPipeline instance to operate on
        """
        self._pipeline = pipeline
        self._query = ModifierQuery(tracker=pipeline.tracker)

    def remove_by_tag(
        self,
        entity_id: EntityID,
        tag: str,
    ) -> int:
        """Remove all modifiers with tag from entity.

        Args:
            entity_id: Target entity
            tag: Tag to match for removal

        Returns:
            Number of modifiers removed
        """
        modifiers_to_remove = (
            self._query.for_entity(entity_id=entity_id).with_tag(tag=tag).execute()
        )

        for modifier in modifiers_to_remove:
            self._pipeline.tracker.remove_modifier(modifier=modifier)

        return len(modifiers_to_remove)

    def remove_by_category(
        self,
        entity_id: EntityID,
        category: str,
    ) -> int:
        """Remove all modifiers in category from entity.

        Args:
            entity_id: Target entity
            category: Category to match for removal

        Returns:
            Number of modifiers removed
        """
        modifiers_to_remove = (
            self._query
            .for_entity(entity_id=entity_id)
            .in_category(category=category)
            .execute()
        )

        for modifier in modifiers_to_remove:
            self._pipeline.tracker.remove_modifier(modifier=modifier)

        return len(modifiers_to_remove)

    def clear_entity_modifiers(
        self,
        entity_id: EntityID,
        preserve_tags: frozenset[str] = frozenset(),
    ) -> int:
        """Remove all modifiers from entity, optionally preserving tagged ones.

        Args:
            entity_id: Target entity
            preserve_tags: Tags to preserve (modifiers with these tags won't be removed)

        Returns:
            Number of modifiers removed
        """
        all_modifiers = self._query.for_entity(entity_id=entity_id).execute()

        modifiers_to_remove = [m for m in all_modifiers if not (m.tags & preserve_tags)]

        for modifier in modifiers_to_remove:
            self._pipeline.tracker.remove_modifier(modifier=modifier)

        return len(modifiers_to_remove)

    def get_stat_total_by_category(
        self,
        entity_id: EntityID,
        stat: str,
        category: str,
    ) -> float:
        """Calculate total modification from specific category.

        Args:
            entity_id: Target entity
            stat: Stat name
            category: Category to sum

        Returns:
            Sum of all modifier values from category for stat
        """
        modifiers = (
            self._query
            .for_entity(entity_id=entity_id)
            .affecting_stat(stat=stat)
            .in_category(category=category)
            .execute()
        )

        return sum(m.value for m in modifiers)

    def has_modifier_with_tag(
        self,
        entity_id: EntityID,
        tag: str,
    ) -> bool:
        """Check if entity has any modifier with tag.

        Args:
            entity_id: Target entity
            tag: Tag to check

        Returns:
            True if entity has at least one modifier with tag
        """
        count = self._query.for_entity(entity_id=entity_id).with_tag(tag=tag).count()

        return count > 0

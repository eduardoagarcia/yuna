"""Query interface for modifier filtering."""

from collections.abc import Callable

from yuna.modifiers.modifier import Modifier
from yuna.modifiers.tracker import ModifierTracker
from yuna.types.identifiers import EntityID


class ModifierQuery:
    """Query interface for modifier filtering.

    Provides fluent API for building complex modifier queries with chaining.

    Usage:
        query = ModifierQuery(tracker=modifier_tracker)
        buffs = query.for_entity(entity_id).with_tag("buff").execute()

        debuff_count = (
            query.for_entity(entity_id).with_any_tag("debuff", "curse").count()
        )

        first_temporary = query.with_tag("temporary").first()
    """

    def __init__(self, tracker: ModifierTracker) -> None:
        """Initialize query with tracker reference.

        Args:
            tracker: ModifierTracker instance to query
        """
        self._tracker = tracker
        self._filters: list[Callable[[Modifier], bool]] = []

    def with_tag(self, tag: str) -> ModifierQuery:
        """Filter modifiers with specific tag.

        Args:
            tag: Tag to match

        Returns:
            Self for method chaining
        """

        def tag_filter(modifier: Modifier) -> bool:
            return tag in modifier.tags

        self._filters.append(tag_filter)
        return self

    def with_any_tag(self, *tags: str) -> ModifierQuery:
        """Filter modifiers with any of the tags.

        Args:
            *tags: Tags to match (OR operation)

        Returns:
            Self for method chaining
        """
        tag_set = frozenset(tags)

        def any_tag_filter(modifier: Modifier) -> bool:
            return bool(modifier.tags & tag_set)

        self._filters.append(any_tag_filter)
        return self

    def with_all_tags(self, *tags: str) -> ModifierQuery:
        """Filter modifiers with all tags.

        Args:
            *tags: Tags to match (AND operation)

        Returns:
            Self for method chaining
        """
        tag_set = frozenset(tags)

        def all_tags_filter(modifier: Modifier) -> bool:
            return tag_set.issubset(modifier.tags)

        self._filters.append(all_tags_filter)
        return self

    def without_tag(self, tag: str) -> ModifierQuery:
        """Filter modifiers without specific tag.

        Args:
            tag: Tag to exclude

        Returns:
            Self for method chaining
        """

        def without_tag_filter(modifier: Modifier) -> bool:
            return tag not in modifier.tags

        self._filters.append(without_tag_filter)
        return self

    def in_category(self, category: str) -> ModifierQuery:
        """Filter modifiers in specific category.

        Args:
            category: Category to match

        Returns:
            Self for method chaining
        """

        def category_filter(modifier: Modifier) -> bool:
            return category in modifier.categories

        self._filters.append(category_filter)
        return self

    def for_entity(self, entity_id: EntityID) -> ModifierQuery:
        """Filter modifiers targeting specific entity.

        Args:
            entity_id: Entity to match

        Returns:
            Self for method chaining
        """

        def entity_filter(modifier: Modifier) -> bool:
            return modifier.entity_id == entity_id

        self._filters.append(entity_filter)
        return self

    def affecting_stat(self, stat: str) -> ModifierQuery:
        """Filter modifiers affecting specific stat.

        Args:
            stat: Stat name to match

        Returns:
            Self for method chaining
        """

        def stat_filter(modifier: Modifier) -> bool:
            return modifier.stat == stat

        self._filters.append(stat_filter)
        return self

    def from_source(self, source: str) -> ModifierQuery:
        """Filter modifiers from specific source.

        Args:
            source: Source identifier to match

        Returns:
            Self for method chaining
        """

        def source_filter(modifier: Modifier) -> bool:
            return modifier.source == source

        self._filters.append(source_filter)
        return self

    def execute(self) -> list[Modifier]:
        """Execute query and return matching modifiers.

        Returns:
            List of modifiers matching all filters
        """
        all_modifiers = self._tracker.get_all_modifiers()

        result = all_modifiers
        for filter_fn in self._filters:
            result = [m for m in result if filter_fn(m)]

        return result

    def count(self) -> int:
        """Count matching modifiers without materializing list.

        Returns:
            Number of modifiers matching all filters
        """
        return len(self.execute())

    def first(self) -> Modifier | None:
        """Get first matching modifier or None.

        Returns:
            First matching modifier or None if no matches
        """
        results = self.execute()
        return results[0] if results else None

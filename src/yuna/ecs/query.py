"""Component query system for filtering entities."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from yuna.ecs.archetype_store import ArchetypeStore
from yuna.ecs.component import Component
from yuna.profiling.monitor import get_performance_monitor
from yuna.types.identifiers import EntityID

if TYPE_CHECKING:
    from yuna.ecs.store import ComponentStore


class Query:
    """Filters entities based on component composition.

    Responsibilities:
    - Find entities with specific components (AND logic)
    - Find entities without specific components (NOT logic)
    - Iterate over matching entities with their components
    - Efficient filtering using component store

    Usage:
        query = Query(store=store)
        query = query.with_components(Position, Velocity)
        query = query.without_components(Dead)

        for entity_id, (position, velocity) in query.iterator():
            # Process entities that have Position and Velocity but not Dead
            pass
    """

    def __init__(
        self,
        store: ComponentStore | ArchetypeStore,
        use_archetypes: bool = False,
        profiling_enabled: bool = False,
    ) -> None:
        self._store = store
        self._with_types: list[type] = []
        self._without_types: list[type] = []
        self._only_dirty: bool = False
        self._use_archetypes = use_archetypes
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    def with_components(self, *component_types: type[Component]) -> Query:
        """Filter for entities that have all specified components.

        Args:
            *component_types: Component types that entities must have

        Returns:
            Query instance for chaining
        """
        new_query = Query(
            store=self._store,
            use_archetypes=self._use_archetypes,
            profiling_enabled=self._profiling_enabled,
        )
        new_query._with_types = self._with_types + list(component_types)
        new_query._without_types = self._without_types.copy()
        new_query._only_dirty = self._only_dirty
        return new_query

    def without_components(self, *component_types: type[Component]) -> Query:
        """Filter for entities that don't have any specified components.

        Args:
            *component_types: Component types that entities must not have

        Returns:
            Query instance for chaining
        """
        new_query = Query(
            store=self._store,
            use_archetypes=self._use_archetypes,
            profiling_enabled=self._profiling_enabled,
        )
        new_query._with_types = self._with_types.copy()
        new_query._without_types = self._without_types + list(component_types)
        new_query._only_dirty = self._only_dirty
        return new_query

    def only_dirty(self) -> Query:
        """Filter for entities with at least one dirty component.

        Only returns entities where at least one of the required components
        has been marked as dirty since the last clear.

        Returns:
            Query instance for chaining

        Example:
            query = Query(store).with_components(Position).only_dirty()
            for entity_id, (pos,) in query.iterator():
                # Only processes entities with dirty Position
                pass
        """
        new_query = Query(
            store=self._store,
            use_archetypes=self._use_archetypes,
            profiling_enabled=self._profiling_enabled,
        )
        new_query._with_types = self._with_types.copy()
        new_query._without_types = self._without_types.copy()
        new_query._only_dirty = True
        return new_query

    def iterator(self) -> Iterator[tuple[EntityID, tuple[Component, ...]]]:
        """Iterate over entities matching the query.

        Yields:
            Tuples of (entity_id, (component1, component2, ...))
            Components are returned in the same order as with_components()

        Example:
            query = Query(store).with_components(Position, Velocity)
            for entity_id, (pos, vel) in query.iterator():
                print(f"Entity {entity_id}: pos={pos}, vel={vel}")
        """
        if not self._with_types:
            return

        if self._use_archetypes and not self._only_dirty:
            yield from self._archetype_iterator()
        else:
            candidate_entities = self._get_candidate_entities()
            with_maps: list[dict[EntityID, Component]] = [
                self._store.get_map(component_type=comp_type)
                for comp_type in self._with_types
            ]
            without_maps: list[dict[EntityID, Component]] = [
                self._store.get_map(component_type=comp_type)
                for comp_type in self._without_types
            ]

            for entity_id in sorted(candidate_entities):
                if all(entity_id in type_map for type_map in with_maps) and not any(
                    entity_id in type_map for type_map in without_maps
                ):
                    yield (
                        entity_id,
                        tuple(type_map.get(entity_id) for type_map in with_maps),
                    )

    def get_entities(self) -> set[EntityID]:
        """Get all entity IDs matching the query.

        Returns:
            Set of entity IDs that match the query
        """
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="queries", name="get_entities"):
                return self._execute_get_entities()
        return self._execute_get_entities()

    def _execute_get_entities(self) -> set[EntityID]:
        """Execute get_entities query logic."""
        if not self._with_types:
            return set()

        candidate_entities = self._get_candidate_entities()
        return {
            entity_id
            for entity_id in candidate_entities
            if self._matches_query(entity_id=entity_id)
        }

    def count(self) -> int:
        """Count number of entities matching the query.

        Returns:
            Number of matching entities
        """
        return len(self.get_entities())

    def _get_candidate_entities(self) -> list[EntityID]:
        """Get initial candidate entities.

        If only_dirty is enabled, returns entities with dirty components.
        Otherwise uses the component type with the fewest entities for
        efficiency, snapshotting its IDs in a single C-level call so
        concurrent queries from multiple threads never alias or mutate
        shared state.

        Returns:
            Entity IDs that have at least the smallest required component
        """
        if self._only_dirty:
            dirty_entities: set[EntityID] = set()
            for comp_type in self._with_types:
                dirty_components: dict[EntityID, Any]
                dirty_components = self._store.get_dirty_components(
                    component_type=comp_type
                )
                dirty_entities.update(dirty_components.keys())
            return list(dirty_entities)

        smallest_type: type | None = None
        smallest_count = 0
        for comp_type in self._with_types:
            type_count = self._store.count(component_type=comp_type)
            if smallest_type is None or type_count < smallest_count:
                smallest_type = comp_type
                smallest_count = type_count

        if smallest_type is None:
            return []
        return self._store.get_entity_ids(component_type=smallest_type)

    def _matches_query(self, entity_id: EntityID) -> bool:
        """Check if entity matches all query conditions.

        Args:
            entity_id: Entity to check

        Returns:
            True if entity matches all with/without conditions
        """
        for comp_type in self._with_types:
            if not self._store.has(entity_id=entity_id, component_type=comp_type):
                return False

        for comp_type in self._without_types:
            if self._store.has(entity_id=entity_id, component_type=comp_type):
                return False

        return True

    def _archetype_iterator(
        self,
    ) -> Iterator[tuple[EntityID, tuple[Component, ...]]]:
        """Optimized iterator using archetype-based queries.

        Results are gathered across matching archetypes and yielded sorted by
        entity id so iteration order matches the non-archetype path and stays
        deterministic across runs.

        Yields:
            Tuples of (entity_id, (component1, component2, ...))
        """
        if not isinstance(self._store, ArchetypeStore):
            return

        matching_archetypes = self._store.query_archetypes(
            component_types=set(self._with_types)
        )

        results: list[tuple[EntityID, tuple[Component, ...]]] = []
        for archetype in matching_archetypes:
            if self._without_types:
                has_excluded = any(
                    comp_type in archetype.component_types
                    for comp_type in self._without_types
                )
                if has_excluded:
                    continue

            results.extend(archetype.iter_components(component_types=self._with_types))

        yield from sorted(results, key=lambda item: item[0])

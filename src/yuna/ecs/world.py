"""ECS world coordinator."""

from __future__ import annotations

import asyncio
import random
import threading
from typing import TYPE_CHECKING, Any, TypeVar

from yuna.config.store import ConfigStore
from yuna.ecs.archetype_store import ArchetypeStore
from yuna.ecs.entity import EntityManager
from yuna.ecs.hierarchy import HierarchyManager
from yuna.ecs.priority import (
    EqualPriorityCalculator,
    PriorityCalculator,
)
from yuna.ecs.query import Query
from yuna.ecs.relationships import RelationshipManager
from yuna.ecs.store import ComponentStore
from yuna.exceptions import (
    StateError,
    WorldWriteProtectionError,
)
from yuna.profiling.monitor import get_performance_monitor
from yuna.spatial.grid import SpatialGrid
from yuna.types.identifiers import EntityID

if TYPE_CHECKING:
    from yuna.config.schema import ConfigSchema
    from yuna.ecs.component import Component
    from yuna.ecs.system import System
    from yuna.modifiers.pipeline import ModifierPipeline
    from yuna.state.manager import StateManager
    from yuna.state.snapshot import WorldSnapshot


ComponentT = TypeVar("ComponentT", bound="Component")


class ECSWorld:
    """Central coordinator for Entity Component System.

    Responsibilities:
    - Manage entity lifecycle
    - Store and retrieve components
    - Query entities by component composition
    - Register and execute systems in priority order
    - Coordinate updates and cleanup

    Usage:
        world = ECSWorld()
        entity_id = world.create_entity()
        world.add_component(entity_id=entity_id, component=Position(x=0, y=0))
        world.register_system(system=MovementSystem())
        world.update(delta_time=0.016)
    """

    def __init__(
        self,
        state_manager: StateManager | None = None,
        use_archetypes: bool = False,
        thread_safe: bool = False,
        profiling_enabled: bool = False,
        config_schema: ConfigSchema | None = None,
        modifier_pipeline: ModifierPipeline | None = None,
        seed: int | None = None,
        spatial_grid: SpatialGrid | None = None,
    ) -> None:
        self.seed = seed or 0
        self._entities = EntityManager(seed=self.seed)
        self._components: ComponentStore | ArchetypeStore
        if use_archetypes:
            self._components = ArchetypeStore()
        else:
            self._components = ComponentStore()
        self._systems: list[System] = []
        self._state_manager = state_manager
        self._use_archetypes = use_archetypes
        self._thread_safe = thread_safe
        self._component_lock = asyncio.Lock() if thread_safe else None
        self._relationships = RelationshipManager()
        self._hierarchy = HierarchyManager()
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None
        self._config_schema = config_schema
        self._config_store: ConfigStore | None = None
        if config_schema is not None:
            self._config_store = ConfigStore(schema=config_schema)
        self._modifier_pipeline = modifier_pipeline
        self._current_tick = 0
        self._random = random.Random(self.seed)
        self._spatial_grid = spatial_grid
        self._metadata: dict[str, Any] = {}
        self._write_protection_enabled = False
        self._write_owner = threading.local()

    def enable_write_protection(self, enabled: bool) -> None:
        """Toggle the master switch for write-protected sections.

        When disabled (the default), every write guard is a single bool
        check, so production pays no behavioral cost.

        Args:
            enabled: Whether write-protected sections are enforced
        """
        self._write_protection_enabled = enabled

    def set_write_owner(self, entity_id: EntityID | None) -> None:
        """Set the entity the current thread may write, or None to clear.

        Scoped per thread: a worker thread sets its owner before running
        owner-scoped work and clears it afterward. Threads without an
        owner are unprotected.

        Args:
            entity_id: Entity the current thread is permitted to write
        """
        self._write_owner.entity_id = entity_id

    def _guard_write(self, entity_id: EntityID | None) -> None:
        if not self._write_protection_enabled:
            return
        owner = getattr(self._write_owner, "entity_id", None)
        if owner is None:
            return
        if entity_id is None or entity_id != owner:
            raise WorldWriteProtectionError(
                owner=str(owner),
                target=str(entity_id),
            )

    @property
    def config(self) -> ConfigStore:
        """Access config store.

        Returns:
            ConfigStore instance

        Raises:
            StateError: If world has no config schema
        """
        if self._config_store is None:
            raise StateError(
                operation="config_access",
                reason="World has no config schema",
            )
        return self._config_store

    @property
    def modifiers(self) -> ModifierPipeline:
        """Access modifier pipeline.

        Returns:
            ModifierPipeline instance

        Raises:
            StateError: If world has no modifier pipeline
        """
        if self._modifier_pipeline is None:
            raise StateError(
                operation="modifiers_access",
                reason="World has no modifier pipeline",
            )
        return self._modifier_pipeline

    @property
    def spatial(self) -> SpatialGrid | None:
        """Access spatial grid for spatial queries.

        Returns:
            SpatialGrid instance or None if not configured
        """
        return self._spatial_grid

    @property
    def tick(self) -> int:
        """Get current tick number.

        Returns:
            Current tick counter
        """
        return self._current_tick

    def set_metadata(self, key: str, value: Any) -> None:
        """Store arbitrary metadata in world context.

        Allows games to attach custom data to world for cross-system access.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._guard_write(entity_id=None)
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Retrieve metadata from world context.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self._metadata.get(key, default)

    def increment_tick(self) -> None:
        """Increment tick counter.

        Should be called by game orchestrator at end of each tick.
        """
        self._current_tick += 1

    def create_entity(
        self,
        entity_id: EntityID | None = None,
    ) -> EntityID:
        """Create a new entity.

        Args:
            entity_id: Optional explicit ID (e.g., external bot UUID)

        Returns:
            Unique entity identifier
        """
        self._guard_write(entity_id=None)
        return self._entities.create(entity_id=entity_id)

    def derive_entity_id(self, name: str) -> EntityID:
        """Derive a deterministic, order-independent entity ID.

        For callers that must pre-allocate an ID from concurrent contexts
        before the entity is created in a deterministic phase.

        Args:
            name: Unique derivation name (e.g. owner id plus tick)

        Returns:
            Deterministic entity identifier (not yet registered)
        """
        return self._entities.derive_id(name=name)

    def destroy_entity(self, entity_id: EntityID) -> None:
        """Mark entity for destruction.

        Entity will be removed at end of current update cycle.

        Args:
            entity_id: Entity to destroy
        """
        self._guard_write(entity_id=entity_id)
        self._entities.destroy(entity_id=entity_id)

    def add_component(
        self,
        entity_id: EntityID,
        component: Component,
    ) -> None:
        """Add component to entity.

        Args:
            entity_id: Entity to add component to
            component: Component instance to add
        """
        self._guard_write(entity_id=entity_id)
        self._components.add(entity_id=entity_id, component=component)

    def get_component(
        self,
        entity_id: EntityID,
        component_type: type[Component],
    ) -> Component | None:
        """Get component from entity.

        Args:
            entity_id: Entity to get component from
            component_type: Type of component to retrieve

        Returns:
            Component instance or None if not found
        """
        return self._components.get(
            entity_id=entity_id,
            component_type=component_type,
        )

    def has_component(
        self,
        entity_id: EntityID,
        component_type: type[Component],
    ) -> bool:
        """Check if entity has component.

        Args:
            entity_id: Entity to check
            component_type: Type of component to check for

        Returns:
            True if entity has component
        """
        return self._components.has(
            entity_id=entity_id,
            component_type=component_type,
        )

    def remove_component(
        self,
        entity_id: EntityID,
        component_type: type[Component],
    ) -> None:
        """Remove component from entity.

        Args:
            entity_id: Entity to remove component from
            component_type: Type of component to remove
        """
        self._guard_write(entity_id=entity_id)
        self._components.remove(
            entity_id=entity_id,
            component_type=component_type,
        )

    def query(self) -> Query:
        """Create a new component query.

        Returns:
            Query instance for filtering entities
        """
        return Query(store=self._components, use_archetypes=self._use_archetypes)

    def component_map(
        self,
        component_type: type[ComponentT],
    ) -> dict[EntityID, ComponentT]:
        """Get the live entity-to-component mapping for a type.

        The bulk read for hot per-tick scans that a Query would revisit
        entity by entity. Same contract as ComponentStore.get_map: the
        dict is live internal storage, callers must never mutate it,
        and Python-iterating it is only safe while kernels are not
        running (system phase, command drain).

        Args:
            component_type: Type of components to view

        Returns:
            Live mapping of entity IDs to component instances
        """
        return self._components.get_map(component_type=component_type)

    def register_system(self, system: System) -> None:
        """Register system for execution.

        Systems are executed in priority order (lower = earlier).

        Args:
            system: System to register
        """
        self._systems.append(system)
        self._systems.sort(key=lambda s: s.priority)

    def update(self, delta_time: float) -> None:
        """Update all systems and flush destroyed entities.

        Systems execute in priority order.
        Destroyed entities are removed after all systems update.
        Dirty flags are cleared at the end to reset tracking for next tick.

        Args:
            delta_time: Time elapsed since last update in seconds
        """
        for system in self._systems:
            if self._profiling_enabled and self._monitor:
                system_name = system.__class__.__name__
                with self._monitor.sample(category="systems", name=system_name):
                    system.update(world=self, delta_time=delta_time)
            else:
                system.update(world=self, delta_time=delta_time)

        self.flush_destroyed_entities()

        self._components._dirty_flag.clear_all()

    def flush_destroyed_entities(self) -> set[EntityID]:
        """Remove entities marked by destroy_entity and return their ids.

        destroy_entity only marks. Games that drive their systems through their
        own scheduler never reach update(), so without calling this the mark is
        never acted on: queries, snapshots, spatial sync and any derived cache
        keep serving an entity whose components are still in the store.

        Separate from update() because a game with its own scheduler wants the
        reaping without also running the systems registered on the world.

        Returns:
            Entity ids removed by this call
        """
        destroyed_entities = self._entities.flush_destroyed()

        for entity_id in sorted(destroyed_entities):
            self._components.remove_all(entity_id=entity_id)
            self._relationships.remove_all_relationships(entity_id=entity_id)
            self._hierarchy.remove_entity(entity_id=entity_id)

        return destroyed_entities

    def get_all_entities(self) -> set[EntityID]:
        """Get all active entity IDs.

        Returns:
            Set of all active entity IDs
        """
        return {
            entity_id
            for entity_id in self._entities._entities
            if entity_id not in self._entities._destroyed
        }

    def get_component_types(self) -> set[type]:
        """Get all registered component types.

        Returns:
            Set of component types
        """
        return self._components.get_component_types()

    def get_all_components(self, component_type: type) -> dict[EntityID, Component]:
        """Get all components of a specific type.

        Args:
            component_type: Type of components to get

        Returns:
            Dictionary mapping entity IDs to component instances
        """
        return self._components.get_all(component_type=component_type)

    def iter_components(self, component_type: type) -> list[tuple[EntityID, Component]]:
        """Get all components of a type as entity/component pairs.

        Cheaper than get_all_components() for read-only iteration.

        Args:
            component_type: Type of components to get

        Returns:
            List of (entity ID, component) pairs
        """
        return self._components.iter_items(component_type=component_type)

    def add_existing_entity(self, entity_id: EntityID) -> None:
        """Add an existing entity ID (used for deserialization).

        Args:
            entity_id: Entity ID to add
        """
        self._guard_write(entity_id=entity_id)
        self._entities.add_existing(entity_id=entity_id)

    def clear_all_entities(self) -> None:
        """Clear all entities and components (used for deserialization)."""
        self._guard_write(entity_id=None)
        for entity_id in list(self._entities._entities):
            self.destroy_entity(entity_id=entity_id)
        self._entities.flush_destroyed()

    def create_snapshot(
        self,
        tick: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> WorldSnapshot:
        """Create snapshot of current world state.

        Args:
            tick: Current tick number
            metadata: Additional metadata to include

        Returns:
            Immutable snapshot of world state

        Raises:
            StateError: If no state manager is configured
        """
        if self._state_manager is None:
            raise StateError(
                operation="create_snapshot",
                reason="No state manager configured for world",
            )

        return self._state_manager.create_snapshot(
            world=self,
            tick=tick,
            metadata=metadata,
        )

    def restore_snapshot(self, snapshot: WorldSnapshot) -> None:
        """Restore world state from snapshot.

        Args:
            snapshot: Snapshot to restore from

        Raises:
            StateError: If no state manager is configured
            ValidationError: If snapshot is invalid
        """
        if self._state_manager is None:
            raise StateError(
                operation="restore_snapshot",
                reason="No state manager configured for world",
            )

        self._state_manager.restore_snapshot(snapshot=snapshot, world=self)

    def add_relationship(
        self,
        from_entity: EntityID,
        to_entity: EntityID,
        relationship_type: str,
    ) -> None:
        """Add relationship between entities.

        Args:
            from_entity: Source entity
            to_entity: Target entity
            relationship_type: Type of relationship
        """
        self._guard_write(entity_id=from_entity)
        self._relationships.add_relationship(
            from_entity=from_entity,
            to_entity=to_entity,
            relationship_type=relationship_type,
        )

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
        self._guard_write(entity_id=from_entity)
        self._relationships.remove_relationship(
            from_entity=from_entity,
            to_entity=to_entity,
            relationship_type=relationship_type,
        )

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
        return self._relationships.get_relationships(
            entity_id=entity_id,
            relationship_type=relationship_type,
            direction=direction,
        )

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
        return self._relationships.has_relationship(
            from_entity=from_entity,
            to_entity=to_entity,
            relationship_type=relationship_type,
        )

    def set_parent(self, child_id: EntityID, parent_id: EntityID) -> None:
        """Establish parent-child relationship.

        Args:
            child_id: Child entity
            parent_id: Parent entity

        Raises:
            CircularHierarchyError: If would create cycle
        """
        self._guard_write(entity_id=child_id)
        self._hierarchy.set_parent(child_id=child_id, parent_id=parent_id)

    def remove_parent(self, child_id: EntityID) -> None:
        """Remove parent from child.

        Args:
            child_id: Child entity
        """
        self._guard_write(entity_id=child_id)
        self._hierarchy.remove_parent(child_id=child_id)

    def get_parent(self, entity_id: EntityID) -> EntityID | None:
        """Get parent entity.

        Args:
            entity_id: Entity to query

        Returns:
            Parent entity ID or None
        """
        return self._hierarchy.get_parent(entity_id=entity_id)

    def get_children(self, entity_id: EntityID) -> list[EntityID]:
        """Get all direct children.

        Args:
            entity_id: Entity to query

        Returns:
            List of child entity IDs
        """
        return self._hierarchy.get_children(entity_id=entity_id)

    def get_descendants(self, entity_id: EntityID) -> list[EntityID]:
        """Get all descendants recursively.

        Args:
            entity_id: Entity to query

        Returns:
            List of all descendant entity IDs
        """
        return self._hierarchy.get_descendants(entity_id=entity_id)

    def get_ancestors(self, entity_id: EntityID) -> list[EntityID]:
        """Get all ancestors recursively.

        Args:
            entity_id: Entity to query

        Returns:
            List of all ancestor entity IDs
        """
        return self._hierarchy.get_ancestors(entity_id=entity_id)

    def get_root(self, entity_id: EntityID) -> EntityID:
        """Find root of hierarchy.

        Args:
            entity_id: Entity to query

        Returns:
            Root entity ID
        """
        return self._hierarchy.get_root(entity_id=entity_id)

    def destroy_recursive(self, entity_id: EntityID) -> None:
        """Destroy entity and all descendants.

        Args:
            entity_id: Root entity to destroy
        """
        self._guard_write(entity_id=entity_id)
        entities_to_destroy = self._hierarchy.get_entities_to_destroy(
            entity_id=entity_id
        )
        for entity in entities_to_destroy:
            self.destroy_entity(entity_id=entity)

    async def add_component_async(
        self,
        entity_id: EntityID,
        component: Component,
    ) -> None:
        """Add component to entity (thread-safe async version).

        Args:
            entity_id: Entity to add component to
            component: Component instance to add
        """
        self._guard_write(entity_id=entity_id)
        if self._component_lock is not None:
            async with self._component_lock:
                self._components.add(entity_id=entity_id, component=component)
        else:
            self._components.add(entity_id=entity_id, component=component)

    async def remove_component_async(
        self,
        entity_id: EntityID,
        component_type: type[Component],
    ) -> None:
        """Remove component from entity (thread-safe async version).

        Args:
            entity_id: Entity to remove component from
            component_type: Type of component to remove
        """
        self._guard_write(entity_id=entity_id)
        if self._component_lock is not None:
            async with self._component_lock:
                self._components.remove(
                    entity_id=entity_id,
                    component_type=component_type,
                )
        else:
            self._components.remove(
                entity_id=entity_id,
                component_type=component_type,
            )

    def sort_entities_by_priority(
        self,
        entity_ids: list[EntityID],
        priority_calculator: PriorityCalculator | None = None,
        tick: int = 0,
    ) -> list[EntityID]:
        """Sort entities by priority with deterministic tie-breaking.

        Calculates priority for each entity using provided calculator.
        Entities with equal priority ordered via seeded randomization for
        deterministic outcomes without registration order bias.

        Args:
            entity_ids: List of entities to sort
            priority_calculator: Calculator to use (EqualPriorityCalculator if None)
            tick: Current tick (used for tie-breaking seed)

        Returns:
            Entities sorted by priority (highest first)

        Design:
            No default calculator stored in world - each call provides its own.
            This allows different systems to use different priority logic.
        """
        if not entity_ids:
            return []

        calculator = priority_calculator or EqualPriorityCalculator()

        priorities = [
            (calculator.calculate_priority(entity_id=eid, world=self), eid)
            for eid in sorted(entity_ids)
        ]

        seeded_random = random.Random(self.seed + tick)
        seeded_random.shuffle(priorities)

        priorities.sort(key=lambda x: x[0], reverse=True)

        return [eid for _, eid in priorities]

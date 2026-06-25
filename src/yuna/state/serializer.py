"""Snapshot serialization and deserialization."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Any,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from yuna.exceptions import SerializationError, ValidationError
from yuna.network.compression import (
    CompressionStrategy,
    NoCompression,
)
from yuna.network.delta import Delta, DeltaSerializer
from yuna.profiling.monitor import get_performance_monitor
from yuna.state.raw_snapshot import RawSnapshot
from yuna.state.snapshot import WorldSnapshot
from yuna.types.identifiers import EntityID

if TYPE_CHECKING:
    from yuna.ecs.world import ECSWorld

_PRIMITIVE_TYPES = frozenset({str, int, float, bool, type(None)})
_IMMUTABLE_CONTAINER_ORIGINS = frozenset({frozenset, tuple})

SERIALIZATION_VERSION_FIELD = "serialization_version"


def bump_serialization_version(component: Any) -> None:
    """Mark a version-counted component as mutated in place.

    Every code path that mutates an opted-in component without replacing
    the instance must call this so the serializer's reuse cache expires.

    Args:
        component: Component declaring a serialization_version field
    """
    component.serialization_version += 1


@dataclass(frozen=True)
class _ComponentSerializationPlan:
    """Precomputed per-type strategy for serializing component instances.

    Components may declare an integer ``serialization_version`` field as a
    mutation counter: every in-place mutation path must bump it, letting the
    serializer reuse the previous serialized dict while the instance and
    version are unchanged. The field itself is never serialized.
    """

    uses_to_dict: bool
    field_names: tuple[str, ...]
    cacheable: bool
    versioned: bool


_component_plans: dict[type, _ComponentSerializationPlan] = {}
_deeply_immutable_types: dict[type, bool] = {}


def _is_immutable_annotation(annotation: Any) -> bool:
    if annotation in _PRIMITIVE_TYPES:
        return True

    origin = get_origin(annotation)
    if origin in _IMMUTABLE_CONTAINER_ORIGINS:
        return all(
            _is_immutable_annotation(annotation=argument)
            for argument in get_args(annotation)
            if argument is not Ellipsis
        )
    if origin is Union or origin is UnionType:
        return all(
            _is_immutable_annotation(annotation=argument)
            for argument in get_args(annotation)
        )

    if isinstance(annotation, type):
        if issubclass(annotation, Enum):
            return True
        if is_dataclass(obj=annotation):
            return _is_deeply_immutable_dataclass(dataclass_type=annotation)

    return False


def _is_deeply_immutable_dataclass(dataclass_type: type) -> bool:
    """Check whether a dataclass type can never observably mutate.

    Requires the dataclass to be frozen with every field annotation
    resolving to a recursively immutable type. Self-referential cycles
    resolve conservatively to False via the provisional cache entry.
    """
    cached = _deeply_immutable_types.get(dataclass_type)
    if cached is not None:
        return cached

    _deeply_immutable_types[dataclass_type] = False

    if not dataclass_type.__dataclass_params__.frozen:  # type: ignore[attr-defined]
        return False

    try:
        hints = get_type_hints(obj=dataclass_type)
    except NameError, TypeError:
        return False

    immutable = all(
        _is_immutable_annotation(annotation=hints.get(dataclass_field.name))
        for dataclass_field in fields(dataclass_type)
    )
    _deeply_immutable_types[dataclass_type] = immutable
    return immutable


def _get_component_plan(component_type: type) -> _ComponentSerializationPlan:
    plan = _component_plans.get(component_type)
    if plan is None:
        if not is_dataclass(obj=component_type):
            raise SerializationError(
                operation="serialize",
                component_type=component_type.__name__,
                reason="Component must be a dataclass instance",
            )
        uses_to_dict = callable(getattr(component_type, "to_dict", None))
        all_field_names = tuple(
            dataclass_field.name for dataclass_field in fields(component_type)
        )
        versioned = not uses_to_dict and SERIALIZATION_VERSION_FIELD in all_field_names
        plan = _ComponentSerializationPlan(
            uses_to_dict=uses_to_dict,
            field_names=tuple(
                name for name in all_field_names if name != SERIALIZATION_VERSION_FIELD
            ),
            cacheable=(
                not uses_to_dict
                and _is_deeply_immutable_dataclass(dataclass_type=component_type)
            ),
            versioned=versioned,
        )
        _component_plans[component_type] = plan
    return plan


class SnapshotSerializer:
    """Serializes and deserializes world snapshots.

    Responsibilities:
    - Capture complete world state as snapshot
    - Restore world state from snapshot
    - Convert snapshots to/from JSON
    - Manage component type registry for dynamic serialization

    Note: This class uses dynamic typing for component registration.
    Component types are not known at compile time, so we use Any
    with runtime validation via is_dataclass().

    Usage:
        serializer = SnapshotSerializer()
        serializer.register_component_type(component_type=Position)
        snapshot = serializer.serialize(world=world)
        serializer.deserialize(snapshot=snapshot, world=world)
        json_str = serializer.to_json(snapshot=snapshot)
        snapshot = serializer.from_json(json_str=json_str)
    """

    def __init__(
        self,
        compression_strategy: CompressionStrategy | None = None,
    ) -> None:
        self._component_types: dict[str, Any] = {}
        self._compression_strategy = compression_strategy or NoCompression()
        self._delta_serializer = DeltaSerializer()
        self._reuse_cache: dict[tuple[EntityID, str], tuple[Any, dict[str, Any]]] = {}
        self._versioned_cache: dict[
            tuple[EntityID, str], tuple[Any, int, dict[str, Any]]
        ] = {}

    def register_component_type(self, component_type: Any) -> None:
        """Register a component type for serialization.

        Args:
            component_type: Component class to register (must be a dataclass)
        """
        if not is_dataclass(obj=component_type):
            raise SerializationError(
                operation="register",
                component_type=component_type.__name__,
                reason="Component type must be a dataclass",
            )
        self._component_types[component_type.__name__] = component_type  # type: ignore[union-attr]

    def serialize(
        self,
        world: ECSWorld,
        tick: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> WorldSnapshot:
        """Capture world state as snapshot.

        Delegates to capture() so full snapshots share the same component
        serialization paths and reuse caches as incremental recording.
        Component dicts inside the returned snapshot may be shared with
        the serializer's reuse caches and with other snapshots from the
        same serializer; callers must treat them as immutable and replace
        dicts wholesale rather than mutating them in place.

        Args:
            world: World to serialize
            tick: Current tick number
            metadata: Additional metadata to include

        Returns:
            Immutable snapshot of world state
        """
        return self.finalize(
            raw_snapshot=self.capture(world=world, tick=tick, metadata=metadata)
        )

    def capture(
        self,
        world: ECSWorld,
        tick: int = 0,
        metadata: dict[str, Any] | None = None,
        excluded_components: set[str] | None = None,
    ) -> RawSnapshot:
        """Capture world state as snapshot with serialized components.

        Args:
            world: World to capture
            tick: Current tick number
            metadata: Additional metadata to include
            excluded_components: Component type names to skip during capture

        Returns:
            Raw snapshot with serialized component data
        """
        monitor = get_performance_monitor()
        excluded = excluded_components or set()

        with monitor.sample(category="serialization", name="capture_snapshot"):
            entities_data: dict[EntityID, dict[str, Any]] = {}

            component_types = world.get_component_types()
            for component_type in component_types:
                component_name = component_type.__name__

                if component_name in excluded:
                    continue

                plan = _get_component_plan(component_type=component_type)
                for entity_id, component in world.iter_components(
                    component_type=component_type
                ):
                    if entity_id not in entities_data:
                        entities_data[entity_id] = {}
                    if plan.cacheable:
                        entities_data[entity_id][component_name] = (
                            self._serialize_cached(
                                entity_id=entity_id,
                                component_name=component_name,
                                component=component,
                            )
                        )
                    elif plan.versioned:
                        entities_data[entity_id][component_name] = (
                            self._serialize_versioned(
                                entity_id=entity_id,
                                component_name=component_name,
                                component=component,
                            )
                        )
                    else:
                        entities_data[entity_id][component_name] = (
                            self._serialize_component(component=component)
                        )

            return RawSnapshot(
                tick=tick,
                timestamp=time.time(),
                entities=entities_data,
                metadata=metadata or {},
            )

    def capture_components(
        self,
        world: ECSWorld,
        included_components: set[str],
    ) -> dict[EntityID, dict[str, Any]]:
        """Capture only the named components as serialized entity data.

        Lets a caller record components that are produced after the primary
        snapshot but belong to the same frame, without re-capturing the
        whole world.

        Args:
            world: World to capture from
            included_components: Component type names to capture

        Returns:
            Mapping of entity id to serialized data for the named components
        """
        entities_data: dict[EntityID, dict[str, Any]] = {}

        if not included_components:
            return entities_data

        component_types = world.get_component_types()
        for component_type in component_types:
            component_name = component_type.__name__

            if component_name not in included_components:
                continue

            for entity_id, component in world.iter_components(
                component_type=component_type
            ):
                if entity_id not in entities_data:
                    entities_data[entity_id] = {}
                entities_data[entity_id][component_name] = self._serialize_component(
                    component=component
                )

        return entities_data

    def _serialize_cached(
        self,
        entity_id: EntityID,
        component_name: str,
        component: Any,
    ) -> dict[str, Any]:
        """Serialize a deeply-immutable component with identity-based reuse.

        Holding the component reference in the cache guarantees the identity
        check can never collide with a recycled object id.

        Args:
            entity_id: Entity owning the component
            component_name: Component type name
            component: Component instance to serialize

        Returns:
            Serialized component dictionary (shared across unchanged ticks)
        """
        cache_key = (entity_id, component_name)
        cached = self._reuse_cache.get(cache_key)
        if cached is not None and cached[0] is component:
            return cached[1]

        serialized = self._serialize_component(component=component)
        self._reuse_cache[cache_key] = (component, serialized)
        return serialized

    def _serialize_versioned(
        self,
        entity_id: EntityID,
        component_name: str,
        component: Any,
    ) -> dict[str, Any]:
        """Serialize a version-counted component with mutation-aware reuse.

        Reuses the previous serialized dict while both the instance identity
        and its serialization_version are unchanged. Every in-place mutation
        path of an opted-in component must bump the version field.

        Args:
            entity_id: Entity owning the component
            component_name: Component type name
            component: Component instance to serialize

        Returns:
            Serialized component dictionary (shared across unchanged ticks)
        """
        cache_key = (entity_id, component_name)
        version = component.serialization_version
        cached = self._versioned_cache.get(cache_key)
        if cached is not None and cached[0] is component and cached[1] == version:
            return cached[2]

        serialized = self._serialize_component(component=component)
        self._versioned_cache[cache_key] = (component, version, serialized)
        return serialized

    @staticmethod
    def finalize(raw_snapshot: RawSnapshot) -> WorldSnapshot:
        """Convert raw snapshot to world snapshot.

        Args:
            raw_snapshot: Raw snapshot with serialized component data

        Returns:
            World snapshot ready for storage
        """
        return WorldSnapshot(
            tick=raw_snapshot.tick,
            timestamp=raw_snapshot.timestamp,
            entities=raw_snapshot.entities,
            metadata=raw_snapshot.metadata,
        )

    def deserialize(self, snapshot: WorldSnapshot, world: ECSWorld) -> None:
        """Restore world state from snapshot.

        Args:
            snapshot: Snapshot to restore from
            world: World to restore into (will be cleared first)
        """
        world.clear_all_entities()

        for entity_id, components_data in snapshot.entities.items():
            world.add_existing_entity(entity_id=entity_id)

            for component_name, component_data in components_data.items():
                if component_name not in self._component_types:
                    raise ValidationError(
                        field="component_type",
                        value=component_name,
                        reason="Unknown component type not registered",
                    )

                component_type = self._component_types[component_name]
                component = self._deserialize_component(
                    component_type=component_type,
                    component_data=component_data,
                )
                world.add_component(entity_id=entity_id, component=component)

    @staticmethod
    def to_json(snapshot: WorldSnapshot) -> str:
        """Convert snapshot to JSON string.

        Args:
            snapshot: Snapshot to serialize

        Returns:
            JSON string representation
        """
        data = {
            "tick": snapshot.tick,
            "timestamp": snapshot.timestamp,
            "entities": dict(snapshot.entities),
            "metadata": snapshot.metadata,
        }
        return json.dumps(obj=data, indent=2)

    @staticmethod
    def from_json(json_str: str) -> WorldSnapshot:
        """Convert JSON string to snapshot.

        Args:
            json_str: JSON string to deserialize

        Returns:
            WorldSnapshot instance
        """
        data = json.loads(s=json_str)
        entities = {
            EntityID(entity_id): components
            for entity_id, components in data["entities"].items()
        }
        return WorldSnapshot(
            tick=data["tick"],
            timestamp=data["timestamp"],
            entities=entities,
            metadata=data["metadata"],
        )

    @staticmethod
    def _serialize_component(component: Any) -> dict[str, Any]:
        """Serialize component to dictionary.

        Args:
            component: Component to serialize (must be dataclass instance)

        Returns:
            Dictionary representation of component

        Raises:
            SerializationError: If component is not a dataclass instance
        """
        plan = _get_component_plan(component_type=type(component))

        if plan.uses_to_dict:
            return cast(dict[str, Any], component.to_dict())

        return {
            name: (
                value
                if type(value := getattr(component, name)) in _PRIMITIVE_TYPES
                else SnapshotSerializer._normalize_for_serialization(data=value)
            )
            for name in plan.field_names
        }

    @staticmethod
    def _normalize_for_serialization(data: Any) -> Any:
        """Recursively normalize data for JSON serialization.

        Handles conversion of non-JSON-serializable types to serializable forms.
        Uses duck typing to detect custom serialization methods.

        Supported conversions:
        - Enum → value (str/int/etc.)
        - frozenset/set → list
        - Objects with to_dict() → dict (e.g., StateMachine, custom types)
        - Dataclasses → dict (e.g., Vector2, nested components)

        Args:
            data: Data to normalize (dict, list, or primitive)

        Returns:
            Data with all types normalized for JSON serialization
        """
        data_type = type(data)
        if data_type in _PRIMITIVE_TYPES:
            return data

        if data_type is dict:
            return {
                key: (
                    value
                    if type(value) in _PRIMITIVE_TYPES
                    else SnapshotSerializer._normalize_for_serialization(data=value)
                )
                for key, value in data.items()
            }

        if data_type is list:
            return [
                (
                    item
                    if type(item) in _PRIMITIVE_TYPES
                    else SnapshotSerializer._normalize_for_serialization(data=item)
                )
                for item in data
            ]

        if isinstance(data, Enum):
            return data.value

        if isinstance(data, (frozenset, set)):
            return [
                SnapshotSerializer._normalize_for_serialization(data=item)
                for item in data
            ]

        if hasattr(data, "to_dict") and callable(data.to_dict):
            return SnapshotSerializer._normalize_for_serialization(data=data.to_dict())

        if is_dataclass(obj=data) and not isinstance(data, type):
            if hasattr(data, "__dict__"):
                return SnapshotSerializer._normalize_for_serialization(
                    data=data.__dict__
                )
            return SnapshotSerializer._normalize_for_serialization(
                data={f.name: getattr(data, f.name) for f in fields(data)}
            )

        if isinstance(data, dict):
            return {
                key: SnapshotSerializer._normalize_for_serialization(data=value)
                for key, value in data.items()
            }

        if isinstance(data, list):
            return [
                SnapshotSerializer._normalize_for_serialization(data=item)
                for item in data
            ]

        return data

    @staticmethod
    def _deserialize_component(
        component_type: Any,
        component_data: dict[str, Any],
    ) -> Any:
        """Deserialize component from dictionary.

        Args:
            component_type: Type of component to create (must be dataclass type)
            component_data: Dictionary data to deserialize

        Returns:
            Component instance

        Raises:
            SerializationError: If component_type is not a dataclass type
        """
        if not is_dataclass(obj=component_type):
            raise SerializationError(
                operation="deserialize",
                component_type=component_type.__name__,
                reason="Component type must be a dataclass",
            )

        field_types = {f.name: f.type for f in fields(component_type)}
        filtered_data = {
            key: value for key, value in component_data.items() if key in field_types
        }

        normalized_data = SnapshotSerializer._normalize_for_deserialization(
            data=filtered_data,
            field_types=field_types,
        )

        return component_type(**normalized_data)  # type: ignore[operator]

    @staticmethod
    def _normalize_for_deserialization(
        data: dict[str, Any],
        field_types: dict[str, Any],
    ) -> dict[str, Any]:
        """Normalize data for component deserialization.

        Handles reconstruction of complex types from serialized forms.
        Add new type handlers here as needed.

        Supported conversions:
        - str/int → Enum (if field type is Enum subclass)

        Args:
            data: Deserialized data dictionary
            field_types: Mapping of field names to their types

        Returns:
            Data with types reconstructed for component instantiation
        """
        normalized = {}
        for key, value in data.items():
            field_type = field_types.get(key)

            if (
                field_type
                and isinstance(field_type, type)
                and issubclass(field_type, Enum)
            ):
                normalized[key] = field_type(value)
            else:
                normalized[key] = value

        return normalized

    def serialize_delta(
        self,
        old_snapshot: WorldSnapshot,
        new_snapshot: WorldSnapshot,
    ) -> bytes:
        """Serialize delta between snapshots with compression.

        Args:
            old_snapshot: Previous snapshot
            new_snapshot: Current snapshot

        Returns:
            Compressed delta bytes
        """
        delta = self._delta_serializer.compute_delta(
            old_snapshot=old_snapshot,
            new_snapshot=new_snapshot,
        )
        delta_dict = {
            "tick": delta.tick,
            "added_entities": {
                str(entity_id): components
                for entity_id, components in delta.added_entities.items()
            },
            "removed_entities": [
                str(entity_id) for entity_id in delta.removed_entities
            ],
            "modified_components": {
                str(entity_id): components
                for entity_id, components in delta.modified_components.items()
            },
        }
        delta_json = json.dumps(obj=delta_dict)
        delta_bytes = delta_json.encode(encoding="utf-8")
        return self._compression_strategy.compress(data=delta_bytes)

    def deserialize_delta(
        self,
        base_snapshot: WorldSnapshot,
        delta_bytes: bytes,
    ) -> WorldSnapshot:
        """Deserialize and apply compressed delta to base snapshot.

        Args:
            base_snapshot: Base snapshot to apply delta to
            delta_bytes: Compressed delta bytes

        Returns:
            New snapshot with delta applied
        """
        decompressed = self._compression_strategy.decompress(data=delta_bytes)
        delta_json = decompressed.decode(encoding="utf-8")
        delta_dict = json.loads(s=delta_json)

        delta = Delta(
            tick=delta_dict["tick"],
            added_entities={
                EntityID(entity_id): components
                for entity_id, components in delta_dict["added_entities"].items()
            },
            removed_entities={
                EntityID(entity_id) for entity_id in delta_dict["removed_entities"]
            },
            modified_components={
                EntityID(entity_id): components
                for entity_id, components in delta_dict["modified_components"].items()
            },
        )

        return self._delta_serializer.apply_delta(
            base_snapshot=base_snapshot,
            delta=delta,
        )

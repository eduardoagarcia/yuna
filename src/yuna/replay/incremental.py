"""Incremental recording with keyframes and deltas for efficient replay storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from yuna.exceptions import StateError
from yuna.profiling.monitor import get_performance_monitor
from yuna.state.raw_snapshot import RawSnapshot
from yuna.state.snapshot import WorldSnapshot
from yuna.types.identifiers import EntityID

if TYPE_CHECKING:
    from yuna.replay.config import RecordingConfig


@dataclass
class EntityChanges:
    """Entity-level changes between snapshots."""

    added: dict[EntityID, dict[str, Any]] = field(default_factory=dict)
    removed: set[EntityID] = field(default_factory=set)


@dataclass
class ComponentChanges:
    """Component-level changes for existing entities."""

    added: dict[EntityID, dict[str, Any]] = field(default_factory=dict)
    modified: dict[EntityID, dict[str, Any]] = field(default_factory=dict)
    removed: dict[EntityID, set[str]] = field(default_factory=dict)


@dataclass
class SnapshotDelta:
    """Represents changes between two snapshots.

    Responsibilities:
    - Track entity-level changes (added/removed entities)
    - Track component-level changes (added/modified/removed components)
    - Support efficient delta application

    Usage:
        delta = SnapshotDelta(
            tick=101,
            entities=EntityChanges(
                added={entity_id: components},
                removed={entity_id},
            ),
            components=ComponentChanges(
                added={entity_id: {"NewComponent": {...}}},
                modified={entity_id: {"Position": {"x": 10, "y": 20}}},
                removed={entity_id: {"OccupiedComponent"}},
            ),
        )
    """

    tick: int
    entities: EntityChanges = field(default_factory=EntityChanges)
    components: ComponentChanges = field(default_factory=ComponentChanges)


def compute_delta(
    previous: WorldSnapshot,
    current: WorldSnapshot,
) -> SnapshotDelta:
    """Compute delta between two snapshots.

    Args:
        previous: Previous snapshot
        current: Current snapshot

    Returns:
        Delta representing changes from previous to current
    """
    previous_entities = set(previous.entities.keys())
    current_entities = set(current.entities.keys())

    entity_changes = EntityChanges(
        added={
            entity_id: current.entities[entity_id]
            for entity_id in (current_entities - previous_entities)
        },
        removed=previous_entities - current_entities,
    )

    component_changes = ComponentChanges()

    for entity_id in previous_entities & current_entities:
        prev_components = previous.entities[entity_id]
        curr_components = current.entities[entity_id]

        if prev_components != curr_components:
            component_changes.modified[entity_id] = curr_components

    return SnapshotDelta(
        tick=current.tick, entities=entity_changes, components=component_changes
    )


def compute_component_level_delta(
    previous: WorldSnapshot,
    current: WorldSnapshot,
) -> SnapshotDelta:
    """Compute delta with component-level granularity.

    Only stores components that actually changed, not entire entity state.
    This significantly reduces delta size when only a few components change.

    Args:
        previous: Previous snapshot
        current: Current snapshot

    Returns:
        Delta with component-level changes (added/modified/removed)
    """
    previous_entities = set(previous.entities.keys())
    current_entities = set(current.entities.keys())

    entity_changes = EntityChanges(
        added={
            entity_id: current.entities[entity_id]
            for entity_id in (current_entities - previous_entities)
        },
        removed=previous_entities - current_entities,
    )

    component_changes = ComponentChanges()

    for entity_id in previous_entities & current_entities:
        prev_components = previous.entities[entity_id]
        curr_components = current.entities[entity_id]

        all_component_names = set(prev_components.keys()) | set(curr_components.keys())

        added_components: dict[str, Any] = {}
        modified_components: dict[str, Any] = {}
        removed_component_names: set[str] = set()

        for comp_name in all_component_names:
            prev_comp = prev_components.get(comp_name)
            curr_comp = curr_components.get(comp_name)

            if prev_comp is curr_comp:
                continue

            if prev_comp is None and curr_comp is not None:
                added_components[comp_name] = curr_comp
            elif prev_comp is not None and curr_comp is None:
                if prev_comp != {}:
                    removed_component_names.add(comp_name)
            elif prev_comp != curr_comp:
                modified_components[comp_name] = curr_comp

        if added_components:
            component_changes.added[entity_id] = added_components

        if modified_components:
            component_changes.modified[entity_id] = modified_components

        if removed_component_names:
            component_changes.removed[entity_id] = removed_component_names

    return SnapshotDelta(
        tick=current.tick, entities=entity_changes, components=component_changes
    )


def apply_delta(
    snapshot: WorldSnapshot,
    delta: SnapshotDelta,
) -> WorldSnapshot:
    """Apply delta to snapshot to produce new snapshot.

    Args:
        snapshot: Base snapshot
        delta: Delta to apply

    Returns:
        New snapshot with delta applied
    """
    entities = dict(snapshot.entities)

    for entity_id in delta.entities.removed:
        entities.pop(entity_id, None)

    for entity_id, components in delta.entities.added.items():
        entities[entity_id] = components

    for entity_id, added_components in delta.components.added.items():
        if entity_id in entities:
            entities[entity_id] = {**entities[entity_id], **added_components}
        else:
            entities[entity_id] = added_components

    for entity_id, modified_components in delta.components.modified.items():
        if entity_id in entities:
            entities[entity_id] = {**entities[entity_id], **modified_components}
        else:
            entities[entity_id] = modified_components

    for entity_id, removed_component_names in delta.components.removed.items():
        if entity_id in entities:
            entities[entity_id] = {
                comp_name: comp_data
                for comp_name, comp_data in entities[entity_id].items()
                if comp_name not in removed_component_names
            }

    return WorldSnapshot(
        tick=delta.tick,
        timestamp=snapshot.timestamp,
        entities=entities,
        metadata=snapshot.metadata,
    )


@dataclass
class IncrementalRecording:
    """Container for incremental recording data.

    Responsibilities:
    - Store keyframe snapshots at regular intervals
    - Store deltas between keyframes
    - Support reconstruction of any tick
    - Track keyframe interval for optimal storage

    Usage:
        recording = IncrementalRecording(
            metadata={"seed": 42},
            keyframe_interval=60,
            keyframes={0: snapshot0, 60: snapshot60},
            deltas={1: delta1, 2: delta2, ...},
        )
    """

    metadata: dict[str, Any]
    keyframe_interval: int
    keyframes: dict[int, WorldSnapshot] = field(default_factory=dict)
    deltas: dict[int, SnapshotDelta] = field(default_factory=dict)

    def get_snapshot(self, tick: int) -> WorldSnapshot | None:
        """Reconstruct snapshot for specific tick.

        Args:
            tick: Tick number to reconstruct

        Returns:
            Reconstructed snapshot, or None if tick not recorded
        """
        if tick in self.keyframes:
            return self.keyframes[tick]

        keyframe_tick = (tick // self.keyframe_interval) * self.keyframe_interval
        if keyframe_tick not in self.keyframes:
            return None

        snapshot = self.keyframes[keyframe_tick]

        for delta_tick in range(keyframe_tick + 1, tick + 1):
            if delta_tick not in self.deltas:
                return None
            snapshot = apply_delta(snapshot=snapshot, delta=self.deltas[delta_tick])

        return snapshot

    def get_keyframe_ticks(self) -> list[int]:
        """Get list of keyframe tick numbers.

        Returns:
            Sorted list of keyframe ticks
        """
        return sorted(self.keyframes.keys())

    def get_delta_ticks(self) -> list[int]:
        """Get list of delta tick numbers.

        Returns:
            Sorted list of delta ticks
        """
        return sorted(self.deltas.keys())


class IncrementalRecorder:
    """Records game sessions using keyframes + deltas for storage efficiency.

    Responsibilities:
    - Store full snapshots at keyframe intervals
    - Store only deltas between keyframes
    - Reduce replay file size by 90% compared to full recording
    - Support configurable keyframe interval
    - Support delta-only mode (no keyframes after initial)

    Storage patterns:
    - Standard mode:
        - Tick 0: Full keyframe
        - Ticks 1-59: Deltas
        - Tick 60: Full keyframe
        - Ticks 61-119: Deltas
    - Delta-only mode:
        - Tick 0: Full keyframe
        - All subsequent ticks: Deltas only (no repeated keyframes)

    Usage:
        recorder = IncrementalRecorder(keyframe_interval=60)
        recorder.start_recording(world=world, metadata={"seed": 42})
        for tick in range(1000):
            recorder.record_tick(world=world, tick=tick)
        recording = recorder.stop_recording()
    """

    def __init__(
        self,
        keyframe_interval: int = 60,
        delta_only: bool = False,
        component_level_deltas: bool = True,
        config: RecordingConfig | None = None,
    ) -> None:
        """Initialize incremental recorder.

        Args:
            keyframe_interval: Ticks between keyframes (default 60)
            delta_only: If True, never create keyframes after tick 0
            component_level_deltas: If True, compute deltas at component
            level for smaller size config: Optional recording configuration
            for filtering components
        """
        self._keyframe_interval = keyframe_interval
        self._delta_only = delta_only
        self._component_level_deltas = component_level_deltas
        self._config = config
        self._recording = False
        self._keyframes: dict[int, WorldSnapshot] = {}
        self._deltas: dict[int, SnapshotDelta] = {}
        self._metadata: dict[str, Any] = {}
        self._last_snapshot: WorldSnapshot | None = None
        self._pending_frame: RawSnapshot | None = None

    def start_recording(
        self,
        world: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Begin recording a game session.

        Args:
            world: World to record (ECSWorld)
            metadata: Game metadata (seed, players, etc.)

        Raises:
            StateError: If already recording
        """
        if self._recording:
            raise StateError(
                operation="start_recording",
                state="recording",
                reason="Recording already in progress",
            )

        self._recording = True
        self._keyframes = {}
        self._deltas = {}
        self._metadata = metadata or {}
        self._last_snapshot = None
        self._pending_frame = None

        excluded_components = self._config.excluded_components if self._config else None

        self._pending_frame = world._state_manager.capture_snapshot(
            world=world,
            tick=0,
            metadata=self._metadata,
            excluded_components=excluded_components,
        )

    def record_tick(self, world: Any, tick: int) -> None:
        """Record a single tick.

        Finalizes the previous frame into a keyframe or delta before
        capturing the new one, so memory stays bounded to two frames
        plus the accumulated deltas.

        Args:
            world: World to record (ECSWorld)
            tick: Current tick number

        Raises:
            StateError: If not recording
        """
        if not self._recording:
            raise StateError(
                operation="record_tick",
                state="not_recording",
                reason="Not currently recording",
            )

        self._finalize_pending_frame(world=world)

        excluded_components = self._config.excluded_components if self._config else None

        self._pending_frame = world._state_manager.capture_snapshot(
            world=world,
            tick=tick,
            metadata=self._metadata,
            excluded_components=excluded_components,
        )

    def update_frame_components(
        self,
        world: Any,
        component_names: set[str],
    ) -> None:
        """Merge the named components into the most recent frame.

        Records components produced after this frame's primary snapshot into
        that same frame (e.g. values computed mid-tick that belong to the
        tick already snapshotted), without re-capturing the whole world.

        Args:
            world: World to capture from (ECSWorld)
            component_names: Component type names to merge

        Raises:
            StateError: If not recording
        """
        if not self._recording:
            raise StateError(
                operation="update_frame_components",
                state="not_recording",
                reason="Not currently recording",
            )

        if not component_names:
            return

        frame = self._pending_frame
        if frame is None:
            return

        components = world._state_manager.capture_components(
            world=world,
            included_components=component_names,
        )

        for entity_id, entity_components in components.items():
            frame.entities.setdefault(entity_id, {}).update(entity_components)

    def stop_recording(self, world: Any) -> IncrementalRecording:
        """Stop recording and return the recording.

        Deltas are computed incrementally during record_tick, so stopping
        only finalizes the last pending frame.

        Args:
            world: World to get state manager from

        Returns:
            Complete incremental recording

        Raises:
            StateError: If not recording
        """
        monitor = get_performance_monitor()

        with monitor.sample(category="recording", name="stop_recording"):
            if not self._recording:
                raise StateError(
                    operation="stop_recording",
                    state="not_recording",
                    reason="Not currently recording",
                )

            self._recording = False

            self._finalize_pending_frame(world=world)

            return IncrementalRecording(
                metadata=self._metadata,
                keyframe_interval=self._keyframe_interval,
                keyframes=self._keyframes,
                deltas=self._deltas,
            )

    def _finalize_pending_frame(self, world: Any) -> None:
        """Fold the pending frame into keyframes or deltas.

        Deferred until the next record_tick (or stop_recording) so frame
        component merges can still land in the pending frame.

        Args:
            world: World to get state manager from
        """
        raw_snapshot = self._pending_frame
        if raw_snapshot is None:
            return

        self._pending_frame = None
        tick = raw_snapshot.tick

        should_keyframe = (
            tick % self._keyframe_interval == 0 and not self._delta_only
        ) or tick == 0

        if should_keyframe:
            snapshot = world._state_manager.finalize_snapshot(raw_snapshot=raw_snapshot)
            self._keyframes[tick] = snapshot
            self._last_snapshot = snapshot
        elif self._last_snapshot is not None:
            filtered_snapshot = self._filter_snapshot(raw_snapshot=raw_snapshot)
            snapshot = world._state_manager.finalize_snapshot(
                raw_snapshot=filtered_snapshot
            )
            monitor = get_performance_monitor()
            with monitor.sample(category="recording", name="compute_delta"):
                if self._component_level_deltas:
                    delta = compute_component_level_delta(
                        previous=self._last_snapshot,
                        current=snapshot,
                    )
                else:
                    delta = compute_delta(
                        previous=self._last_snapshot,
                        current=snapshot,
                    )
            self._deltas[tick] = delta
            self._last_snapshot = snapshot

    def is_recording(self) -> bool:
        """Check if currently recording.

        Returns:
            True if recording is in progress
        """
        return self._recording

    def _filter_snapshot(self, raw_snapshot: RawSnapshot) -> RawSnapshot:
        """Filter components from snapshot based on config.

        Args:
            raw_snapshot: Raw snapshot to filter

        Returns:
            Filtered raw snapshot
        """
        if self._config is None:
            return raw_snapshot

        filtered_entities: dict[EntityID, dict[str, Any]] = {}

        for entity_id, components in raw_snapshot.entities.items():
            filtered_components: dict[str, Any] = {}

            for comp_name, comp_data in components.items():
                if not self._config.should_include_component(component_name=comp_name):
                    continue

                if self._config.skip_empty_marker_components and comp_data == {}:
                    continue

                filtered_components[comp_name] = comp_data

            if filtered_components:
                filtered_entities[entity_id] = filtered_components

        return RawSnapshot(
            tick=raw_snapshot.tick,
            timestamp=raw_snapshot.timestamp,
            entities=filtered_entities,
            metadata=raw_snapshot.metadata,
        )

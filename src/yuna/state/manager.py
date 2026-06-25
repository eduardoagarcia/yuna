"""State management for world snapshots."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yuna.exceptions import ValidationError
from yuna.state.raw_snapshot import RawSnapshot
from yuna.state.serializer import SnapshotSerializer
from yuna.state.snapshot import WorldSnapshot
from yuna.types.identifiers import EntityID

if TYPE_CHECKING:
    from yuna.ecs.world import ECSWorld


class StateManager:
    """Manages world state snapshots and restoration.

    Responsibilities:
    - Create snapshots from world state
    - Restore world state from snapshots
    - Validate snapshot integrity
    - Coordinate with SnapshotSerializer

    Usage:
        manager = StateManager(serializer=serializer)
        snapshot = manager.create_snapshot(world=world, tick=100)
        manager.restore_snapshot(snapshot=snapshot, world=world)
        is_valid = manager.validate_snapshot(snapshot=snapshot)
    """

    def __init__(self, serializer: SnapshotSerializer) -> None:
        """Initialize StateManager.

        Args:
            serializer: Serializer to use for snapshot operations
        """
        self._serializer = serializer

    def create_snapshot(
        self,
        world: ECSWorld,
        tick: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> WorldSnapshot:
        """Capture current world state as snapshot.

        Args:
            world: World to capture
            tick: Current tick number
            metadata: Additional metadata to include

        Returns:
            Immutable snapshot of world state
        """
        return self._serializer.serialize(
            world=world,
            tick=tick,
            metadata=metadata,
        )

    def capture_snapshot(
        self,
        world: ECSWorld,
        tick: int = 0,
        metadata: dict[str, Any] | None = None,
        excluded_components: set[str] | None = None,
    ) -> RawSnapshot:
        """Capture current world state as a raw snapshot (hot path).

        Components are serialized to plain dictionaries during capture;
        deeply immutable components reuse their previous serialized dict
        by identity. This is the per-tick capture path used by recording.

        Args:
            world: World to capture
            tick: Current tick number
            metadata: Additional metadata to include
            excluded_components: Component type names to skip during capture

        Returns:
            Raw snapshot with serialized component data
        """
        return self._serializer.capture(
            world=world,
            tick=tick,
            metadata=metadata,
            excluded_components=excluded_components,
        )

    def capture_components(
        self,
        world: ECSWorld,
        included_components: set[str],
    ) -> dict[EntityID, dict[str, Any]]:
        """Capture only the named components from world state.

        Args:
            world: World to capture from
            included_components: Component type names to capture

        Returns:
            Mapping of entity id to serialized data for the named components
        """
        return self._serializer.capture_components(
            world=world,
            included_components=included_components,
        )

    def finalize_snapshot(self, raw_snapshot: RawSnapshot) -> WorldSnapshot:
        """Wrap a raw snapshot into a WorldSnapshot.

        Component data is already serialized at capture time, so this only
        rewraps the snapshot container for storage.

        Args:
            raw_snapshot: Raw snapshot to finalize

        Returns:
            WorldSnapshot ready for storage
        """
        return self._serializer.finalize(raw_snapshot=raw_snapshot)

    def restore_snapshot(
        self,
        snapshot: WorldSnapshot,
        world: ECSWorld,
    ) -> None:
        """Restore world state from snapshot.

        Args:
            snapshot: Snapshot to restore from
            world: World to restore into (will be cleared first)

        Raises:
            ValidationError: If snapshot is invalid
        """
        if not self.validate_snapshot(snapshot=snapshot):
            raise ValidationError(
                field="snapshot",
                reason="Snapshot validation failed",
            )

        self._serializer.deserialize(snapshot=snapshot, world=world)

    @staticmethod
    def validate_snapshot(snapshot: WorldSnapshot) -> bool:
        """Validate snapshot integrity.

        Args:
            snapshot: Snapshot to validate

        Returns:
            True if snapshot is valid
        """
        if snapshot.tick < 0:
            return False

        if snapshot.timestamp <= 0:
            return False

        if not isinstance(snapshot.entities, dict):
            return False  # type: ignore[unreachable]

        if not isinstance(snapshot.metadata, dict):
            return False  # type: ignore[unreachable]

        return True

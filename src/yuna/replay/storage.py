"""Game recording storage and serialization."""

from __future__ import annotations

import gzip
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from yuna.replay.incremental import (
    ComponentChanges,
    EntityChanges,
    IncrementalRecording,
    SnapshotDelta,
)
from yuna.state.snapshot import WorldSnapshot


@dataclass
class GameRecording:
    """Container for game recording data.

    Responsibilities:
    - Store game metadata (seed, start time, players)
    - Store tick snapshots for replay (full mode)
    - Store incremental recording data (incremental mode)
    - Optionally store events and commands
    - Serialize to/from files with compression

    Usage:
        recording = GameRecording(
            metadata={"seed": 42, "players": 2},
            snapshots=[snapshot1, snapshot2],
        )
        recording.to_file(path="game.replay")
        loaded = GameRecording.from_file(path="game.replay")
    """

    metadata: dict[str, Any]
    snapshots: list[WorldSnapshot] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    commands: list[dict[str, Any]] = field(default_factory=list)
    incremental: IncrementalRecording | None = None

    def to_file(self, path: str | Path, compress: bool = True) -> None:
        """Save recording to file.

        Args:
            path: File path to save to
            compress: Whether to use gzip compression (default True)
        """
        path = Path(path)
        data = self._to_dict()
        json_str = json.dumps(obj=data, indent=2)

        if compress:
            path.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(filename=path, mode="wt", encoding="utf-8") as f:
                f.write(json_str)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data=json_str, encoding="utf-8")

    @staticmethod
    def from_file(path: str | Path, compressed: bool = True) -> GameRecording:
        """Load recording from file.

        Args:
            path: File path to load from
            compressed: Whether file is gzip compressed (default True)

        Returns:
            GameRecording instance
        """
        path = Path(path)

        if compressed:
            with gzip.open(filename=path, mode="rt", encoding="utf-8") as f:
                json_str = f.read()
        else:
            json_str = path.read_text(encoding="utf-8")

        data = json.loads(s=json_str)
        return GameRecording._from_dict(data=data)

    def _to_dict(self) -> dict[str, Any]:
        """Convert recording to dictionary.

        Returns:
            Dictionary representation
        """
        result: dict[str, Any] = {
            "metadata": self.metadata,
            "snapshots": [
                {
                    "tick": snapshot.tick,
                    "timestamp": snapshot.timestamp,
                    "entities": dict(snapshot.entities),
                    "metadata": snapshot.metadata,
                }
                for snapshot in self.snapshots
            ],
            "events": self.events,
            "commands": self.commands,
        }

        if self.incremental is not None:
            result["incremental"] = {
                "metadata": self.incremental.metadata,
                "keyframe_interval": self.incremental.keyframe_interval,
                "keyframes": {
                    tick: {
                        "tick": snapshot.tick,
                        "timestamp": snapshot.timestamp,
                        "entities": dict(snapshot.entities),
                        "metadata": snapshot.metadata,
                    }
                    for tick, snapshot in self.incremental.keyframes.items()
                },
                "deltas": {
                    tick: {
                        "tick": delta.tick,
                        "entities": {
                            "added": delta.entities.added,
                            "removed": sorted(delta.entities.removed),
                        },
                        "components": {
                            "added": delta.components.added,
                            "modified": delta.components.modified,
                            "removed": {
                                eid: sorted(names)
                                for eid, names in delta.components.removed.items()
                            },
                        },
                    }
                    for tick, delta in self.incremental.deltas.items()
                },
            }

        return result

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> GameRecording:
        """Convert dictionary to recording.

        Args:
            data: Dictionary data

        Returns:
            GameRecording instance
        """
        snapshots = [
            WorldSnapshot(
                tick=snapshot_data["tick"],
                timestamp=snapshot_data["timestamp"],
                entities=snapshot_data["entities"],
                metadata=snapshot_data["metadata"],
            )
            for snapshot_data in data["snapshots"]
        ]

        incremental = None
        if "incremental" in data:
            incremental_data = data["incremental"]
            keyframes = {
                int(tick): WorldSnapshot(
                    tick=snapshot_data["tick"],
                    timestamp=snapshot_data["timestamp"],
                    entities=snapshot_data["entities"],
                    metadata=snapshot_data["metadata"],
                )
                for tick, snapshot_data in incremental_data["keyframes"].items()
            }
            deltas = {}
            for tick, delta_data in incremental_data["deltas"].items():
                if "entities" in delta_data:
                    entity_changes = EntityChanges(
                        added=delta_data["entities"].get("added", {}),
                        removed=set(delta_data["entities"].get("removed", [])),
                    )
                    component_changes = ComponentChanges(
                        added=delta_data["components"].get("added", {}),
                        modified=delta_data["components"].get("modified", {}),
                        removed={
                            eid: set(names)
                            for eid, names in delta_data["components"]
                            .get("removed", {})
                            .items()
                        },
                    )
                    deltas[int(tick)] = SnapshotDelta(
                        tick=delta_data["tick"],
                        entities=entity_changes,
                        components=component_changes,
                    )
                else:
                    entity_changes = EntityChanges(
                        added=delta_data.get("added_entities", {}),
                        removed=set(delta_data.get("removed_entities", [])),
                    )
                    component_changes = ComponentChanges(
                        modified=delta_data.get("modified_components", {}),
                    )
                    deltas[int(tick)] = SnapshotDelta(
                        tick=delta_data["tick"],
                        entities=entity_changes,
                        components=component_changes,
                    )
            incremental = IncrementalRecording(
                metadata=incremental_data["metadata"],
                keyframe_interval=incremental_data["keyframe_interval"],
                keyframes=keyframes,
                deltas=deltas,
            )

        return GameRecording(
            metadata=data["metadata"],
            snapshots=snapshots,
            events=data.get("events", []),
            commands=data.get("commands", []),
            incremental=incremental,
        )

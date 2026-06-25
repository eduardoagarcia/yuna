"""World snapshot for state capture and replay."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from yuna.types.identifiers import EntityID


@dataclass(frozen=True)
class WorldSnapshot:
    """Immutable snapshot of complete world state at a specific tick.

    Responsibilities:
    - Store complete entity and component data
    - Preserve tick number and timestamp
    - Store additional metadata for replay context
    - Ensure immutability for safe storage and comparison

    Usage:
        snapshot = WorldSnapshot(
            tick=100,
            timestamp=1234567890.0,
            entities={entity_id: {"Position": {"x": 10, "y": 20}}},
            metadata={"seed": 42, "player_count": 4},
        )
    """

    tick: int
    timestamp: float
    entities: dict[EntityID, dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

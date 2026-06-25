"""Raw snapshot for fast state capture without serialization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from yuna.types.identifiers import EntityID


@dataclass
class RawSnapshot:
    """Fast snapshot storing raw component objects without serialization.

    This is used during game execution for high-performance state capture.
    Component objects are stored directly without expensive asdict() conversion.
    After game completes, RawSnapshots are converted to WorldSnapshots for storage.

    Responsibilities:
    - Store raw component objects (not serialized dicts)
    - Minimal overhead during game tick (<0.01ms per tick)
    - Deferred serialization after game completes

    Performance:
    - Capture: ~0.01ms (just shallow copy references)
    - Serialization: ~0.7ms (done after game, not during hot path)

    Usage:
        raw = RawSnapshot(
            tick=100,
            timestamp=1234567890.0,
            entities={entity_id: {"Position": position_obj}},
            metadata={"seed": 42},
        )
    """

    tick: int
    timestamp: float
    entities: dict[EntityID, dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

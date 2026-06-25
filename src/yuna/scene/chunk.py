"""Chunk-based world representation for streaming."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2


class ChunkState(Enum):
    """State of a world chunk."""

    UNLOADED = auto()
    LOADING = auto()
    LOADED = auto()
    UNLOADING = auto()


@dataclass
class ChunkBounds:
    """Spatial bounds of a chunk.

    Attributes:
        min_pos: Minimum position (bottom-left corner)
        max_pos: Maximum position (top-right corner)

    Usage:
        bounds = ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        )
    """

    min_pos: Vector2
    max_pos: Vector2

    def contains(self, position: Vector2) -> bool:
        """Check if position is within chunk bounds.

        Args:
            position: Position to check

        Returns:
            True if position is within bounds
        """
        return (
            self.min_pos.x <= position.x <= self.max_pos.x
            and self.min_pos.y <= position.y <= self.max_pos.y
        )

    def distance_to(self, position: Vector2) -> float:
        """Calculate distance from position to nearest point in chunk.

        Args:
            position: Position to measure distance from

        Returns:
            Distance to chunk (0 if position is inside chunk)
        """
        if self.contains(position=position):
            return 0.0

        closest_x = max(self.min_pos.x, min(position.x, self.max_pos.x))
        closest_y = max(self.min_pos.y, min(position.y, self.max_pos.y))
        closest = Vector2(x=closest_x, y=closest_y)

        return position.distance(other=closest)

    def center(self) -> Vector2:
        """Get center position of chunk.

        Returns:
            Center position
        """
        return Vector2(
            x=(self.min_pos.x + self.max_pos.x) / 2.0,
            y=(self.min_pos.y + self.max_pos.y) / 2.0,
        )


@dataclass
class Chunk:
    """World chunk for streaming system.

    A chunk represents a spatial section of the game world that can be
    loaded and unloaded independently. Chunks contain entities and track
    their loading state.

    Attributes:
        chunk_id: Unique identifier for this chunk
        bounds: Spatial bounds of the chunk
        state: Current loading state
        entities: Set of entity IDs in this chunk
        on_load: Optional callback when chunk loads
        on_unload: Optional callback when chunk unloads
        user_data: Optional custom data for chunk

    Usage:
        chunk = Chunk(
            chunk_id="forest_01",
            bounds=ChunkBounds(
                min_pos=Vector2(x=0.0, y=0.0),
                max_pos=Vector2(x=100.0, y=100.0),
            ),
        )
        chunk.add_entity(entity_id)
        chunk.load()
    """

    chunk_id: str
    bounds: ChunkBounds
    state: ChunkState = ChunkState.UNLOADED
    entities: set[EntityID] = field(default_factory=set)
    on_load: Callable[[], None] | None = None
    on_unload: Callable[[], None] | None = None
    user_data: dict[str, Any] = field(default_factory=dict)

    def add_entity(self, entity_id: EntityID) -> None:
        """Add entity to chunk.

        Args:
            entity_id: Entity to add
        """
        self.entities.add(entity_id)

    def remove_entity(self, entity_id: EntityID) -> None:
        """Remove entity from chunk.

        Args:
            entity_id: Entity to remove
        """
        self.entities.discard(entity_id)

    def has_entity(self, entity_id: EntityID) -> bool:
        """Check if chunk contains entity.

        Args:
            entity_id: Entity to check

        Returns:
            True if entity is in chunk
        """
        return entity_id in self.entities

    def clear_entities(self) -> None:
        """Remove all entities from chunk."""
        self.entities.clear()

    def load(self) -> None:
        """Transition chunk to loading state.

        Triggers on_load callback if set.
        """
        if self.state == ChunkState.UNLOADED:
            self.state = ChunkState.LOADING
            if self.on_load:
                self.on_load()
            self.state = ChunkState.LOADED

    def unload(self) -> None:
        """Transition chunk to unloading state.

        Triggers on_unload callback if set.
        Clears all entities.
        """
        if self.state == ChunkState.LOADED:
            self.state = ChunkState.UNLOADING
            if self.on_unload:
                self.on_unload()
            self.clear_entities()
            self.state = ChunkState.UNLOADED

    def is_loaded(self) -> bool:
        """Check if chunk is fully loaded.

        Returns:
            True if chunk is in LOADED state
        """
        return self.state == ChunkState.LOADED

    def is_loading(self) -> bool:
        """Check if chunk is currently loading.

        Returns:
            True if chunk is in LOADING state
        """
        return self.state == ChunkState.LOADING

    def is_unloaded(self) -> bool:
        """Check if chunk is unloaded.

        Returns:
            True if chunk is in UNLOADED state
        """
        return self.state == ChunkState.UNLOADED

    def contains_position(self, position: Vector2) -> bool:
        """Check if position is within chunk bounds.

        Args:
            position: Position to check

        Returns:
            True if position is within chunk
        """
        return self.bounds.contains(position=position)

    def distance_to_position(self, position: Vector2) -> float:
        """Calculate distance from position to chunk.

        Args:
            position: Position to measure from

        Returns:
            Distance to nearest point in chunk
        """
        return self.bounds.distance_to(position=position)

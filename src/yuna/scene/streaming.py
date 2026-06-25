"""Streaming manager for chunk-based world loading."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from yuna.exceptions import ValidationError
from yuna.scene.chunk import Chunk, ChunkState
from yuna.types.vector import Vector2


@dataclass
class StreamingConfig:
    """Configuration for streaming manager.

    Attributes:
        load_radius: Distance within which chunks auto-load
        unload_radius: Distance beyond which chunks unload
        max_chunks_per_update: Maximum chunks to process per update

    Usage:
        config = StreamingConfig(
            load_radius=200.0,
            unload_radius=300.0,
            max_chunks_per_update=2,
        )
    """

    load_radius: float
    unload_radius: float
    max_chunks_per_update: int = 2

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.load_radius <= 0:
            raise ValidationError(
                field="load_radius",
                value=str(self.load_radius),
                reason="Load radius must be positive",
            )

        if self.unload_radius <= self.load_radius:
            raise ValidationError(
                field="unload_radius",
                value=str(self.unload_radius),
                reason="Unload radius must be greater than load radius",
            )

        if self.max_chunks_per_update < 1:
            raise ValidationError(
                field="max_chunks_per_update",
                value=str(self.max_chunks_per_update),
                reason="Must process at least 1 chunk per update",
            )


class StreamingManager:
    """Manages chunk-based world streaming.

    Responsibilities:
    - Track registered chunks
    - Load chunks within load radius
    - Unload chunks beyond unload radius
    - Process chunks incrementally (no frame drops)
    - Prioritize nearest chunks

    Usage:
        manager = StreamingManager(config=config)
        manager.register_chunk(chunk=chunk)
        manager.update(player_position=position)
    """

    def __init__(self, config: StreamingConfig) -> None:
        """Initialize streaming manager.

        Args:
            config: Streaming configuration
        """
        self.config = config
        self._chunks: dict[str, Chunk] = {}
        self._last_position: Vector2 | None = None

    def register_chunk(self, chunk: Chunk) -> None:
        """Register chunk for streaming.

        Args:
            chunk: Chunk to register

        Raises:
            ValidationError: If chunk ID already registered
        """
        if chunk.chunk_id in self._chunks:
            raise ValidationError(
                field="chunk_id",
                value=chunk.chunk_id,
                reason="Chunk already registered",
            )

        self._chunks[chunk.chunk_id] = chunk

    def unregister_chunk(self, chunk_id: str) -> None:
        """Unregister chunk from streaming.

        Args:
            chunk_id: ID of chunk to unregister

        Raises:
            ValidationError: If chunk not registered
        """
        if chunk_id not in self._chunks:
            raise ValidationError(
                field="chunk_id",
                value=chunk_id,
                reason="Chunk not registered",
            )

        chunk = self._chunks[chunk_id]
        if chunk.is_loaded():
            chunk.unload()

        del self._chunks[chunk_id]

    def get_chunk(self, chunk_id: str) -> Chunk | None:
        """Get chunk by ID.

        Args:
            chunk_id: ID of chunk to get

        Returns:
            Chunk if found, None otherwise
        """
        return self._chunks.get(chunk_id)

    def get_loaded_chunks(self) -> list[Chunk]:
        """Get all loaded chunks.

        Returns:
            List of loaded chunks
        """
        return [chunk for chunk in self._chunks.values() if chunk.is_loaded()]

    def get_chunks_at_position(self, position: Vector2) -> list[Chunk]:
        """Get all chunks containing position.

        Args:
            position: Position to query

        Returns:
            List of chunks containing position
        """
        return [
            chunk
            for chunk in self._chunks.values()
            if chunk.contains_position(position=position)
        ]

    def update(self, player_position: Vector2) -> dict[str, Any]:
        """Update streaming based on player position.

        Loads chunks within load_radius and unloads chunks beyond unload_radius.
        Processes limited number of chunks per update to avoid frame drops.

        Args:
            player_position: Current player position

        Returns:
            Statistics about chunks loaded/unloaded this update
        """
        self._last_position = player_position

        chunks_to_load = self._find_chunks_to_load(position=player_position)
        chunks_to_unload = self._find_chunks_to_unload(position=player_position)

        loaded_count = self._process_loads(chunks=chunks_to_load)
        unloaded_count = self._process_unloads(chunks=chunks_to_unload)

        return {
            "loaded": loaded_count,
            "unloaded": unloaded_count,
            "total_loaded": len(self.get_loaded_chunks()),
            "total_chunks": len(self._chunks),
        }

    def _find_chunks_to_load(self, position: Vector2) -> list[Chunk]:
        """Find chunks that should be loaded.

        Args:
            position: Reference position

        Returns:
            List of chunks to load, sorted by distance (nearest first)
        """
        chunks_to_load: list[tuple[float, Chunk]] = []

        for chunk in self._chunks.values():
            if chunk.is_unloaded():
                distance = chunk.distance_to_position(position=position)
                if distance <= self.config.load_radius:
                    chunks_to_load.append((distance, chunk))

        chunks_to_load.sort(key=lambda x: x[0])
        return [chunk for _, chunk in chunks_to_load]

    def _find_chunks_to_unload(self, position: Vector2) -> list[Chunk]:
        """Find chunks that should be unloaded.

        Args:
            position: Reference position

        Returns:
            List of chunks to unload, sorted by distance (farthest first)
        """
        chunks_to_unload: list[tuple[float, Chunk]] = []

        for chunk in self._chunks.values():
            if chunk.is_loaded():
                distance = chunk.distance_to_position(position=position)
                if distance > self.config.unload_radius:
                    chunks_to_unload.append((distance, chunk))

        chunks_to_unload.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in chunks_to_unload]

    def _process_loads(self, chunks: list[Chunk]) -> int:
        """Process chunk loading with limit.

        Args:
            chunks: Chunks to load (already sorted by priority)

        Returns:
            Number of chunks loaded
        """
        loaded_count = 0

        for chunk in chunks[: self.config.max_chunks_per_update]:
            chunk.load()
            loaded_count += 1

        return loaded_count

    def _process_unloads(self, chunks: list[Chunk]) -> int:
        """Process chunk unloading with limit.

        Args:
            chunks: Chunks to unload (already sorted by priority)

        Returns:
            Number of chunks unloaded
        """
        unloaded_count = 0

        for chunk in chunks[: self.config.max_chunks_per_update]:
            chunk.unload()
            unloaded_count += 1

        return unloaded_count

    def load_all(self) -> None:
        """Load all registered chunks.

        Useful for preloading or testing.
        """
        for chunk in self._chunks.values():
            if chunk.is_unloaded():
                chunk.load()

    def unload_all(self) -> None:
        """Unload all chunks.

        Useful for cleanup or scene transitions.
        """
        for chunk in self._chunks.values():
            if chunk.is_loaded():
                chunk.unload()

    def get_statistics(self) -> dict[str, Any]:
        """Get streaming statistics.

        Returns:
            Dictionary with statistics
        """
        loaded = len([c for c in self._chunks.values() if c.is_loaded()])
        loading = len([c for c in self._chunks.values() if c.is_loading()])
        unloaded = len([c for c in self._chunks.values() if c.is_unloaded()])
        unloading = len([
            c for c in self._chunks.values() if c.state == ChunkState.UNLOADING
        ])

        total_entities = sum(len(c.entities) for c in self._chunks.values())

        return {
            "total_chunks": len(self._chunks),
            "loaded_chunks": loaded,
            "loading_chunks": loading,
            "unloaded_chunks": unloaded,
            "unloading_chunks": unloading,
            "total_entities": total_entities,
            "load_radius": self.config.load_radius,
            "unload_radius": self.config.unload_radius,
        }

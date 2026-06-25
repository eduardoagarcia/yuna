"""Tests for streaming manager."""

import pytest
from faker import Faker

from yuna.exceptions import ValidationError
from yuna.scene.chunk import Chunk, ChunkBounds
from yuna.scene.streaming import StreamingConfig, StreamingManager
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

fake = Faker()


def test_streaming_config_creation() -> None:
    """Test streaming config creation."""
    config = StreamingConfig(
        load_radius=200.0,
        unload_radius=300.0,
        max_chunks_per_update=2,
    )

    assert config.load_radius == 200.0
    assert config.unload_radius == 300.0
    assert config.max_chunks_per_update == 2


def test_streaming_config_invalid_load_radius() -> None:
    """Test streaming config validation for load radius."""
    with pytest.raises(ValidationError, match="Load radius must be positive"):
        StreamingConfig(
            load_radius=0.0,
            unload_radius=300.0,
        )


def test_streaming_config_invalid_unload_radius() -> None:
    """Test streaming config validation for unload radius."""
    with pytest.raises(
        ValidationError, match="Unload radius must be greater than load radius"
    ):
        StreamingConfig(
            load_radius=300.0,
            unload_radius=200.0,
        )


def test_streaming_config_invalid_max_chunks() -> None:
    """Test streaming config validation for max chunks."""
    with pytest.raises(
        ValidationError, match="Must process at least 1 chunk per update"
    ):
        StreamingConfig(
            load_radius=200.0,
            unload_radius=300.0,
            max_chunks_per_update=0,
        )


def test_streaming_manager_creation() -> None:
    """Test streaming manager creation."""
    config = StreamingConfig(
        load_radius=200.0,
        unload_radius=300.0,
    )

    manager = StreamingManager(config=config)

    assert manager.config == config


def test_register_chunk() -> None:
    """Test registering chunk."""
    config = StreamingConfig(load_radius=200.0, unload_radius=300.0)
    manager = StreamingManager(config=config)
    chunk = Chunk(
        chunk_id="chunk_1",
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )

    manager.register_chunk(chunk=chunk)

    assert manager.get_chunk(chunk_id="chunk_1") == chunk


def test_register_duplicate_chunk() -> None:
    """Test registering duplicate chunk raises error."""
    config = StreamingConfig(load_radius=200.0, unload_radius=300.0)
    manager = StreamingManager(config=config)
    chunk = Chunk(
        chunk_id="chunk_1",
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    manager.register_chunk(chunk=chunk)

    with pytest.raises(ValidationError, match="Chunk already registered"):
        manager.register_chunk(chunk=chunk)


def test_unregister_chunk() -> None:
    """Test unregistering chunk."""
    config = StreamingConfig(load_radius=200.0, unload_radius=300.0)
    manager = StreamingManager(config=config)
    chunk = Chunk(
        chunk_id="chunk_1",
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    manager.register_chunk(chunk=chunk)

    manager.unregister_chunk(chunk_id="chunk_1")

    assert manager.get_chunk(chunk_id="chunk_1") is None


def test_unregister_loaded_chunk() -> None:
    """Test unregistering loaded chunk unloads it first."""
    config = StreamingConfig(load_radius=200.0, unload_radius=300.0)
    manager = StreamingManager(config=config)
    chunk = Chunk(
        chunk_id="chunk_1",
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    chunk.load()
    manager.register_chunk(chunk=chunk)

    manager.unregister_chunk(chunk_id="chunk_1")

    assert chunk.is_unloaded() is True


def test_unregister_nonexistent_chunk() -> None:
    """Test unregistering nonexistent chunk raises error."""
    config = StreamingConfig(load_radius=200.0, unload_radius=300.0)
    manager = StreamingManager(config=config)

    with pytest.raises(ValidationError, match="Chunk not registered"):
        manager.unregister_chunk(chunk_id="nonexistent")


def test_get_loaded_chunks() -> None:
    """Test getting loaded chunks."""
    config = StreamingConfig(load_radius=200.0, unload_radius=300.0)
    manager = StreamingManager(config=config)
    chunk1 = Chunk(
        chunk_id="chunk_1",
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    chunk2 = Chunk(
        chunk_id="chunk_2",
        bounds=ChunkBounds(
            min_pos=Vector2(x=100.0, y=0.0),
            max_pos=Vector2(x=200.0, y=100.0),
        ),
    )
    chunk1.load()
    manager.register_chunk(chunk=chunk1)
    manager.register_chunk(chunk=chunk2)

    loaded = manager.get_loaded_chunks()

    assert len(loaded) == 1
    assert loaded[0] == chunk1


def test_get_chunks_at_position() -> None:
    """Test getting chunks at position."""
    config = StreamingConfig(load_radius=200.0, unload_radius=300.0)
    manager = StreamingManager(config=config)
    chunk = Chunk(
        chunk_id="chunk_1",
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    manager.register_chunk(chunk=chunk)

    chunks = manager.get_chunks_at_position(position=Vector2(x=50.0, y=50.0))

    assert len(chunks) == 1
    assert chunks[0] == chunk


def test_update_loads_nearby_chunks() -> None:
    """Test update loads chunks within load radius."""
    config = StreamingConfig(
        load_radius=150.0,
        unload_radius=300.0,
        max_chunks_per_update=10,
    )
    manager = StreamingManager(config=config)
    chunk = Chunk(
        chunk_id="chunk_1",
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    manager.register_chunk(chunk=chunk)

    stats = manager.update(player_position=Vector2(x=50.0, y=50.0))

    assert chunk.is_loaded() is True
    assert stats["loaded"] == 1


def test_update_unloads_far_chunks() -> None:
    """Test update unloads chunks beyond unload radius."""
    config = StreamingConfig(
        load_radius=100.0,
        unload_radius=200.0,
        max_chunks_per_update=10,
    )
    manager = StreamingManager(config=config)
    chunk = Chunk(
        chunk_id="chunk_1",
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    chunk.load()
    manager.register_chunk(chunk=chunk)

    stats = manager.update(player_position=Vector2(x=500.0, y=500.0))

    assert chunk.is_unloaded() is True
    assert stats["unloaded"] == 1


def test_update_respects_max_chunks_limit() -> None:
    """Test update respects max chunks per update limit."""
    config = StreamingConfig(
        load_radius=500.0,
        unload_radius=1000.0,
        max_chunks_per_update=2,
    )
    manager = StreamingManager(config=config)

    for i in range(5):
        chunk = Chunk(
            chunk_id=f"chunk_{i}",
            bounds=ChunkBounds(
                min_pos=Vector2(x=float(i * 100), y=0.0),
                max_pos=Vector2(x=float((i + 1) * 100), y=100.0),
            ),
        )
        manager.register_chunk(chunk=chunk)

    stats = manager.update(player_position=Vector2(x=250.0, y=50.0))

    assert stats["loaded"] <= 2


def test_update_prioritizes_nearest_chunks() -> None:
    """Test update loads nearest chunks first."""
    config = StreamingConfig(
        load_radius=500.0,
        unload_radius=1000.0,
        max_chunks_per_update=1,
    )
    manager = StreamingManager(config=config)

    chunk_near = Chunk(
        chunk_id="chunk_near",
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    chunk_far = Chunk(
        chunk_id="chunk_far",
        bounds=ChunkBounds(
            min_pos=Vector2(x=300.0, y=0.0),
            max_pos=Vector2(x=400.0, y=100.0),
        ),
    )
    manager.register_chunk(chunk=chunk_far)
    manager.register_chunk(chunk=chunk_near)

    manager.update(player_position=Vector2(x=50.0, y=50.0))

    assert chunk_near.is_loaded() is True
    assert chunk_far.is_unloaded() is True


def test_load_all() -> None:
    """Test loading all chunks."""
    config = StreamingConfig(load_radius=200.0, unload_radius=300.0)
    manager = StreamingManager(config=config)
    chunk1 = Chunk(
        chunk_id="chunk_1",
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    chunk2 = Chunk(
        chunk_id="chunk_2",
        bounds=ChunkBounds(
            min_pos=Vector2(x=100.0, y=0.0),
            max_pos=Vector2(x=200.0, y=100.0),
        ),
    )
    manager.register_chunk(chunk=chunk1)
    manager.register_chunk(chunk=chunk2)

    manager.load_all()

    assert chunk1.is_loaded() is True
    assert chunk2.is_loaded() is True


def test_unload_all() -> None:
    """Test unloading all chunks."""
    config = StreamingConfig(load_radius=200.0, unload_radius=300.0)
    manager = StreamingManager(config=config)
    chunk1 = Chunk(
        chunk_id="chunk_1",
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    chunk2 = Chunk(
        chunk_id="chunk_2",
        bounds=ChunkBounds(
            min_pos=Vector2(x=100.0, y=0.0),
            max_pos=Vector2(x=200.0, y=100.0),
        ),
    )
    chunk1.load()
    chunk2.load()
    manager.register_chunk(chunk=chunk1)
    manager.register_chunk(chunk=chunk2)

    manager.unload_all()

    assert chunk1.is_unloaded() is True
    assert chunk2.is_unloaded() is True


def test_get_statistics() -> None:
    """Test getting streaming statistics."""
    config = StreamingConfig(load_radius=200.0, unload_radius=300.0)
    manager = StreamingManager(config=config)
    chunk = Chunk(
        chunk_id="chunk_1",
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    chunk.load()
    chunk.add_entity(entity_id=EntityID(fake.uuid4()))
    manager.register_chunk(chunk=chunk)

    stats = manager.get_statistics()

    assert stats["total_chunks"] == 1
    assert stats["loaded_chunks"] == 1
    assert stats["unloaded_chunks"] == 0
    assert stats["total_entities"] == 1
    assert stats["load_radius"] == 200.0
    assert stats["unload_radius"] == 300.0


def test_update_returns_statistics() -> None:
    """Test update returns statistics."""
    config = StreamingConfig(
        load_radius=150.0,
        unload_radius=300.0,
        max_chunks_per_update=10,
    )
    manager = StreamingManager(config=config)
    chunk = Chunk(
        chunk_id="chunk_1",
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    manager.register_chunk(chunk=chunk)

    stats = manager.update(player_position=Vector2(x=50.0, y=50.0))

    assert "loaded" in stats
    assert "unloaded" in stats
    assert "total_loaded" in stats
    assert "total_chunks" in stats

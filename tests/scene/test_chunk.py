"""Tests for chunk-based world representation."""

from faker import Faker

from yuna.scene.chunk import Chunk, ChunkBounds, ChunkState
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

fake = Faker()


def test_chunk_bounds_contains_inside() -> None:
    """Test bounds contains position inside."""
    bounds = ChunkBounds(
        min_pos=Vector2(x=0.0, y=0.0),
        max_pos=Vector2(x=100.0, y=100.0),
    )

    assert bounds.contains(position=Vector2(x=50.0, y=50.0)) is True


def test_chunk_bounds_contains_edge() -> None:
    """Test bounds contains position on edge."""
    bounds = ChunkBounds(
        min_pos=Vector2(x=0.0, y=0.0),
        max_pos=Vector2(x=100.0, y=100.0),
    )

    assert bounds.contains(position=Vector2(x=0.0, y=0.0)) is True
    assert bounds.contains(position=Vector2(x=100.0, y=100.0)) is True


def test_chunk_bounds_contains_outside() -> None:
    """Test bounds contains position outside."""
    bounds = ChunkBounds(
        min_pos=Vector2(x=0.0, y=0.0),
        max_pos=Vector2(x=100.0, y=100.0),
    )

    assert bounds.contains(position=Vector2(x=-10.0, y=50.0)) is False
    assert bounds.contains(position=Vector2(x=110.0, y=50.0)) is False
    assert bounds.contains(position=Vector2(x=50.0, y=-10.0)) is False
    assert bounds.contains(position=Vector2(x=50.0, y=110.0)) is False


def test_chunk_bounds_distance_inside() -> None:
    """Test distance to bounds when position inside."""
    bounds = ChunkBounds(
        min_pos=Vector2(x=0.0, y=0.0),
        max_pos=Vector2(x=100.0, y=100.0),
    )

    distance = bounds.distance_to(position=Vector2(x=50.0, y=50.0))

    assert distance == 0.0


def test_chunk_bounds_distance_outside() -> None:
    """Test distance to bounds when position outside."""
    bounds = ChunkBounds(
        min_pos=Vector2(x=0.0, y=0.0),
        max_pos=Vector2(x=100.0, y=100.0),
    )

    distance = bounds.distance_to(position=Vector2(x=150.0, y=50.0))

    assert distance == 50.0


def test_chunk_bounds_center() -> None:
    """Test bounds center calculation."""
    bounds = ChunkBounds(
        min_pos=Vector2(x=0.0, y=0.0),
        max_pos=Vector2(x=100.0, y=100.0),
    )

    center = bounds.center()

    assert center.x == 50.0
    assert center.y == 50.0


def test_chunk_creation() -> None:
    """Test chunk creation."""
    chunk_id = fake.word()
    bounds = ChunkBounds(
        min_pos=Vector2(x=0.0, y=0.0),
        max_pos=Vector2(x=100.0, y=100.0),
    )

    chunk = Chunk(chunk_id=chunk_id, bounds=bounds)

    assert chunk.chunk_id == chunk_id
    assert chunk.bounds == bounds
    assert chunk.state == ChunkState.UNLOADED
    assert len(chunk.entities) == 0


def test_chunk_add_entity() -> None:
    """Test adding entity to chunk."""
    chunk = Chunk(
        chunk_id=fake.word(),
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    entity_id = EntityID(fake.uuid4())

    chunk.add_entity(entity_id=entity_id)

    assert chunk.has_entity(entity_id=entity_id) is True
    assert len(chunk.entities) == 1


def test_chunk_remove_entity() -> None:
    """Test removing entity from chunk."""
    chunk = Chunk(
        chunk_id=fake.word(),
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    entity_id = EntityID(fake.uuid4())
    chunk.add_entity(entity_id=entity_id)

    chunk.remove_entity(entity_id=entity_id)

    assert chunk.has_entity(entity_id=entity_id) is False
    assert len(chunk.entities) == 0


def test_chunk_clear_entities() -> None:
    """Test clearing all entities from chunk."""
    chunk = Chunk(
        chunk_id=fake.word(),
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    entity_id_1 = EntityID(fake.uuid4())
    entity_id_2 = EntityID(fake.uuid4())
    chunk.add_entity(entity_id=entity_id_1)
    chunk.add_entity(entity_id=entity_id_2)

    chunk.clear_entities()

    assert len(chunk.entities) == 0


def test_chunk_load() -> None:
    """Test chunk loading."""
    chunk = Chunk(
        chunk_id=fake.word(),
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )

    chunk.load()

    assert chunk.is_loaded() is True
    assert chunk.state == ChunkState.LOADED


def test_chunk_load_callback() -> None:
    """Test chunk load callback is triggered."""
    called = False

    def on_load() -> None:
        nonlocal called
        called = True

    chunk = Chunk(
        chunk_id=fake.word(),
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
        on_load=on_load,
    )

    chunk.load()

    assert called is True


def test_chunk_unload() -> None:
    """Test chunk unloading."""
    chunk = Chunk(
        chunk_id=fake.word(),
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    chunk.load()

    chunk.unload()

    assert chunk.is_unloaded() is True
    assert chunk.state == ChunkState.UNLOADED


def test_chunk_unload_clears_entities() -> None:
    """Test chunk unload clears entities."""
    chunk = Chunk(
        chunk_id=fake.word(),
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )
    chunk.load()
    chunk.add_entity(entity_id=EntityID(fake.uuid4()))

    chunk.unload()

    assert len(chunk.entities) == 0


def test_chunk_unload_callback() -> None:
    """Test chunk unload callback is triggered."""
    called = False

    def on_unload() -> None:
        nonlocal called
        called = True

    chunk = Chunk(
        chunk_id=fake.word(),
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
        on_unload=on_unload,
    )
    chunk.load()

    chunk.unload()

    assert called is True


def test_chunk_is_loading() -> None:
    """Test chunk is_loading check."""
    chunk = Chunk(
        chunk_id=fake.word(),
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )

    assert chunk.is_loading() is False
    assert chunk.is_loaded() is False
    assert chunk.is_unloaded() is True


def test_chunk_contains_position() -> None:
    """Test chunk contains_position."""
    chunk = Chunk(
        chunk_id=fake.word(),
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )

    assert chunk.contains_position(position=Vector2(x=50.0, y=50.0)) is True
    assert chunk.contains_position(position=Vector2(x=150.0, y=50.0)) is False


def test_chunk_distance_to_position() -> None:
    """Test chunk distance_to_position."""
    chunk = Chunk(
        chunk_id=fake.word(),
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
    )

    distance_inside = chunk.distance_to_position(position=Vector2(x=50.0, y=50.0))
    distance_outside = chunk.distance_to_position(position=Vector2(x=150.0, y=50.0))

    assert distance_inside == 0.0
    assert distance_outside == 50.0


def test_chunk_user_data() -> None:
    """Test chunk user data."""
    chunk = Chunk(
        chunk_id=fake.word(),
        bounds=ChunkBounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        ),
        user_data={"difficulty": "hard"},
    )

    assert chunk.user_data["difficulty"] == "hard"

"""Tests for double-buffered component storage."""

from dataclasses import dataclass
from threading import Thread

from faker import Faker

from yuna.ecs.buffer import DoubleBufferedStore
from yuna.ecs.component import Component
from yuna.types.identifiers import EntityID

fake = Faker()


@dataclass
class Position(Component):
    x: float
    y: float


@dataclass
class Velocity(Component):
    dx: float
    dy: float


def test_double_buffered_store_creation() -> None:
    store = DoubleBufferedStore()

    assert store is not None


def test_write_and_read_after_swap() -> None:
    store = DoubleBufferedStore()
    entity_id = EntityID(fake.uuid4())

    store.write(
        entity_id=entity_id,
        component_type=Position,
        component=Position(x=1.0, y=2.0),
    )

    position = store.read(entity_id=entity_id, component_type=Position)
    assert position is None

    store.swap()

    position = store.read(entity_id=entity_id, component_type=Position)
    assert position is not None
    assert position.x == 1.0
    assert position.y == 2.0


def test_read_returns_none_for_non_existent_component() -> None:
    store = DoubleBufferedStore()
    entity_id = EntityID(fake.uuid4())

    position = store.read(entity_id=entity_id, component_type=Position)

    assert position is None


def test_swap_makes_write_buffer_readable() -> None:
    store = DoubleBufferedStore()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    store.write(
        entity_id=entity1, component_type=Position, component=Position(x=1.0, y=1.0)
    )
    store.write(
        entity_id=entity2, component_type=Position, component=Position(x=2.0, y=2.0)
    )

    assert store.read(entity_id=entity1, component_type=Position) is None
    assert store.read(entity_id=entity2, component_type=Position) is None

    store.swap()

    pos1 = store.read(entity_id=entity1, component_type=Position)
    pos2 = store.read(entity_id=entity2, component_type=Position)

    assert pos1 is not None
    assert pos1.x == 1.0
    assert pos2 is not None
    assert pos2.x == 2.0


def test_has_checks_read_buffer() -> None:
    store = DoubleBufferedStore()
    entity_id = EntityID(fake.uuid4())

    store.write(
        entity_id=entity_id, component_type=Position, component=Position(x=1.0, y=1.0)
    )

    assert not store.has(entity_id=entity_id, component_type=Position)

    store.swap()

    assert store.has(entity_id=entity_id, component_type=Position)


def test_has_returns_false_for_non_existent_component() -> None:
    store = DoubleBufferedStore()
    entity_id = EntityID(fake.uuid4())

    assert not store.has(entity_id=entity_id, component_type=Position)


def test_get_all_returns_components_from_read_buffer() -> None:
    store = DoubleBufferedStore()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    store.write(
        entity_id=entity1, component_type=Position, component=Position(x=1.0, y=1.0)
    )
    store.write(
        entity_id=entity2, component_type=Position, component=Position(x=2.0, y=2.0)
    )

    all_positions = store.get_all(component_type=Position)
    assert len(all_positions) == 0

    store.swap()

    all_positions = store.get_all(component_type=Position)
    assert len(all_positions) == 2
    assert entity1 in all_positions
    assert entity2 in all_positions


def test_get_all_returns_empty_for_non_existent_type() -> None:
    store = DoubleBufferedStore()

    all_positions = store.get_all(component_type=Position)

    assert len(all_positions) == 0


def test_multiple_swaps() -> None:
    store = DoubleBufferedStore()
    entity_id = EntityID(fake.uuid4())

    store.write(
        entity_id=entity_id, component_type=Position, component=Position(x=1.0, y=1.0)
    )
    store.swap()

    pos = store.read(entity_id=entity_id, component_type=Position)
    assert pos is not None
    assert pos.x == 1.0

    store.write(
        entity_id=entity_id, component_type=Position, component=Position(x=2.0, y=2.0)
    )
    store.swap()

    pos = store.read(entity_id=entity_id, component_type=Position)
    assert pos is not None
    assert pos.x == 2.0


def test_swap_clears_write_buffer() -> None:
    store = DoubleBufferedStore()
    entity_id = EntityID(fake.uuid4())

    store.write(
        entity_id=entity_id, component_type=Position, component=Position(x=1.0, y=1.0)
    )
    store.swap()

    pos = store.read(entity_id=entity_id, component_type=Position)
    assert pos is not None

    store.swap()

    pos = store.read(entity_id=entity_id, component_type=Position)
    assert pos is None


def test_clear_write_buffer() -> None:
    store = DoubleBufferedStore()
    entity_id = EntityID(fake.uuid4())

    store.write(
        entity_id=entity_id, component_type=Position, component=Position(x=1.0, y=1.0)
    )

    store.clear_write_buffer()
    store.swap()

    pos = store.read(entity_id=entity_id, component_type=Position)
    assert pos is None


def test_copy_to_write_buffer() -> None:
    store = DoubleBufferedStore()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    store.write(
        entity_id=entity1, component_type=Position, component=Position(x=1.0, y=1.0)
    )
    store.write(
        entity_id=entity2, component_type=Position, component=Position(x=2.0, y=2.0)
    )
    store.swap()

    store.copy_to_write_buffer()
    store.swap()

    pos1 = store.read(entity_id=entity1, component_type=Position)
    pos2 = store.read(entity_id=entity2, component_type=Position)

    assert pos1 is not None
    assert pos1.x == 1.0
    assert pos2 is not None
    assert pos2.x == 2.0


def test_copy_to_write_buffer_preserves_state() -> None:
    store = DoubleBufferedStore()
    entity_id = EntityID(fake.uuid4())

    store.write(
        entity_id=entity_id, component_type=Position, component=Position(x=1.0, y=1.0)
    )
    store.swap()

    store.copy_to_write_buffer()

    store.write(
        entity_id=entity_id, component_type=Velocity, component=Velocity(dx=0.5, dy=0.5)
    )
    store.swap()

    pos = store.read(entity_id=entity_id, component_type=Position)
    vel = store.read(entity_id=entity_id, component_type=Velocity)

    assert pos is not None
    assert pos.x == 1.0
    assert vel is not None
    assert vel.dx == 0.5


def test_multiple_component_types() -> None:
    store = DoubleBufferedStore()
    entity_id = EntityID(fake.uuid4())

    store.write(
        entity_id=entity_id, component_type=Position, component=Position(x=1.0, y=1.0)
    )
    store.write(
        entity_id=entity_id, component_type=Velocity, component=Velocity(dx=0.5, dy=0.5)
    )
    store.swap()

    pos = store.read(entity_id=entity_id, component_type=Position)
    vel = store.read(entity_id=entity_id, component_type=Velocity)

    assert pos is not None
    assert pos.x == 1.0
    assert vel is not None
    assert vel.dx == 0.5


def test_read_during_write_no_conflicts() -> None:
    store = DoubleBufferedStore()
    entity_id = EntityID(fake.uuid4())

    store.write(
        entity_id=entity_id, component_type=Position, component=Position(x=1.0, y=1.0)
    )
    store.swap()

    original_pos = store.read(entity_id=entity_id, component_type=Position)

    store.write(
        entity_id=entity_id, component_type=Position, component=Position(x=2.0, y=2.0)
    )

    current_pos = store.read(entity_id=entity_id, component_type=Position)

    assert original_pos is not None
    assert original_pos.x == 1.0
    assert current_pos is not None
    assert current_pos.x == 1.0


def test_thread_safe_swap() -> None:
    store = DoubleBufferedStore()
    entity_id = EntityID(fake.uuid4())
    results: list[Position | None] = []

    def write_and_swap() -> None:
        store.write(
            entity_id=entity_id,
            component_type=Position,
            component=Position(x=1.0, y=1.0),
        )
        store.swap()

    def read_after_delay() -> None:
        pos = store.read(entity_id=entity_id, component_type=Position)
        results.append(pos)

    thread1 = Thread(target=write_and_swap)
    thread2 = Thread(target=read_after_delay)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    assert len(results) == 1


def test_overwrite_component_in_write_buffer() -> None:
    store = DoubleBufferedStore()
    entity_id = EntityID(fake.uuid4())

    store.write(
        entity_id=entity_id, component_type=Position, component=Position(x=1.0, y=1.0)
    )
    store.write(
        entity_id=entity_id, component_type=Position, component=Position(x=2.0, y=2.0)
    )
    store.swap()

    pos = store.read(entity_id=entity_id, component_type=Position)

    assert pos is not None
    assert pos.x == 2.0

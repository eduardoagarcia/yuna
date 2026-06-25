"""Tests for Scene class."""

from dataclasses import dataclass

from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.system import System
from yuna.ecs.world import ECSWorld
from yuna.scene.scene import Scene

fake = Faker()


@dataclass
class TestComponent(Component):
    """Test component."""

    value: int


class TestSystem(System):
    """Test system for tracking updates."""

    def __init__(self, priority_value: int) -> None:
        self._priority = priority_value
        self.update_count = 0
        self.last_delta_time = 0.0

    @property
    def priority(self) -> int:
        return self._priority

    def update(self, world: ECSWorld, delta_time: float) -> None:
        self.update_count += 1
        self.last_delta_time = delta_time


def test_scene_creation() -> None:
    """Test scene can be created."""
    name = fake.word()
    scene = Scene(name=name)

    assert scene.name == name
    assert scene.world is not None
    assert scene.event_bus is not None
    assert scene.systems == []
    assert scene.metadata == {}
    assert scene.is_loaded is False


def test_scene_creation_with_metadata() -> None:
    """Test scene can be created with metadata."""
    name = fake.word()
    metadata = {fake.word(): fake.word()}
    scene = Scene(name=name, metadata=metadata)

    assert scene.metadata == metadata


def test_add_system() -> None:
    """Test adding system to scene."""
    scene = Scene(name=fake.word())
    system = TestSystem(priority_value=100)

    scene.add_system(system=system)

    assert system in scene.systems


def test_add_system_maintains_priority_order() -> None:
    """Test systems are sorted by priority when added."""
    scene = Scene(name=fake.word())
    system_1 = TestSystem(priority_value=200)
    system_2 = TestSystem(priority_value=100)
    system_3 = TestSystem(priority_value=300)

    scene.add_system(system=system_1)
    scene.add_system(system=system_2)
    scene.add_system(system=system_3)

    assert scene.systems == [system_2, system_1, system_3]


def test_load_scene() -> None:
    """Test loading scene."""
    scene = Scene(name=fake.word())

    scene.load()

    assert scene.is_loaded is True


def test_load_scene_idempotent() -> None:
    """Test loading already loaded scene does nothing."""
    scene = Scene(name=fake.word())

    scene.load()
    scene.load()

    assert scene.is_loaded is True


def test_unload_scene() -> None:
    """Test unloading scene."""
    scene = Scene(name=fake.word())
    scene.load()

    scene.unload()

    assert scene.is_loaded is False


def test_unload_scene_idempotent() -> None:
    """Test unloading already unloaded scene does nothing."""
    scene = Scene(name=fake.word())

    scene.unload()
    scene.unload()

    assert scene.is_loaded is False


def test_update_scene() -> None:
    """Test updating scene updates systems."""
    scene = Scene(name=fake.word())
    system = TestSystem(priority_value=100)
    scene.add_system(system=system)
    scene.load()

    delta_time = fake.pyfloat(min_value=0.01, max_value=0.1)
    scene.update(delta_time=delta_time)

    assert system.update_count == 1
    assert system.last_delta_time == delta_time


def test_update_scene_not_loaded() -> None:
    """Test updating unloaded scene does nothing."""
    scene = Scene(name=fake.word())
    system = TestSystem(priority_value=100)
    scene.add_system(system=system)

    scene.update(delta_time=0.016)

    assert system.update_count == 0


def test_update_scene_multiple_systems() -> None:
    """Test updating scene with multiple systems."""
    scene = Scene(name=fake.word())
    system_1 = TestSystem(priority_value=100)
    system_2 = TestSystem(priority_value=200)
    scene.add_system(system=system_1)
    scene.add_system(system=system_2)
    scene.load()

    scene.update(delta_time=0.016)

    assert system_1.update_count == 1
    assert system_2.update_count == 1


def test_scene_world_is_unique() -> None:
    """Test each scene has unique ECS world."""
    scene_1 = Scene(name=fake.word())
    scene_2 = Scene(name=fake.word())

    assert scene_1.world is not scene_2.world


def test_scene_event_bus_is_unique() -> None:
    """Test each scene has unique event bus."""
    scene_1 = Scene(name=fake.word())
    scene_2 = Scene(name=fake.word())

    assert scene_1.event_bus is not scene_2.event_bus


def test_scene_world_isolated() -> None:
    """Test scene worlds are isolated from each other."""
    scene_1 = Scene(name=fake.word())
    scene_2 = Scene(name=fake.word())

    entity_1 = scene_1.world.create_entity()
    entity_2 = scene_2.world.create_entity()

    assert entity_1 in scene_1.world.get_all_entities()
    assert entity_1 not in scene_2.world.get_all_entities()
    assert entity_2 in scene_2.world.get_all_entities()
    assert entity_2 not in scene_1.world.get_all_entities()

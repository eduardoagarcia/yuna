"""Tests for SceneManager."""

import pytest
from faker import Faker

from yuna.exceptions import ValidationError
from yuna.scene.manager import (
    NoActiveSceneError,
    SceneManager,
    SceneNotFoundError,
)
from yuna.scene.scene import Scene
from yuna.scene.transition import (
    CrossfadeTransition,
    FadeTransition,
)

fake = Faker()


def test_scene_manager_creation() -> None:
    """Test scene manager can be created."""
    manager = SceneManager()

    assert manager is not None


def test_register_scene() -> None:
    """Test registering scene with manager."""
    manager = SceneManager()
    scene = Scene(name=fake.word())

    manager.register_scene(scene=scene)


def test_load_scene() -> None:
    """Test loading scene."""
    manager = SceneManager()
    scene = Scene(name=fake.word())
    manager.register_scene(scene=scene)

    manager.load_scene(scene_name=scene.name)

    assert scene.is_loaded is True
    assert manager.get_active_scene() == scene


def test_load_scene_with_transition() -> None:
    """Test loading scene with custom transition."""
    manager = SceneManager()
    scene = Scene(name=fake.word())
    manager.register_scene(scene=scene)
    transition = FadeTransition(duration=1.0)

    manager.load_scene(scene_name=scene.name, transition=transition)

    assert scene.is_loaded is True


def test_load_scene_not_registered() -> None:
    """Test loading unregistered scene raises error."""
    manager = SceneManager()

    with pytest.raises(SceneNotFoundError):
        manager.load_scene(scene_name=fake.word())


def test_load_scene_unloads_previous() -> None:
    """Test loading new scene unloads previous scene."""
    manager = SceneManager()
    scene_1 = Scene(name=fake.word())
    scene_2 = Scene(name=fake.word())
    manager.register_scene(scene=scene_1)
    manager.register_scene(scene=scene_2)

    manager.load_scene(scene_name=scene_1.name)
    manager.load_scene(scene_name=scene_2.name)

    assert scene_1.is_loaded is False
    assert scene_2.is_loaded is True
    assert manager.get_active_scene() == scene_2


def test_load_scene_additive() -> None:
    """Test loading scene additively."""
    manager = SceneManager()
    scene_1 = Scene(name=fake.word())
    scene_2 = Scene(name=fake.word())
    manager.register_scene(scene=scene_1)
    manager.register_scene(scene=scene_2)

    manager.load_scene(scene_name=scene_1.name)
    manager.load_scene_additive(scene_name=scene_2.name)

    assert scene_1.is_loaded is True
    assert scene_2.is_loaded is True
    assert manager.get_active_scene() == scene_1


def test_load_scene_additive_not_registered() -> None:
    """Test loading unregistered scene additively raises error."""
    manager = SceneManager()

    with pytest.raises(SceneNotFoundError):
        manager.load_scene_additive(scene_name=fake.word())


def test_load_scene_additive_idempotent() -> None:
    """Test loading same scene additively twice is idempotent."""
    manager = SceneManager()
    scene = Scene(name=fake.word())
    manager.register_scene(scene=scene)

    manager.load_scene(scene_name=scene.name)
    manager.load_scene_additive(scene_name=scene.name)

    loaded_scenes = manager.get_loaded_scenes()
    assert loaded_scenes.count(scene) == 1


def test_unload_scene() -> None:
    """Test unloading additive scene."""
    manager = SceneManager()
    name_1 = fake.word()
    name_2 = fake.word()
    if name_1 == name_2:
        name_2 = f"{name_2}_2"
    scene_1 = Scene(name=name_1)
    scene_2 = Scene(name=name_2)
    manager.register_scene(scene=scene_1)
    manager.register_scene(scene=scene_2)

    manager.load_scene(scene_name=scene_1.name)
    manager.load_scene_additive(scene_name=scene_2.name)
    manager.unload_scene(scene_name=scene_2.name)

    assert scene_2.is_loaded is False
    assert scene_1.is_loaded is True


def test_unload_scene_not_registered() -> None:
    """Test unloading unregistered scene raises error."""
    manager = SceneManager()

    with pytest.raises(SceneNotFoundError):
        manager.unload_scene(scene_name=fake.word())


def test_unload_active_scene_raises_error() -> None:
    """Test unloading active scene raises error."""
    manager = SceneManager()
    scene = Scene(name=fake.word())
    manager.register_scene(scene=scene)
    manager.load_scene(scene_name=scene.name)

    with pytest.raises(ValidationError):
        manager.unload_scene(scene_name=scene.name)


def test_unload_scene_not_loaded() -> None:
    """Test unloading scene that isn't loaded does nothing."""
    manager = SceneManager()
    scene = Scene(name=fake.word())
    manager.register_scene(scene=scene)

    manager.unload_scene(scene_name=scene.name)


def test_get_active_scene() -> None:
    """Test getting active scene."""
    manager = SceneManager()
    scene = Scene(name=fake.word())
    manager.register_scene(scene=scene)
    manager.load_scene(scene_name=scene.name)

    active = manager.get_active_scene()

    assert active == scene


def test_get_active_scene_no_scene_loaded() -> None:
    """Test getting active scene when none loaded raises error."""
    manager = SceneManager()

    with pytest.raises(NoActiveSceneError):
        manager.get_active_scene()


def test_get_loaded_scenes() -> None:
    """Test getting all loaded scenes."""
    manager = SceneManager()
    scene_1 = Scene(name=fake.unique.word())
    scene_2 = Scene(name=fake.unique.word())
    scene_3 = Scene(name=fake.unique.word())
    manager.register_scene(scene=scene_1)
    manager.register_scene(scene=scene_2)
    manager.register_scene(scene=scene_3)

    manager.load_scene(scene_name=scene_1.name)
    manager.load_scene_additive(scene_name=scene_2.name)
    manager.load_scene_additive(scene_name=scene_3.name)

    loaded = manager.get_loaded_scenes()

    assert len(loaded) == 3
    assert scene_1 in loaded
    assert scene_2 in loaded
    assert scene_3 in loaded


def test_get_loaded_scenes_returns_copy() -> None:
    """Test get_loaded_scenes returns copy not reference."""
    manager = SceneManager()
    scene = Scene(name=fake.word())
    manager.register_scene(scene=scene)
    manager.load_scene(scene_name=scene.name)

    loaded_1 = manager.get_loaded_scenes()
    loaded_2 = manager.get_loaded_scenes()

    assert loaded_1 == loaded_2
    assert loaded_1 is not loaded_2


def test_update_manager() -> None:
    """Test updating manager updates all loaded scenes."""
    manager = SceneManager()
    scene_1 = Scene(name=fake.word())
    scene_2 = Scene(name=fake.word())
    manager.register_scene(scene=scene_1)
    manager.register_scene(scene=scene_2)

    manager.load_scene(scene_name=scene_1.name)
    manager.load_scene_additive(scene_name=scene_2.name)

    entity_1 = scene_1.world.create_entity()
    entity_2 = scene_2.world.create_entity()

    manager.update(delta_time=0.016)

    assert entity_1 in scene_1.world.get_all_entities()
    assert entity_2 in scene_2.world.get_all_entities()


def test_load_scene_uses_instant_transition_by_default() -> None:
    """Test load_scene uses instant transition when none provided."""
    manager = SceneManager()
    scene = Scene(name=fake.word())
    manager.register_scene(scene=scene)

    manager.load_scene(scene_name=scene.name)

    assert scene.is_loaded is True


def test_load_scene_with_crossfade_transition() -> None:
    """Test loading scene with crossfade transition."""
    manager = SceneManager()
    scene_1 = Scene(name=fake.word())
    scene_2 = Scene(name=fake.word())
    manager.register_scene(scene=scene_1)
    manager.register_scene(scene=scene_2)
    transition = CrossfadeTransition(duration=2.0)

    manager.load_scene(scene_name=scene_1.name)
    manager.load_scene(scene_name=scene_2.name, transition=transition)

    assert scene_2.is_loaded is True
    assert scene_1.is_loaded is False


def test_multiple_scenes_loaded_simultaneously() -> None:
    """Test multiple scenes can be loaded at same time."""
    manager = SceneManager()
    scenes = [Scene(name=fake.unique.word()) for _ in range(5)]
    for scene in scenes:
        manager.register_scene(scene=scene)

    manager.load_scene(scene_name=scenes[0].name)
    for scene in scenes[1:]:
        manager.load_scene_additive(scene_name=scene.name)

    loaded = manager.get_loaded_scenes()
    assert len(loaded) == 5
    for scene in scenes:
        assert scene.is_loaded is True


def test_load_scene_unloads_all_additive_scenes() -> None:
    """Test load_scene unloads all additive scenes."""
    manager = SceneManager()
    scene_1 = Scene(name=fake.word())
    scene_2 = Scene(name=fake.word())
    scene_3 = Scene(name=fake.word())
    manager.register_scene(scene=scene_1)
    manager.register_scene(scene=scene_2)
    manager.register_scene(scene=scene_3)

    manager.load_scene(scene_name=scene_1.name)
    manager.load_scene_additive(scene_name=scene_2.name)
    manager.load_scene(scene_name=scene_3.name)

    assert scene_1.is_loaded is False
    assert scene_2.is_loaded is False
    assert scene_3.is_loaded is True
    assert len(manager.get_loaded_scenes()) == 1

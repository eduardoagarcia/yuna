"""Tests for scene transitions."""

from faker import Faker

from yuna.scene.scene import Scene
from yuna.scene.transition import (
    CrossfadeTransition,
    FadeTransition,
    InstantTransition,
    SceneTransition,
)

fake = Faker()


def test_instant_transition_execute() -> None:
    """Test instant transition executes without error."""
    transition = InstantTransition()
    from_scene = Scene(name=fake.word())
    to_scene = Scene(name=fake.word())

    transition.execute(from_scene=from_scene, to_scene=to_scene)


def test_instant_transition_execute_with_no_from_scene() -> None:
    """Test instant transition works when from_scene is None."""
    transition = InstantTransition()
    to_scene = Scene(name=fake.word())

    transition.execute(from_scene=None, to_scene=to_scene)


def test_fade_transition_has_duration() -> None:
    """Test fade transition stores duration."""
    duration = fake.pyfloat(min_value=0.1, max_value=5.0)
    transition = FadeTransition(duration=duration)

    assert transition.duration == duration


def test_fade_transition_execute() -> None:
    """Test fade transition executes without error."""
    transition = FadeTransition(duration=1.0)
    from_scene = Scene(name=fake.word())
    to_scene = Scene(name=fake.word())

    transition.execute(from_scene=from_scene, to_scene=to_scene)


def test_fade_transition_execute_with_no_from_scene() -> None:
    """Test fade transition works when from_scene is None."""
    transition = FadeTransition(duration=1.0)
    to_scene = Scene(name=fake.word())

    transition.execute(from_scene=None, to_scene=to_scene)


def test_crossfade_transition_has_duration() -> None:
    """Test crossfade transition stores duration."""
    duration = fake.pyfloat(min_value=0.1, max_value=5.0)
    transition = CrossfadeTransition(duration=duration)

    assert transition.duration == duration


def test_crossfade_transition_execute() -> None:
    """Test crossfade transition executes without error."""
    transition = CrossfadeTransition(duration=1.0)
    from_scene = Scene(name=fake.word())
    to_scene = Scene(name=fake.word())

    transition.execute(from_scene=from_scene, to_scene=to_scene)


def test_crossfade_transition_execute_with_no_from_scene() -> None:
    """Test crossfade transition works when from_scene is None."""
    transition = CrossfadeTransition(duration=1.0)
    to_scene = Scene(name=fake.word())

    transition.execute(from_scene=None, to_scene=to_scene)


def test_transition_is_abstract() -> None:
    """Test SceneTransition cannot be instantiated directly."""
    try:
        SceneTransition()  # type: ignore[abstract]
        raise AssertionError("Should not be able to instantiate SceneTransition")
    except TypeError:
        pass

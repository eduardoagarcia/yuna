"""Tests for ECS system base class."""

from unittest.mock import MagicMock

import pytest

from yuna.ecs.system import System
from yuna.ecs.world import ECSWorld


class ConcreteSystem(System):
    """Test system implementation."""

    def __init__(self, priority_value: int = 100) -> None:
        self._priority = priority_value
        self.update_called = False
        self.last_delta_time = 0.0

    @property
    def priority(self) -> int:
        return self._priority

    def update(self, world: ECSWorld, delta_time: float) -> None:
        self.update_called = True
        self.last_delta_time = delta_time


class AnotherSystem(System):
    """Another test system implementation."""

    @property
    def priority(self) -> int:
        return 200

    def update(self, world: ECSWorld, delta_time: float) -> None:
        pass


def test_system_is_abstract() -> None:
    """Test System cannot be instantiated directly."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        System()  # type: ignore[abstract]


def test_concrete_system_can_be_instantiated() -> None:
    """Test concrete system implementing all abstract methods can be created."""
    system = ConcreteSystem()
    assert system is not None
    assert isinstance(system, System)


def test_system_has_priority_property() -> None:
    """Test system priority property returns correct value."""
    system = ConcreteSystem(priority_value=50)
    assert system.priority == 50


def test_system_update_method_can_be_called() -> None:
    """Test system update method can be called."""
    system = ConcreteSystem()
    world = MagicMock()
    delta_time = 0.016
    system.update(world=world, delta_time=delta_time)
    assert system.update_called is True
    assert system.last_delta_time == delta_time


def test_system_update_receives_world() -> None:
    """Test system update method receives world parameter."""
    system = ConcreteSystem()
    world = MagicMock()
    system.update(world=world, delta_time=0.016)
    assert world is not None


def test_different_systems_have_different_priorities() -> None:
    """Test different system types can have different priorities."""
    system1 = ConcreteSystem(priority_value=100)
    system2 = AnotherSystem()
    assert system1.priority != system2.priority


def test_system_priority_can_be_zero() -> None:
    """Test system priority can be zero."""
    system = ConcreteSystem(priority_value=0)
    assert system.priority == 0


def test_system_priority_can_be_negative() -> None:
    """Test system priority can be negative."""
    system = ConcreteSystem(priority_value=-100)
    assert system.priority == -100


def test_system_priority_can_be_large() -> None:
    """Test system priority can be large value."""
    system = ConcreteSystem(priority_value=999999)
    assert system.priority == 999999


def test_system_update_with_zero_delta_time() -> None:
    """Test system update works with zero delta time."""
    system = ConcreteSystem()
    world = MagicMock()
    system.update(world=world, delta_time=0.0)
    assert system.update_called is True
    assert system.last_delta_time == 0.0


def test_system_update_with_large_delta_time() -> None:
    """Test system update works with large delta time."""
    system = ConcreteSystem()
    world = MagicMock()
    delta_time = 1000.0
    system.update(world=world, delta_time=delta_time)
    assert system.last_delta_time == delta_time


def test_multiple_systems_can_be_created() -> None:
    """Test multiple system instances can be created."""
    system1 = ConcreteSystem(priority_value=100)
    system2 = ConcreteSystem(priority_value=200)
    system3 = AnotherSystem()
    assert system1 is not system2
    assert system2 is not system3


def test_system_sorting_by_priority() -> None:
    """Test systems can be sorted by priority."""
    system1 = ConcreteSystem(priority_value=300)
    system2 = ConcreteSystem(priority_value=100)
    system3 = ConcreteSystem(priority_value=200)
    systems = [system1, system2, system3]
    sorted_systems = sorted(systems, key=lambda s: s.priority)
    assert sorted_systems[0].priority == 100
    assert sorted_systems[1].priority == 200
    assert sorted_systems[2].priority == 300


def test_incomplete_system_implementation_raises_error() -> None:
    """Test system without priority implementation cannot be instantiated."""

    class IncompleteSystem(System):
        def update(self, world: ECSWorld, delta_time: float) -> None:
            pass

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteSystem()  # type: ignore[abstract]


def test_incomplete_system_without_update_raises_error() -> None:
    """Test system without update implementation cannot be instantiated."""

    class IncompleteSystem(System):
        @property
        def priority(self) -> int:
            return 100

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteSystem()  # type: ignore[abstract]

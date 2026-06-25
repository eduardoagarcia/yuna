"""Tests for system dependency graph."""

import pytest
from faker import Faker

from yuna.ecs.system import System
from yuna.ecs.world import ECSWorld
from yuna.exceptions import ValidationError
from yuna.loop.dependencies import (
    CyclicDependencyError,
    DependencyGraph,
)
from yuna.loop.scheduler import SystemScheduler

fake = Faker()


class MockSystem(System):
    """Mock system for testing."""

    def __init__(self, name: str, priority_value: int) -> None:
        self.name = name
        self._priority = priority_value

    @property
    def priority(self) -> int:
        return self._priority

    def update(self, world: ECSWorld, delta_time: float) -> None:
        pass

    def __repr__(self) -> str:
        return f"MockSystem({self.name})"


def test_dependency_graph_initialization() -> None:
    """Test dependency graph initializes empty."""
    graph = DependencyGraph()

    assert graph.node_count == 0
    assert graph.edge_count == 0


def test_add_node() -> None:
    """Test adding nodes to dependency graph."""
    graph = DependencyGraph()
    system = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system)

    assert graph.node_count == 1
    assert graph.edge_count == 0


def test_add_multiple_nodes() -> None:
    """Test adding multiple nodes to dependency graph."""
    graph = DependencyGraph()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system3 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system1)
    graph.add_node(system=system2)
    graph.add_node(system=system3)

    assert graph.node_count == 3


def test_add_edge() -> None:
    """Test adding dependencies between systems."""
    graph = DependencyGraph()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system1)
    graph.add_node(system=system2)
    graph.add_edge(from_system=system1, to_system=system2)

    assert graph.edge_count == 1


def test_add_edge_raises_if_from_system_not_in_graph() -> None:
    """Test adding edge raises error if from_system not in graph."""
    graph = DependencyGraph()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system2)

    with pytest.raises(ValidationError, match="not in dependency graph"):
        graph.add_edge(from_system=system1, to_system=system2)


def test_add_edge_raises_if_to_system_not_in_graph() -> None:
    """Test adding edge raises error if to_system not in graph."""
    graph = DependencyGraph()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system1)

    with pytest.raises(ValidationError, match="not in dependency graph"):
        graph.add_edge(from_system=system1, to_system=system2)


def test_topological_sort_no_dependencies() -> None:
    """Test topological sort with no dependencies uses priority order."""
    graph = DependencyGraph()
    system1 = MockSystem(name="high", priority_value=100)
    system2 = MockSystem(name="low", priority_value=50)
    system3 = MockSystem(name="medium", priority_value=75)

    graph.add_node(system=system1)
    graph.add_node(system=system2)
    graph.add_node(system=system3)

    ordered = graph.topological_sort()

    assert ordered == [system2, system3, system1]


def test_topological_sort_with_linear_dependencies() -> None:
    """Test topological sort with linear dependency chain."""
    graph = DependencyGraph()
    system1 = MockSystem(name="first", priority_value=100)
    system2 = MockSystem(name="second", priority_value=100)
    system3 = MockSystem(name="third", priority_value=100)

    graph.add_node(system=system1)
    graph.add_node(system=system2)
    graph.add_node(system=system3)

    graph.add_edge(from_system=system2, to_system=system1)
    graph.add_edge(from_system=system3, to_system=system2)

    ordered = graph.topological_sort()

    assert ordered == [system1, system2, system3]


def test_topological_sort_with_branching_dependencies() -> None:
    """Test topological sort with branching dependencies."""
    graph = DependencyGraph()
    system_a = MockSystem(name="a", priority_value=100)
    system_b = MockSystem(name="b", priority_value=100)
    system_c = MockSystem(name="c", priority_value=100)
    system_d = MockSystem(name="d", priority_value=100)

    graph.add_node(system=system_a)
    graph.add_node(system=system_b)
    graph.add_node(system=system_c)
    graph.add_node(system=system_d)

    graph.add_edge(from_system=system_b, to_system=system_a)
    graph.add_edge(from_system=system_c, to_system=system_a)
    graph.add_edge(from_system=system_d, to_system=system_b)
    graph.add_edge(from_system=system_d, to_system=system_c)

    ordered = graph.topological_sort()

    assert ordered[0] == system_a
    assert ordered[-1] == system_d
    assert ordered.index(system_b) < ordered.index(system_d)
    assert ordered.index(system_c) < ordered.index(system_d)


def test_topological_sort_respects_priority_for_same_level() -> None:
    """Test topological sort uses priority for systems at same dependency level."""
    graph = DependencyGraph()
    system_a = MockSystem(name="a", priority_value=100)
    system_b = MockSystem(name="b", priority_value=50)
    system_c = MockSystem(name="c", priority_value=75)
    system_d = MockSystem(name="d", priority_value=100)

    graph.add_node(system=system_a)
    graph.add_node(system=system_b)
    graph.add_node(system=system_c)
    graph.add_node(system=system_d)

    graph.add_edge(from_system=system_d, to_system=system_a)
    graph.add_edge(from_system=system_d, to_system=system_b)
    graph.add_edge(from_system=system_d, to_system=system_c)

    ordered = graph.topological_sort()

    assert ordered == [system_b, system_c, system_a, system_d]


def test_detect_cycles_simple() -> None:
    """Test cycle detection with simple circular dependency."""
    graph = DependencyGraph()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system1)
    graph.add_node(system=system2)
    graph.add_edge(from_system=system1, to_system=system2)
    graph.add_edge(from_system=system2, to_system=system1)

    cycles = graph.detect_cycles()

    assert len(cycles) > 0
    assert system1 in cycles[0]
    assert system2 in cycles[0]


def test_detect_cycles_complex() -> None:
    """Test cycle detection with complex circular dependency."""
    graph = DependencyGraph()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system3 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system1)
    graph.add_node(system=system2)
    graph.add_node(system=system3)
    graph.add_edge(from_system=system1, to_system=system2)
    graph.add_edge(from_system=system2, to_system=system3)
    graph.add_edge(from_system=system3, to_system=system1)

    cycles = graph.detect_cycles()

    assert len(cycles) > 0


def test_detect_cycles_no_cycles() -> None:
    """Test cycle detection returns empty when no cycles."""
    graph = DependencyGraph()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system1)
    graph.add_node(system=system2)
    graph.add_edge(from_system=system2, to_system=system1)

    cycles = graph.detect_cycles()

    assert len(cycles) == 0


def test_validate_returns_true_when_no_cycles() -> None:
    """Test validate returns True when graph has no cycles."""
    graph = DependencyGraph()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system1)
    graph.add_node(system=system2)
    graph.add_edge(from_system=system2, to_system=system1)

    assert graph.validate()


def test_validate_returns_false_when_cycles_exist() -> None:
    """Test validate returns False when graph has cycles."""
    graph = DependencyGraph()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system1)
    graph.add_node(system=system2)
    graph.add_edge(from_system=system1, to_system=system2)
    graph.add_edge(from_system=system2, to_system=system1)

    assert not graph.validate()


def test_topological_sort_raises_on_cycle() -> None:
    """Test topological sort raises error when cycle detected."""
    graph = DependencyGraph()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system1)
    graph.add_node(system=system2)
    graph.add_edge(from_system=system1, to_system=system2)
    graph.add_edge(from_system=system2, to_system=system1)

    with pytest.raises(CyclicDependencyError, match="Circular dependency"):
        graph.topological_sort()


def test_get_dependencies() -> None:
    """Test getting dependencies for a system."""
    graph = DependencyGraph()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system3 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system1)
    graph.add_node(system=system2)
    graph.add_node(system=system3)
    graph.add_edge(from_system=system3, to_system=system1)
    graph.add_edge(from_system=system3, to_system=system2)

    deps = graph.get_dependencies(system=system3)

    assert system1 in deps
    assert system2 in deps
    assert len(deps) == 2


def test_get_dependencies_raises_if_system_not_in_graph() -> None:
    """Test get_dependencies raises error if system not in graph."""
    graph = DependencyGraph()
    system = MockSystem(name=fake.word(), priority_value=fake.pyint())

    with pytest.raises(ValidationError, match="not in dependency graph"):
        graph.get_dependencies(system=system)


def test_get_dependents() -> None:
    """Test getting systems that depend on a system."""
    graph = DependencyGraph()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system3 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system1)
    graph.add_node(system=system2)
    graph.add_node(system=system3)
    graph.add_edge(from_system=system2, to_system=system1)
    graph.add_edge(from_system=system3, to_system=system1)

    dependents = graph.get_dependents(system=system1)

    assert system2 in dependents
    assert system3 in dependents
    assert len(dependents) == 2


def test_get_dependents_raises_if_system_not_in_graph() -> None:
    """Test get_dependents raises error if system not in graph."""
    graph = DependencyGraph()
    system = MockSystem(name=fake.word(), priority_value=fake.pyint())

    with pytest.raises(ValidationError, match="not in dependency graph"):
        graph.get_dependents(system=system)


def test_clear() -> None:
    """Test clearing dependency graph."""
    graph = DependencyGraph()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    graph.add_node(system=system1)
    graph.add_node(system=system2)
    graph.add_edge(from_system=system2, to_system=system1)

    assert graph.node_count == 2
    assert graph.edge_count == 1

    graph.clear()

    assert graph.node_count == 0
    assert graph.edge_count == 0


def test_scheduler_register_adds_to_dependency_graph() -> None:
    """Test scheduler register adds system to dependency graph."""
    scheduler = SystemScheduler()
    system = MockSystem(name=fake.word(), priority_value=fake.pyint())

    scheduler.register(system=system)

    assert scheduler.count == 1
    assert scheduler._dependency_graph.node_count == 1


def test_scheduler_add_dependency() -> None:
    """Test scheduler can add dependencies between systems."""
    scheduler = SystemScheduler()
    system1 = MockSystem(name=fake.word(), priority_value=100)
    system2 = MockSystem(name=fake.word(), priority_value=200)

    scheduler.register(system=system1)
    scheduler.register(system=system2)
    scheduler.add_dependency(system=system2, depends_on=system1)

    ordered = scheduler.get_ordered_systems()

    assert ordered == [system1, system2]


def test_scheduler_add_dependency_raises_if_system_not_registered() -> None:
    """Test add_dependency raises error if system not registered."""
    scheduler = SystemScheduler()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    scheduler.register(system=system1)

    with pytest.raises(ValidationError, match="not registered"):
        scheduler.add_dependency(system=system2, depends_on=system1)


def test_scheduler_add_dependency_raises_if_depends_on_not_registered() -> None:
    """Test add_dependency raises error if depends_on not registered."""
    scheduler = SystemScheduler()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    scheduler.register(system=system1)

    with pytest.raises(ValidationError, match="not registered"):
        scheduler.add_dependency(system=system1, depends_on=system2)


def test_scheduler_add_dependency_raises_on_cycle() -> None:
    """Test add_dependency raises error if creates circular dependency."""
    scheduler = SystemScheduler()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    scheduler.register(system=system1)
    scheduler.register(system=system2)
    scheduler.add_dependency(system=system2, depends_on=system1)

    with pytest.raises(CyclicDependencyError, match="Circular dependency"):
        scheduler.add_dependency(system=system1, depends_on=system2)


def test_scheduler_get_ordered_systems_priority_only() -> None:
    """Test get_ordered_systems uses priority when no dependencies."""
    scheduler = SystemScheduler()
    system1 = MockSystem(name="high", priority_value=200)
    system2 = MockSystem(name="low", priority_value=100)
    system3 = MockSystem(name="medium", priority_value=150)

    scheduler.register(system=system1)
    scheduler.register(system=system2)
    scheduler.register(system=system3)

    ordered = scheduler.get_ordered_systems()

    assert ordered == [system2, system3, system1]


def test_scheduler_get_ordered_systems_with_dependencies() -> None:
    """Test get_ordered_systems respects dependencies over priority."""
    scheduler = SystemScheduler()
    system1 = MockSystem(name="high", priority_value=200)
    system2 = MockSystem(name="low", priority_value=100)

    scheduler.register(system=system1)
    scheduler.register(system=system2)
    scheduler.add_dependency(system=system1, depends_on=system2)

    ordered = scheduler.get_ordered_systems()

    assert ordered == [system2, system1]


def test_scheduler_get_ordered_systems_mixed_priority_and_dependencies() -> None:
    """Test get_ordered_systems with mixed priority and dependencies."""
    scheduler = SystemScheduler()
    system_a = MockSystem(name="a", priority_value=100)
    system_b = MockSystem(name="b", priority_value=200)
    system_c = MockSystem(name="c", priority_value=150)
    system_d = MockSystem(name="d", priority_value=50)

    scheduler.register(system=system_a)
    scheduler.register(system=system_b)
    scheduler.register(system=system_c)
    scheduler.register(system=system_d)

    scheduler.add_dependency(system=system_b, depends_on=system_a)

    ordered = scheduler.get_ordered_systems()

    assert ordered.index(system_a) < ordered.index(system_b)
    assert ordered[0] == system_d


def test_scheduler_clear_removes_systems_and_dependencies() -> None:
    """Test clear removes all systems and dependencies."""
    scheduler = SystemScheduler()
    system1 = MockSystem(name=fake.word(), priority_value=fake.pyint())
    system2 = MockSystem(name=fake.word(), priority_value=fake.pyint())

    scheduler.register(system=system1)
    scheduler.register(system=system2)
    scheduler.add_dependency(system=system2, depends_on=system1)

    assert scheduler.count == 2
    assert scheduler._dependency_graph.edge_count == 1

    scheduler.clear()

    assert scheduler.count == 0
    assert scheduler._dependency_graph.node_count == 0
    assert scheduler._dependency_graph.edge_count == 0

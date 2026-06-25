"""Tests for behavior tree component."""

from unittest.mock import Mock

from yuna.ai.behavior_tree.component import BehaviorTreeComponent


def test_behavior_tree_component_creation() -> None:
    """Test creating BehaviorTreeComponent with defaults."""
    component = BehaviorTreeComponent()

    assert component.root is None
    assert component.tick_interval == 1
    assert component.enabled is True
    assert component._ticks_since_update == 0


def test_behavior_tree_component_with_root() -> None:
    """Test creating BehaviorTreeComponent with root node."""
    mock_root = Mock()
    component = BehaviorTreeComponent(root=mock_root)

    assert component.root == mock_root


def test_behavior_tree_component_with_custom_tick_interval() -> None:
    """Test creating BehaviorTreeComponent with custom tick interval."""
    component = BehaviorTreeComponent(tick_interval=5)

    assert component.tick_interval == 5


def test_should_tick_returns_false_when_disabled() -> None:
    """Test should_tick returns False when component is disabled."""
    mock_root = Mock()
    component = BehaviorTreeComponent(root=mock_root, enabled=False)

    should_tick = component.should_tick()

    assert should_tick is False


def test_should_tick_returns_false_when_no_root() -> None:
    """Test should_tick returns False when root is None."""
    component = BehaviorTreeComponent(root=None, enabled=True)

    should_tick = component.should_tick()

    assert should_tick is False


def test_should_tick_returns_true_on_first_tick() -> None:
    """Test should_tick returns True on first tick."""
    mock_root = Mock()
    component = BehaviorTreeComponent(root=mock_root, tick_interval=1)

    should_tick = component.should_tick()

    assert should_tick is True


def test_should_tick_respects_tick_interval() -> None:
    """Test should_tick respects tick interval."""
    mock_root = Mock()
    component = BehaviorTreeComponent(root=mock_root, tick_interval=3)

    should_tick_1 = component.should_tick()
    should_tick_2 = component.should_tick()
    should_tick_3 = component.should_tick()
    should_tick_4 = component.should_tick()

    assert should_tick_1 is False
    assert should_tick_2 is False
    assert should_tick_3 is True
    assert should_tick_4 is False


def test_should_tick_resets_counter_after_tick() -> None:
    """Test should_tick resets counter after ticking."""
    mock_root = Mock()
    component = BehaviorTreeComponent(root=mock_root, tick_interval=2)

    component.should_tick()
    should_tick_2 = component.should_tick()
    component.should_tick()
    should_tick_4 = component.should_tick()

    assert should_tick_2 is True
    assert should_tick_4 is True


def test_should_tick_with_interval_of_one() -> None:
    """Test should_tick with interval of 1 ticks every frame."""
    mock_root = Mock()
    component = BehaviorTreeComponent(root=mock_root, tick_interval=1)

    should_tick_1 = component.should_tick()
    should_tick_2 = component.should_tick()
    should_tick_3 = component.should_tick()

    assert should_tick_1 is True
    assert should_tick_2 is True
    assert should_tick_3 is True


def test_disabling_component_stops_ticking() -> None:
    """Test disabling component stops ticking."""
    mock_root = Mock()
    component = BehaviorTreeComponent(root=mock_root, tick_interval=1)

    component.should_tick()
    component.enabled = False
    should_tick_2 = component.should_tick()

    assert should_tick_2 is False


def test_enabling_component_resumes_ticking() -> None:
    """Test enabling component resumes ticking."""
    mock_root = Mock()
    component = BehaviorTreeComponent(root=mock_root, tick_interval=1, enabled=False)

    component.should_tick()
    component.enabled = True
    should_tick_2 = component.should_tick()

    assert should_tick_2 is True

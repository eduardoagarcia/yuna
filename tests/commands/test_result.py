"""Tests for command result."""

from faker import Faker

from yuna.commands.result import CommandResult

fake = Faker()


def test_command_result_creation() -> None:
    """Test CommandResult can be instantiated."""
    result = CommandResult(success=True)
    assert result is not None


def test_command_result_success() -> None:
    """Test CommandResult with success status."""
    result = CommandResult(success=True)
    assert result.success is True


def test_command_result_failure() -> None:
    """Test CommandResult with failure status."""
    result = CommandResult(success=False)
    assert result.success is False


def test_command_result_with_reason() -> None:
    """Test CommandResult with failure reason."""
    reason = "Invalid position"
    result = CommandResult(success=False, reason=reason)
    assert result.reason == reason


def test_command_result_success_with_none_reason() -> None:
    """Test successful CommandResult has None reason by default."""
    result = CommandResult(success=True)
    assert result.reason is None


def test_command_result_with_data() -> None:
    """Test CommandResult with execution data."""
    data = {"entity_id": "abc123", "position": {"x": 10, "y": 20}}
    result = CommandResult(success=True, data=data)
    assert result.data == data


def test_command_result_empty_data_by_default() -> None:
    """Test CommandResult has empty dict for data by default."""
    result = CommandResult(success=True)
    assert result.data == {}


def test_command_result_is_immutable() -> None:
    """Test CommandResult is frozen and immutable."""
    result = CommandResult(success=True)
    try:
        result.success = False  # type: ignore[misc]
        msg = "Should not be able to modify frozen dataclass"
        raise AssertionError(msg)
    except AttributeError:
        pass


def test_command_result_with_all_fields() -> None:
    """Test CommandResult with all fields populated."""
    reason = "Out of range"
    data = {"attempted_position": {"x": 100, "y": 100}}
    result = CommandResult(success=False, reason=reason, data=data)
    assert result.success is False
    assert result.reason == reason
    assert result.data == data


def test_command_result_data_can_be_empty_dict() -> None:
    """Test CommandResult can have explicit empty dict."""
    result = CommandResult(success=True, data={})
    assert result.data == {}


def test_command_result_equality() -> None:
    """Test CommandResult equality comparison."""
    result_1 = CommandResult(success=True, reason=None, data={"key": "value"})
    result_2 = CommandResult(success=True, reason=None, data={"key": "value"})
    assert result_1 == result_2


def test_command_result_inequality() -> None:
    """Test CommandResult inequality comparison."""
    result_1 = CommandResult(success=True)
    result_2 = CommandResult(success=False)
    assert result_1 != result_2


def test_command_result_different_data_not_equal() -> None:
    """Test CommandResults with different data are not equal."""
    result_1 = CommandResult(success=True, data={"a": 1})
    result_2 = CommandResult(success=True, data={"b": 2})
    assert result_1 != result_2


def test_command_result_different_reason_not_equal() -> None:
    """Test CommandResults with different reasons are not equal."""
    result_1 = CommandResult(success=False, reason="Error 1")
    result_2 = CommandResult(success=False, reason="Error 2")
    assert result_1 != result_2


def test_command_result_with_complex_data() -> None:
    """Test CommandResult with nested complex data structures."""
    data = {
        "entities": ["abc", "def", "ghi"],
        "positions": [{"x": 1, "y": 2}, {"x": 3, "y": 4}],
        "metadata": {"timestamp": 123456789, "tick": 100},
    }
    result = CommandResult(success=True, data=data)
    assert result.data == data
    assert result.data["entities"] == ["abc", "def", "ghi"]


def test_command_result_reason_can_be_none_for_failure() -> None:
    """Test CommandResult failure can have None reason."""
    result = CommandResult(success=False, reason=None)
    assert result.success is False
    assert result.reason is None


def test_command_result_success_with_reason() -> None:
    """Test successful CommandResult can have a reason (e.g., warning)."""
    result = CommandResult(success=True, reason="Completed with warnings")
    assert result.success is True
    assert result.reason == "Completed with warnings"

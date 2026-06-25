"""Tests for command base class."""

import pytest
from faker import Faker

from yuna.commands.command import Command
from yuna.commands.permissions import ActionPermission
from yuna.commands.result import CommandResult

fake = Faker()


class TestContext:
    """Test context for command execution."""

    def __init__(self) -> None:
        self.value = 0
        self.executed = False


class ConcreteCommand(Command[TestContext, CommandResult]):
    """Test command implementation."""

    def __init__(
        self,
        priority_value: int = 100,
        permission_value: ActionPermission | None = None,
        can_execute_result: tuple[bool, str] = (True, ""),
    ) -> None:
        self._priority = priority_value
        self._permission = permission_value or ActionPermission()
        self._can_execute_result = can_execute_result
        self.execute_called = False
        self.undo_called = False

    @property
    def priority(self) -> int:
        return self._priority

    def permission(self, context: TestContext) -> ActionPermission:
        return self._permission

    def can_execute(self, context: TestContext) -> tuple[bool, str]:
        return self._can_execute_result

    def execute(self, context: TestContext) -> CommandResult:
        self.execute_called = True
        context.executed = True
        context.value += 10
        return CommandResult(success=True, data={"value": context.value})

    def undo(self, context: TestContext, result: CommandResult) -> None:
        self.undo_called = True
        context.value -= 10


class AnotherCommand(Command[TestContext, CommandResult]):
    """Another test command implementation."""

    @property
    def priority(self) -> int:
        return 200

    def permission(self, context: TestContext) -> ActionPermission:
        return ActionPermission(cooldown_ticks=5)

    def can_execute(self, context: TestContext) -> tuple[bool, str]:
        return True, ""

    def execute(self, context: TestContext) -> CommandResult:
        return CommandResult(success=True)


def test_command_is_abstract() -> None:
    """Test Command ABC cannot be instantiated."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        Command()  # type: ignore[abstract]


def test_concrete_command_can_be_created() -> None:
    """Test concrete command implementing all methods can be created."""
    command = ConcreteCommand()
    assert command is not None
    assert isinstance(command, Command)


def test_command_has_priority() -> None:
    """Test command has priority property."""
    command = ConcreteCommand(priority_value=50)
    assert command.priority == 50


def test_command_has_permission() -> None:
    """Test command has permission method."""
    permission_value = ActionPermission(cooldown_ticks=10)
    command = ConcreteCommand(permission_value=permission_value)
    context = TestContext()
    permission = command.permission(context=context)
    assert permission.cooldown_ticks == 10


def test_command_can_execute() -> None:
    """Test command can_execute validates execution."""
    command = ConcreteCommand(can_execute_result=(True, ""))
    context = TestContext()
    can_execute, reason = command.can_execute(context=context)
    assert can_execute is True
    assert not reason


def test_command_cannot_execute() -> None:
    """Test command can_execute returns failure."""
    command = ConcreteCommand(can_execute_result=(False, "Invalid state"))
    context = TestContext()
    can_execute, reason = command.can_execute(context=context)
    assert can_execute is False
    assert reason == "Invalid state"


def test_command_execute() -> None:
    """Test command execute modifies context."""
    command = ConcreteCommand()
    context = TestContext()
    result = command.execute(context=context)
    assert result.success is True
    assert context.executed is True


def test_command_execute_returns_result() -> None:
    """Test command execute returns result."""
    command = ConcreteCommand()
    context = TestContext()
    result = command.execute(context=context)
    assert isinstance(result, CommandResult)
    assert result.data["value"] == 10


def test_command_undo() -> None:
    """Test command undo reverses execution."""
    command = ConcreteCommand()
    context = TestContext()
    result = command.execute(context=context)
    assert context.value == 10
    command.undo(context=context, result=result)
    assert context.value == 0
    assert command.undo_called is True


def test_different_commands_have_different_priorities() -> None:
    """Test different command types have different priorities."""
    command_1 = ConcreteCommand(priority_value=100)
    command_2 = AnotherCommand()
    assert command_1.priority != command_2.priority


def test_different_commands_have_different_permissions() -> None:
    """Test different command types have different permissions."""
    command_1 = ConcreteCommand()
    command_2 = AnotherCommand()
    context = TestContext()
    permission_1 = command_1.permission(context=context)
    permission_2 = command_2.permission(context=context)
    assert permission_1.cooldown_ticks != permission_2.cooldown_ticks


def test_command_priority_can_be_zero() -> None:
    """Test command priority can be zero."""
    command = ConcreteCommand(priority_value=0)
    assert command.priority == 0


def test_command_priority_can_be_negative() -> None:
    """Test command priority can be negative."""
    command = ConcreteCommand(priority_value=-100)
    assert command.priority == -100


def test_command_permission_can_have_no_effects() -> None:
    """Test command permission can have no resource effects."""
    command = ConcreteCommand()
    context = TestContext()
    permission = command.permission(context=context)
    assert permission.resource_effects == ()


def test_command_permission_can_have_required_stats() -> None:
    """Test command permission can have required stats."""
    permission_value = ActionPermission(required_stats={"strength": 10.5})
    command = ConcreteCommand(permission_value=permission_value)
    context = TestContext()
    permission = command.permission(context=context)
    assert permission.required_stats == {"strength": 10.5}


def test_command_sorting_by_priority() -> None:
    """Test commands can be sorted by priority."""
    command_1 = ConcreteCommand(priority_value=300)
    command_2 = ConcreteCommand(priority_value=100)
    command_3 = ConcreteCommand(priority_value=200)
    commands = [command_1, command_2, command_3]
    sorted_commands = sorted(commands, key=lambda c: c.priority)
    assert sorted_commands[0].priority == 100
    assert sorted_commands[1].priority == 200
    assert sorted_commands[2].priority == 300


def test_incomplete_command_without_priority_raises_error() -> None:
    """Test command without priority implementation cannot be instantiated."""

    class IncompleteCommand(Command[TestContext, CommandResult]):
        def permission(self, context: TestContext) -> ActionPermission:
            return ActionPermission()

        def can_execute(self, context: TestContext) -> tuple[bool, str]:
            return True, ""

        def execute(self, context: TestContext) -> CommandResult:
            return CommandResult(success=True)

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteCommand()  # type: ignore[abstract]


def test_incomplete_command_without_permission_raises_error() -> None:
    """Test command without permission implementation cannot be instantiated."""

    class IncompleteCommand(Command[TestContext, CommandResult]):
        @property
        def priority(self) -> int:
            return 100

        def can_execute(self, context: TestContext) -> tuple[bool, str]:
            return True, ""

        def execute(self, context: TestContext) -> CommandResult:
            return CommandResult(success=True)

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteCommand()  # type: ignore[abstract]


def test_incomplete_command_without_can_execute_raises_error() -> None:
    """Test command without can_execute implementation cannot be instantiated."""

    class IncompleteCommand(Command[TestContext, CommandResult]):
        @property
        def priority(self) -> int:
            return 100

        def permission(self, context: TestContext) -> ActionPermission:
            return ActionPermission()

        def execute(self, context: TestContext) -> CommandResult:
            return CommandResult(success=True)

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteCommand()  # type: ignore[abstract]


def test_incomplete_command_without_execute_raises_error() -> None:
    """Test command without execute implementation cannot be instantiated."""

    class IncompleteCommand(Command[TestContext, CommandResult]):
        @property
        def priority(self) -> int:
            return 100

        def permission(self, context: TestContext) -> ActionPermission:
            return ActionPermission()

        def can_execute(self, context: TestContext) -> tuple[bool, str]:
            return True, ""

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteCommand()  # type: ignore[abstract]


def test_command_undo_is_optional() -> None:
    """Test command can be created without overriding undo."""

    class CommandWithoutUndo(Command[TestContext, CommandResult]):
        @property
        def priority(self) -> int:
            return 100

        def permission(self, context: TestContext) -> ActionPermission:
            return ActionPermission()

        def can_execute(self, context: TestContext) -> tuple[bool, str]:
            return True, ""

        def execute(self, context: TestContext) -> CommandResult:
            return CommandResult(success=True)

    command = CommandWithoutUndo()
    context = TestContext()
    result = command.execute(context=context)
    command.undo(context=context, result=result)


def test_command_execute_multiple_times() -> None:
    """Test command can be executed multiple times."""
    command = ConcreteCommand()
    context = TestContext()
    command.execute(context=context)
    command.execute(context=context)
    command.execute(context=context)
    assert context.value == 30


def test_multiple_commands_on_same_context() -> None:
    """Test multiple commands can operate on same context."""
    command_1 = ConcreteCommand()
    command_2 = ConcreteCommand()
    context = TestContext()
    command_1.execute(context=context)
    command_2.execute(context=context)
    assert context.value == 20


def test_command_with_different_generic_types() -> None:
    """Test command can use different generic types."""

    class StringCommand(Command[str, int]):
        @property
        def priority(self) -> int:
            return 100

        def permission(self, context: str) -> ActionPermission:
            return ActionPermission()

        def can_execute(self, context: str) -> tuple[bool, str]:
            return len(context) > 0, ""

        def execute(self, context: str) -> int:
            return len(context)

    command = StringCommand()
    result = command.execute(context="hello")
    assert result == 5

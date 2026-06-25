"""Tests for macro command."""

from faker import Faker

from yuna.commands.command import Command
from yuna.commands.macro import MacroCommand
from yuna.commands.permissions import ActionPermission
from yuna.commands.result import CommandResult

fake = Faker()


class TestContext:
    """Test context for command execution."""

    def __init__(self) -> None:
        self.value = 0
        self.operations: list[str] = []


class IncrementCommand(Command[TestContext, CommandResult]):
    """Test command that increments value."""

    def __init__(self, amount: int = 1) -> None:
        self.amount = amount

    @property
    def priority(self) -> int:
        return 100

    def permission(self, context: TestContext) -> ActionPermission:
        return ActionPermission()

    def can_execute(self, context: TestContext) -> tuple[bool, str]:
        return True, ""

    def execute(self, context: TestContext) -> CommandResult:
        context.value += self.amount
        context.operations.append(f"add_{self.amount}")
        return CommandResult(success=True, data={"amount": self.amount})

    def undo(self, context: TestContext, result: CommandResult) -> None:
        context.value -= self.amount
        context.operations.append(f"undo_add_{self.amount}")


class FailingValidationCommand(Command[TestContext, CommandResult]):
    """Test command that fails validation."""

    @property
    def priority(self) -> int:
        return 100

    def permission(self, context: TestContext) -> ActionPermission:
        return ActionPermission()

    def can_execute(self, context: TestContext) -> tuple[bool, str]:
        return False, "Validation failed"

    def execute(self, context: TestContext) -> CommandResult:
        return CommandResult(success=False)


class FailingExecutionCommand(Command[TestContext, CommandResult]):
    """Test command that passes validation but fails execution."""

    @property
    def priority(self) -> int:
        return 100

    def permission(self, context: TestContext) -> ActionPermission:
        return ActionPermission()

    def can_execute(self, context: TestContext) -> tuple[bool, str]:
        return True, ""

    def execute(self, context: TestContext) -> CommandResult:
        return CommandResult(success=False, reason="Execution failed")


def test_macro_command_creation() -> None:
    """Test MacroCommand can be instantiated."""
    commands = [IncrementCommand(amount=1)]
    macro = MacroCommand[TestContext](commands=commands)
    assert macro is not None


def test_macro_command_has_priority() -> None:
    """Test MacroCommand has priority."""
    commands = [IncrementCommand()]
    macro = MacroCommand[TestContext](commands=commands, priority_value=50)
    assert macro.priority == 50


def test_macro_command_permission_aggregates() -> None:
    """Test MacroCommand permission aggregates sub-command permissions."""
    commands = [
        IncrementCommand(amount=1),
        IncrementCommand(amount=2),
        IncrementCommand(amount=3),
    ]
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    assert macro.permission(context=context) is not None


def test_macro_command_custom_permission() -> None:
    """Test MacroCommand with custom permission override."""
    commands = [IncrementCommand(amount=1)]
    custom_permission = ActionPermission(cooldown_ticks=10)
    macro = MacroCommand[TestContext](
        commands=commands, permission_override=custom_permission
    )
    context = TestContext()
    assert macro.permission(context=context).cooldown_ticks == 10


def test_macro_command_get_commands() -> None:
    """Test getting list of sub-commands."""
    commands = [IncrementCommand(amount=1), IncrementCommand(amount=2)]
    macro = MacroCommand[TestContext](commands=commands)
    retrieved = macro.commands
    assert len(retrieved) == 2


def test_macro_command_commands_returns_copy() -> None:
    """Test commands property returns copy of list."""
    commands = [IncrementCommand(amount=1)]
    macro = MacroCommand[TestContext](commands=commands)
    retrieved = macro.commands
    retrieved.append(IncrementCommand(amount=2))
    assert len(macro.commands) == 1


def test_macro_command_can_execute_all_valid() -> None:
    """Test can_execute when all sub-commands are valid."""
    commands = [IncrementCommand(amount=1), IncrementCommand(amount=2)]
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    can_execute, reason = macro.can_execute(context=context)
    assert can_execute is True
    assert not reason


def test_macro_command_can_execute_with_failing_command() -> None:
    """Test can_execute fails when sub-command fails validation."""
    commands = [IncrementCommand(amount=1), FailingValidationCommand()]
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    can_execute, reason = macro.can_execute(context=context)
    assert can_execute is False
    assert "Command 1 failed" in reason


def test_macro_command_execute() -> None:
    """Test executing macro command."""
    commands = [IncrementCommand(amount=5), IncrementCommand(amount=10)]
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    result = macro.execute(context=context)
    assert result.success is True
    assert context.value == 15


def test_macro_command_execute_collects_results() -> None:
    """Test macro command collects sub-command results."""
    commands = [IncrementCommand(amount=1), IncrementCommand(amount=2)]
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    result = macro.execute(context=context)
    assert "sub_results" in result.data
    assert len(result.data["sub_results"]) == 2


def test_macro_command_execute_order() -> None:
    """Test commands execute in order."""
    commands = [
        IncrementCommand(amount=1),
        IncrementCommand(amount=2),
        IncrementCommand(amount=3),
    ]
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    macro.execute(context=context)
    assert context.operations == ["add_1", "add_2", "add_3"]


def test_macro_command_execute_with_failing_subcommand() -> None:
    """Test macro execution when sub-command fails."""
    commands = [IncrementCommand(amount=1), FailingExecutionCommand()]
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    result = macro.execute(context=context)
    assert result.success is False


def test_macro_command_undo() -> None:
    """Test undoing macro command."""
    commands = [IncrementCommand(amount=5), IncrementCommand(amount=10)]
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    macro.execute(context=context)
    assert context.value == 15
    macro.undo(context=context)
    assert context.value == 0


def test_macro_command_undo_reverse_order() -> None:
    """Test undo executes in reverse order."""
    commands = [
        IncrementCommand(amount=1),
        IncrementCommand(amount=2),
        IncrementCommand(amount=3),
    ]
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    macro.execute(context=context)
    macro.undo(context=context)
    undo_ops = [op for op in context.operations if op.startswith("undo")]
    assert undo_ops == ["undo_add_3", "undo_add_2", "undo_add_1"]


def test_macro_command_with_single_command() -> None:
    """Test macro command with single sub-command."""
    commands = [IncrementCommand(amount=5)]
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    result = macro.execute(context=context)
    assert result.success is True
    assert context.value == 5


def test_macro_command_with_empty_commands() -> None:
    """Test macro command with empty command list."""
    commands: list[Command[TestContext, CommandResult]] = []
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    can_execute, _reason = macro.can_execute(context=context)
    assert can_execute is True


def test_macro_command_execute_empty_commands() -> None:
    """Test executing macro with no sub-commands."""
    commands: list[Command[TestContext, CommandResult]] = []
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    result = macro.execute(context=context)
    assert result.success is True
    assert result.data["sub_results"] == []


def test_macro_command_permission_empty_for_empty_commands() -> None:
    """Test macro permission is empty when no sub-commands."""
    commands: list[Command[TestContext, CommandResult]] = []
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    assert macro.permission(context=context).resource_effects == ()


def test_macro_command_multiple_executions() -> None:
    """Test executing macro command multiple times."""
    commands = [IncrementCommand(amount=1)]
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    macro.execute(context=context)
    macro.execute(context=context)
    macro.execute(context=context)
    assert context.value == 3


def test_macro_command_undo_without_execute() -> None:
    """Test undo without prior execute completes without error."""
    commands = [IncrementCommand(amount=1)]
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    CommandResult(success=True)
    macro.undo(context=context)


def test_macro_command_complex_scenario() -> None:
    """Test complex scenario with multiple commands."""
    commands = [
        IncrementCommand(amount=10),
        IncrementCommand(amount=20),
        IncrementCommand(amount=30),
    ]
    macro = MacroCommand[TestContext](commands=commands, priority_value=50)
    context = TestContext()
    can_execute, _reason = macro.can_execute(context=context)
    assert can_execute is True
    result = macro.execute(context=context)
    assert result.success is True
    assert context.value == 60
    assert macro.permission(context=context) is not None
    macro.undo(context=context)
    assert context.value == 0


def test_macro_command_default_priority() -> None:
    """Test macro command has default priority of 100."""
    commands = [IncrementCommand(amount=1)]
    macro = MacroCommand[TestContext](commands=commands)
    assert macro.priority == 100


def test_macro_command_aggregates_overlapping_stats() -> None:
    """Test macro aggregates overlapping stat requirements taking max values."""

    class CommandWithStats1(Command[TestContext, CommandResult]):
        @property
        def priority(self) -> int:
            return 100

        def permission(self, context: TestContext) -> ActionPermission:
            return ActionPermission(required_stats={"strength": 10.0, "agility": 5.0})

        def can_execute(self, context: TestContext) -> tuple[bool, str]:
            return True, ""

        def execute(self, context: TestContext) -> CommandResult:
            return CommandResult(success=True)

    class CommandWithStats2(Command[TestContext, CommandResult]):
        @property
        def priority(self) -> int:
            return 100

        def permission(self, context: TestContext) -> ActionPermission:
            return ActionPermission(
                required_stats={"strength": 15.0, "intelligence": 8.0}
            )

        def can_execute(self, context: TestContext) -> tuple[bool, str]:
            return True, ""

        def execute(self, context: TestContext) -> CommandResult:
            return CommandResult(success=True)

    commands = [CommandWithStats1(), CommandWithStats2()]
    macro = MacroCommand[TestContext](commands=commands)
    context = TestContext()
    perm = macro.permission(context=context)
    assert perm.required_stats["strength"] == 15.0
    assert perm.required_stats["agility"] == 5.0
    assert perm.required_stats["intelligence"] == 8.0

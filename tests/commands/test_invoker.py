"""Tests for command invoker."""

from faker import Faker

from yuna.commands.command import Command
from yuna.commands.invoker import CommandInvoker
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


class FailingCommand(Command[TestContext, CommandResult]):
    """Test command that always fails validation."""

    @property
    def priority(self) -> int:
        return 100

    def permission(self, context: TestContext) -> ActionPermission:
        return ActionPermission()

    def can_execute(self, context: TestContext) -> tuple[bool, str]:
        return False, "Always fails"

    def execute(self, context: TestContext) -> CommandResult:
        return CommandResult(success=False)


def test_command_invoker_creation() -> None:
    """Test CommandInvoker can be instantiated."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    assert invoker is not None


def test_execute_command() -> None:
    """Test executing a command."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = IncrementCommand(amount=5)
    success, result, reason = invoker.execute(command=command, context=context)
    assert success is True
    assert context.value == 5
    assert not reason


def test_execute_command_returns_result() -> None:
    """Test execute returns command result."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = IncrementCommand(amount=10)
    success, result, _reason = invoker.execute(command=command, context=context)
    assert isinstance(result, CommandResult)
    assert result.data["amount"] == 10


def test_execute_command_adds_to_history() -> None:
    """Test executing command adds to history."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = IncrementCommand()
    invoker.execute(command=command, context=context)
    assert invoker.get_history_count() == 1


def test_execute_failing_command() -> None:
    """Test executing command that fails validation."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = FailingCommand()
    success, result, reason = invoker.execute(command=command, context=context)
    assert success is False
    assert result is None
    assert reason == "Always fails"


def test_execute_failing_command_not_added_to_history() -> None:
    """Test failed command not added to history."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = FailingCommand()
    invoker.execute(command=command, context=context)
    assert invoker.get_history_count() == 0


def test_undo_command() -> None:
    """Test undoing a command."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = IncrementCommand(amount=5)
    invoker.execute(command=command, context=context)
    assert context.value == 5
    success = invoker.undo(context=context)
    assert success is True
    assert context.value == 0


def test_undo_removes_from_history() -> None:
    """Test undo removes command from history."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = IncrementCommand()
    invoker.execute(command=command, context=context)
    invoker.undo(context=context)
    assert invoker.get_history_count() == 0


def test_undo_adds_to_redo_stack() -> None:
    """Test undo adds command to redo stack."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = IncrementCommand()
    invoker.execute(command=command, context=context)
    invoker.undo(context=context)
    assert invoker.get_redo_count() == 1


def test_undo_with_empty_history() -> None:
    """Test undo with no commands in history."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    success = invoker.undo(context=context)
    assert success is False


def test_redo_command() -> None:
    """Test redoing a command."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = IncrementCommand(amount=5)
    invoker.execute(command=command, context=context)
    invoker.undo(context=context)
    assert context.value == 0
    success = invoker.redo(context=context)
    assert success is True
    assert context.value == 5


def test_redo_adds_to_history() -> None:
    """Test redo adds command back to history."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = IncrementCommand()
    invoker.execute(command=command, context=context)
    invoker.undo(context=context)
    invoker.redo(context=context)
    assert invoker.get_history_count() == 1


def test_redo_removes_from_redo_stack() -> None:
    """Test redo removes command from redo stack."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = IncrementCommand()
    invoker.execute(command=command, context=context)
    invoker.undo(context=context)
    invoker.redo(context=context)
    assert invoker.get_redo_count() == 0


def test_redo_with_empty_stack() -> None:
    """Test redo with no commands in redo stack."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    success = invoker.redo(context=context)
    assert success is False


def test_execute_clears_redo_stack() -> None:
    """Test executing new command clears redo stack."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command_1 = IncrementCommand(amount=5)
    command_2 = IncrementCommand(amount=10)
    invoker.execute(command=command_1, context=context)
    invoker.undo(context=context)
    assert invoker.get_redo_count() == 1
    invoker.execute(command=command_2, context=context)
    assert invoker.get_redo_count() == 0


def test_can_undo() -> None:
    """Test can_undo returns correct status."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    assert invoker.can_undo() is False
    command = IncrementCommand()
    invoker.execute(command=command, context=context)
    assert invoker.can_undo() is True


def test_can_redo() -> None:
    """Test can_redo returns correct status."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    assert invoker.can_redo() is False
    command = IncrementCommand()
    invoker.execute(command=command, context=context)
    invoker.undo(context=context)
    assert invoker.can_redo() is True


def test_clear_history() -> None:
    """Test clearing command history."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = IncrementCommand()
    invoker.execute(command=command, context=context)
    invoker.clear_history()
    assert invoker.get_history_count() == 0


def test_clear_history_clears_redo_stack() -> None:
    """Test clear_history also clears redo stack."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = IncrementCommand()
    invoker.execute(command=command, context=context)
    invoker.undo(context=context)
    invoker.clear_history()
    assert invoker.get_redo_count() == 0


def test_multiple_undo_redo() -> None:
    """Test multiple undo/redo operations."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command_1 = IncrementCommand(amount=5)
    command_2 = IncrementCommand(amount=10)
    command_3 = IncrementCommand(amount=15)
    invoker.execute(command=command_1, context=context)
    invoker.execute(command=command_2, context=context)
    invoker.execute(command=command_3, context=context)
    assert context.value == 30
    invoker.undo(context=context)
    assert context.value == 15
    invoker.undo(context=context)
    assert context.value == 5
    invoker.redo(context=context)
    assert context.value == 15
    invoker.redo(context=context)
    assert context.value == 30


def test_history_count() -> None:
    """Test get_history_count returns correct count."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    assert invoker.get_history_count() == 0
    invoker.execute(command=IncrementCommand(), context=context)
    assert invoker.get_history_count() == 1
    invoker.execute(command=IncrementCommand(), context=context)
    assert invoker.get_history_count() == 2


def test_redo_count() -> None:
    """Test get_redo_count returns correct count."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    assert invoker.get_redo_count() == 0
    invoker.execute(command=IncrementCommand(), context=context)
    invoker.undo(context=context)
    assert invoker.get_redo_count() == 1
    invoker.execute(command=IncrementCommand(), context=context)
    invoker.undo(context=context)
    assert invoker.get_redo_count() == 1


def test_undo_redo_preserves_operations() -> None:
    """Test undo/redo executes operations correctly."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    command = IncrementCommand(amount=5)
    invoker.execute(command=command, context=context)
    invoker.undo(context=context)
    invoker.redo(context=context)
    assert "add_5" in context.operations
    assert "undo_add_5" in context.operations


def test_execute_multiple_different_commands() -> None:
    """Test executing multiple different commands."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    invoker.execute(command=IncrementCommand(amount=1), context=context)
    invoker.execute(command=IncrementCommand(amount=2), context=context)
    invoker.execute(command=IncrementCommand(amount=3), context=context)
    assert context.value == 6
    assert invoker.get_history_count() == 3


def test_undo_all_commands() -> None:
    """Test undoing all commands returns to initial state."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    invoker.execute(command=IncrementCommand(amount=5), context=context)
    invoker.execute(command=IncrementCommand(amount=10), context=context)
    invoker.execute(command=IncrementCommand(amount=15), context=context)
    invoker.undo(context=context)
    invoker.undo(context=context)
    invoker.undo(context=context)
    assert context.value == 0
    assert invoker.get_history_count() == 0


def test_redo_all_commands() -> None:
    """Test redoing all commands restores final state."""
    invoker = CommandInvoker[TestContext, CommandResult]()
    context = TestContext()
    invoker.execute(command=IncrementCommand(amount=5), context=context)
    invoker.execute(command=IncrementCommand(amount=10), context=context)
    invoker.undo(context=context)
    invoker.undo(context=context)
    invoker.redo(context=context)
    invoker.redo(context=context)
    assert context.value == 15
    assert invoker.get_redo_count() == 0

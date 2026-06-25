"""Command invoker with undo/redo support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yuna.commands.command import Command


class CommandInvoker[TContext, TResult]:
    """Command invoker with history and undo/redo support.

    Responsibilities:
    - Execute commands with validation
    - Track command history
    - Support undo/redo operations
    - Clear redo stack on new command

    Usage:
        invoker = CommandInvoker[GameWorld, CommandResult]()

        success, result, reason = invoker.execute(
            command=move_command,
            context=world,
        )

        if success:
            print(f"Executed: {result}")

        if invoker.can_undo():
            invoker.undo(context=world)

        if invoker.can_redo():
            invoker.redo(context=world)
    """

    def __init__(self) -> None:
        self._history: list[tuple[Command[TContext, TResult], TResult]] = []
        self._redo_stack: list[tuple[Command[TContext, TResult], TResult]] = []

    def execute(
        self,
        command: Command[TContext, TResult],
        context: TContext,
    ) -> tuple[bool, Any, str]:
        """Execute command with validation.

        Args:
            command: Command to execute
            context: Execution context

        Returns:
            Tuple of (success, result, reason)
        """
        can_execute, reason = command.can_execute(context=context)
        if not can_execute:
            return False, None, reason

        result = command.execute(context=context)
        self._history.append((command, result))
        self._redo_stack.clear()

        return True, result, ""

    def undo(self, context: TContext) -> bool:
        """Undo last executed command.

        Args:
            context: Execution context

        Returns:
            True if undo succeeded, False if no history
        """
        if not self._history:
            return False

        command, result = self._history.pop()
        command.undo(context=context, result=result)
        self._redo_stack.append((command, result))

        return True

    def redo(self, context: TContext) -> bool:
        """Redo last undone command.

        Args:
            context: Execution context

        Returns:
            True if redo succeeded, False if no redo stack
        """
        if not self._redo_stack:
            return False

        command, _previous_result = self._redo_stack.pop()
        new_result = command.execute(context=context)
        self._history.append((command, new_result))

        return True

    def can_undo(self) -> bool:
        """Check if undo is available.

        Returns:
            True if history is not empty
        """
        return len(self._history) > 0

    def can_redo(self) -> bool:
        """Check if redo is available.

        Returns:
            True if redo stack is not empty
        """
        return len(self._redo_stack) > 0

    def clear_history(self) -> None:
        """Clear command history and redo stack."""
        self._history.clear()
        self._redo_stack.clear()

    def get_history_count(self) -> int:
        """Get number of commands in history.

        Returns:
            Number of executed commands
        """
        return len(self._history)

    def get_redo_count(self) -> int:
        """Get number of commands in redo stack.

        Returns:
            Number of undone commands
        """
        return len(self._redo_stack)

"""Base command class for actions."""

from abc import ABC, abstractmethod
from typing import Any

from yuna.commands.permissions import ActionPermission


class Command[TContext, TResult](ABC):
    """Abstract base class for all commands.

    Responsibilities:
    - Validate execution conditions
    - Execute action on context
    - Support undo (optional)
    - Define priority and permission requirements

    Usage:
        class MoveCommand(Command[GameWorld, CommandResult]):
            @property
            def priority(self) -> int:
                return 100

            def permission(self, context: GameWorld) -> ActionPermission:
                return ActionPermission(
                    resource_effects=(
                        ResourceEffect(
                            resource_type="energy",
                            modification_type=ResourceModificationType.FLAT,
                            amount=-float(context.config.get("energy_cost")),
                        ),
                    ),
                )

            def can_execute(self, context: GameWorld) -> tuple[bool, str]:
                if context.is_valid_position(self.target):
                    return (True, "")
                return (False, "Invalid position")

            def execute(self, context: GameWorld) -> CommandResult:
                context.move_entity(self.entity_id, self.target)
                return CommandResult(success=True)

            def undo(self, context: GameWorld, result: CommandResult) -> None:
                context.move_entity(self.entity_id, self.original_pos)
    """

    @property
    @abstractmethod
    def priority(self) -> int:
        """Execution priority for this command.

        Lower values execute earlier.

        Returns:
            Priority value
        """
        ...  # pragma: no cover

    @abstractmethod
    def permission(self, context: TContext) -> ActionPermission:
        """Permission requirements for executing this command.

        Args:
            context: Execution context (for accessing config, world state, etc.)

        Returns:
            ActionPermission defining resource effects and constraints
        """
        ...  # pragma: no cover

    @abstractmethod
    def can_execute(self, context: TContext) -> tuple[bool, str]:
        """Validate if command can execute.

        Args:
            context: Execution context

        Returns:
            Tuple of (can_execute, reason_if_not)
        """
        ...  # pragma: no cover

    @abstractmethod
    def execute(self, context: TContext) -> TResult:
        """Execute command on context.

        Args:
            context: Execution context

        Returns:
            Execution result
        """
        ...  # pragma: no cover

    def undo(self, context: TContext, result: TResult) -> None:  # noqa: PLR6301
        """Undo command execution (optional).

        Override this method to support undo functionality.
        Default implementation is a no-op.

        Args:
            context: Execution context
            result: Result from original execution
        """
        _ = context
        _ = result

    def to_dict(self) -> dict[str, Any]:  # noqa: PLR6301
        """Serialize command to dictionary for recording.

        Override this method to include command-specific data in recordings.
        Default implementation returns empty dict.

        Returns:
            Dictionary with command data for serialization
        """
        return {}

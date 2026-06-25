"""Macro command for composing multiple commands."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from yuna.commands.permissions import (
    ActionPermission,
    ResourceEffect,
)
from yuna.commands.result import CommandResult

if TYPE_CHECKING:
    from yuna.commands.command import Command


class MacroCommand[TContext]:
    """Composite command that executes multiple sub-commands.

    Responsibilities:
    - Execute multiple commands in sequence
    - Validate all sub-commands before execution
    - Undo all sub-commands in reverse order
    - Collect results from all sub-commands
    - Aggregate permissions from all sub-commands

    Usage:
        macro = MacroCommand[GameWorld](
            commands=[
                MoveCommand(target=(10, 10)),
                AttackCommand(target_id="enemy_1"),
                CollectCommand(item_id="coin_1"),
            ],
        )

        can_execute, reason = macro.can_execute(context=world)
        if can_execute:
            result = macro.execute(context=world)
    """

    def __init__(
        self,
        commands: Sequence[Command[TContext, CommandResult]],
        priority_value: int = 100,
        permission_override: ActionPermission | None = None,
    ) -> None:
        self._commands = list(commands)
        self._priority = priority_value
        self._permission_override = permission_override
        self._results: list[CommandResult] = []

    def _aggregate_permissions(self, context: TContext) -> ActionPermission:
        """Aggregate permissions from all sub-commands.

        Combines resource effects, required stats (max), and tags from all commands.

        Args:
            context: Execution context for accessing command permissions

        Returns:
            Aggregated ActionPermission
        """
        all_effects: list[ResourceEffect] = []
        all_required_stats: dict[str, float] = {}
        all_forbidden_tags: set[str] = set()
        all_required_tags: set[str] = set()
        max_cooldown = 0

        for command in self._commands:
            perm = command.permission(context=context)

            all_effects.extend(perm.resource_effects)

            for stat, value in perm.required_stats.items():
                all_required_stats[stat] = max(all_required_stats.get(stat, 0.0), value)

            all_forbidden_tags.update(perm.forbidden_tags)
            all_required_tags.update(perm.required_tags)
            max_cooldown = max(max_cooldown, perm.cooldown_ticks)

        return ActionPermission(
            resource_effects=tuple(all_effects),
            required_stats=all_required_stats,
            forbidden_tags=frozenset(all_forbidden_tags),
            required_tags=frozenset(all_required_tags),
            cooldown_ticks=max_cooldown,
        )

    @property
    def priority(self) -> int:
        """Get macro command priority.

        Returns:
            Priority value
        """
        return self._priority

    def permission(self, context: TContext) -> ActionPermission:
        """Get aggregated permission requirements.

        Args:
            context: Execution context for accessing command permissions

        Returns:
            Aggregated ActionPermission from all sub-commands
        """
        if self._permission_override is not None:
            return self._permission_override
        return self._aggregate_permissions(context=context)

    @property
    def commands(self) -> list[Command[TContext, CommandResult]]:
        """Get list of sub-commands.

        Returns:
            List of commands to execute
        """
        return self._commands.copy()

    def can_execute(self, context: TContext) -> tuple[bool, str]:
        """Validate all sub-commands can execute.

        Args:
            context: Execution context

        Returns:
            Tuple of (can_execute, reason_if_not)
        """
        for i, command in enumerate(self._commands):
            can_execute, reason = command.can_execute(context=context)
            if not can_execute:
                return False, f"Command {i} failed: {reason}"
        return True, ""

    def execute(self, context: TContext) -> CommandResult:
        """Execute all sub-commands in sequence.

        Args:
            context: Execution context

        Returns:
            Composite result with all sub-results
        """
        self._results.clear()
        all_data: dict[str, list[dict[str, Any]]] = {"sub_results": []}

        for command in self._commands:
            result = command.execute(context=context)
            self._results.append(result)
            all_data["sub_results"].append(result.data)

        all_success = all(r.success for r in self._results)
        return CommandResult(success=all_success, data=all_data)

    def undo(self, context: TContext) -> None:
        """Undo all sub-commands in reverse order.

        Args:
            context: Execution context
        """
        for command, cmd_result in reversed(
            list(zip(self._commands, self._results, strict=False))
        ):
            command.undo(context=context, result=cmd_result)

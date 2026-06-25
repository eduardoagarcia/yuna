"""Command execution result."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CommandResult:
    """Result of command execution.

    Responsibilities:
    - Track success/failure status
    - Provide failure reason
    - Carry execution data

    Usage:
        result = CommandResult(
            success=True,
            reason=None,
            data={"entity_id": "abc123"},
        )

        if not result.success:
            print(f"Failed: {result.reason}")
    """

    success: bool
    reason: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

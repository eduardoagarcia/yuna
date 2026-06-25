"""State machine component for ECS integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from yuna.fsm.machine import StateMachine


@dataclass
class StateMachineComponent[TContext]:
    """Component holding a state machine instance.

    Responsibilities:
    - Store state machine for entity
    - Provide state-specific context data
    - Enable multiple entities to have independent state machines

    Usage:
        @dataclass
        class AIContext:
            target_position: Position
            aggression: float

        machine = StateMachine[AIContext]()
        machine.add_state(state=idle_state)
        machine.add_state(state=patrol_state)
        machine.set_state(state_name="idle", context=ai_context)

        component = StateMachineComponent(
            machine=machine,
            context=ai_context,
        )
    """

    machine: StateMachine[TContext]
    context: TContext
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary.

        Only serializes the state machine state (current_state, history).
        Context is NOT serialized as it contains runtime references (world, commands)
        that will be recreated during replay.

        Returns:
            Dictionary with machine state and metadata
        """
        return {
            "machine": self.machine.to_dict(),
            "metadata": self.metadata,
        }

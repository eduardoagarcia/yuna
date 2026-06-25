"""Types for behavior tree nodes and execution context."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yuna.ai.blackboard import Blackboard
    from yuna.ecs.world import ECSWorld
    from yuna.types.identifiers import EntityID


class NodeStatus(Enum):
    """Status returned by behavior tree nodes after execution.

    Responsibilities:
    - Indicate node execution result
    - Control tree execution flow
    - Enable composite node logic

    Values:
    - SUCCESS: Node completed successfully
    - FAILURE: Node failed to complete
    - RUNNING: Node is still executing (multi-frame)

    Usage:
        def tick(self, context: BehaviorContext) -> NodeStatus:
            if self.is_complete():
                return NodeStatus.SUCCESS
            elif self.has_failed():
                return NodeStatus.FAILURE
            else:
                return NodeStatus.RUNNING
    """

    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


@dataclass
class BehaviorContext:
    """Execution context passed to behavior tree nodes.

    Responsibilities:
    - Provide access to world state
    - Pass entity and blackboard references
    - Track delta time for time-based logic
    - Enable node isolation (no direct world access)

    Usage:
        context = BehaviorContext(
            world=world,
            entity_id=agent_id,
            blackboard=blackboard,
            delta_time=0.016,
        )

        status = root_node.tick(context=context)
    """

    world: ECSWorld
    entity_id: EntityID
    blackboard: Blackboard
    delta_time: float
    data: dict[str, Any] | None = None

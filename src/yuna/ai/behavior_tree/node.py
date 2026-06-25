"""Base class for behavior tree nodes."""

from abc import ABC, abstractmethod

from yuna.ai.behavior_tree.types import (
    BehaviorContext,
    NodeStatus,
)


class BehaviorNode(ABC):
    """Base class for all behavior tree nodes.

    Responsibilities:
    - Define node execution interface
    - Enable tree composition
    - Provide status returns

    All behavior tree nodes extend this base class and implement
    the tick method. Nodes can be composed into trees using composite
    nodes (Sequence, Selector, Parallel) and modified with decorators
    (Inverter, Repeat, Conditional).

    Usage:
        class CustomActionNode(BehaviorNode):
            def tick(self, context: BehaviorContext) -> NodeStatus:
                # Perform action
                if success:
                    return NodeStatus.SUCCESS
                else:
                    return NodeStatus.FAILURE
    """

    @abstractmethod
    def tick(self, context: BehaviorContext) -> NodeStatus:
        """Execute node logic for current frame.

        Args:
            context: Execution context with world, entity, blackboard

        Returns:
            NodeStatus indicating execution result
        """
        ...  # pragma: no cover

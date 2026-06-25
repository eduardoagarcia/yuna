"""Decorator nodes for modifying child behavior."""

from collections.abc import Callable
from dataclasses import dataclass

from yuna.ai.behavior_tree.node import BehaviorNode
from yuna.ai.behavior_tree.types import (
    BehaviorContext,
    NodeStatus,
)


@dataclass
class DecoratorNode(BehaviorNode):
    """Base class for nodes that modify single child behavior.

    Responsibilities:
    - Wrap single child node
    - Modify child execution or result
    - Provide transformation logic

    Decorator nodes modify how their child executes or
    how the child's result is interpreted (invert, repeat,
    conditional execution).
    """

    child: BehaviorNode | None = None


@dataclass
class InverterNode(DecoratorNode):
    """Invert child node result (SUCCESS ↔ FAILURE).

    Responsibilities:
    - Execute child node
    - Swap SUCCESS and FAILURE
    - Pass through RUNNING unchanged

    Logic:
    - Returns FAILURE if child returns SUCCESS
    - Returns SUCCESS if child returns FAILURE
    - Returns RUNNING if child returns RUNNING

    Usage:
        inverter = InverterNode(
            child=IsEnemyNearbyNode()
        )
    """

    def tick(self, context: BehaviorContext) -> NodeStatus:
        """Execute child and invert result.

        Args:
            context: Execution context

        Returns:
            Inverted child status (SUCCESS ↔ FAILURE)
        """
        if self.child is None:
            return NodeStatus.FAILURE

        status = self.child.tick(context=context)

        if status == NodeStatus.SUCCESS:
            return NodeStatus.FAILURE
        elif status == NodeStatus.FAILURE:
            return NodeStatus.SUCCESS
        else:
            return NodeStatus.RUNNING


@dataclass
class RepeatNode(DecoratorNode):
    """Repeat child execution specified number of times.

    Responsibilities:
    - Execute child multiple times
    - Track repeat count
    - Support infinite repeats

    Logic:
    - Returns RUNNING while repeating
    - Returns FAILURE if child fails
    - Returns SUCCESS after max_repeats

    Usage:
        repeat = RepeatNode(
            child=PatrolWaypointNode(),
            max_repeats=5,
        )
    """

    max_repeats: int = -1
    current_repeat: int = 0

    def tick(self, context: BehaviorContext) -> NodeStatus:
        """Execute child and track repeats.

        Args:
            context: Execution context

        Returns:
            RUNNING while repeating, SUCCESS after max_repeats, FAILURE if child fails
        """
        if self.child is None:
            return NodeStatus.FAILURE

        status = self.child.tick(context=context)

        if status == NodeStatus.FAILURE:
            return NodeStatus.FAILURE

        if status == NodeStatus.SUCCESS:
            self.current_repeat += 1

            if self.max_repeats == -1:
                return NodeStatus.RUNNING

            if self.current_repeat >= self.max_repeats:
                self.current_repeat = 0
                return NodeStatus.SUCCESS

        return NodeStatus.RUNNING


@dataclass
class ConditionalNode(DecoratorNode):
    """Execute child only if condition is true.

    Responsibilities:
    - Evaluate condition before execution
    - Skip child if condition false
    - Enable conditional behavior

    Logic:
    - Returns child status if condition true
    - Returns FAILURE if condition false

    Usage:
        conditional = ConditionalNode(
            child=AttackNode(),
            condition=lambda ctx: ctx.blackboard.get_value("has_target"),
        )
    """

    condition: Callable[[BehaviorContext], bool] | None = None

    def tick(self, context: BehaviorContext) -> NodeStatus:
        """Execute child only if condition true.

        Args:
            context: Execution context

        Returns:
            Child status if condition true, FAILURE if condition false
        """
        if self.child is None or self.condition is None:
            return NodeStatus.FAILURE

        if not self.condition(context):
            return NodeStatus.FAILURE

        return self.child.tick(context=context)


@dataclass
class UntilFailNode(DecoratorNode):
    """Repeat child until it fails.

    Responsibilities:
    - Execute child repeatedly
    - Stop on first failure
    - Enable loop-until-fail logic

    Logic:
    - Returns RUNNING if child succeeds (keeps looping)
    - Returns SUCCESS if child fails (exits loop)

    Usage:
        until_fail = UntilFailNode(
            child=MoveForwardNode()
        )
    """

    def tick(self, context: BehaviorContext) -> NodeStatus:
        """Execute child until failure.

        Args:
            context: Execution context

        Returns:
            RUNNING if child succeeds, SUCCESS if child fails
        """
        if self.child is None:
            return NodeStatus.SUCCESS

        status = self.child.tick(context=context)

        if status == NodeStatus.FAILURE:
            return NodeStatus.SUCCESS

        return NodeStatus.RUNNING

"""Composite nodes for behavior tree composition."""

from dataclasses import dataclass, field

from yuna.ai.behavior_tree.node import BehaviorNode
from yuna.ai.behavior_tree.types import (
    BehaviorContext,
    NodeStatus,
)


@dataclass
class CompositeNode(BehaviorNode):
    """Base class for nodes with multiple children.

    Responsibilities:
    - Manage child node list
    - Track current child index
    - Provide child execution utilities

    Composite nodes execute multiple children in sequence
    or parallel, combining their results according to
    specific logic (Sequence, Selector, Parallel).
    """

    children: list[BehaviorNode] = field(default_factory=list)
    current_child_index: int = 0

    def reset(self) -> None:
        """Reset current child index to beginning."""
        self.current_child_index = 0


@dataclass
class SequenceNode(CompositeNode):
    """Execute children in sequence until one fails.

    Responsibilities:
    - Run children in order
    - Stop on first failure
    - Return success only if all succeed

    Logic:
    - Returns FAILURE if any child fails
    - Returns RUNNING if any child is running
    - Returns SUCCESS if all children succeed

    Usage:
        sequence = SequenceNode(
            children=[
                CheckTargetNode(),
                MoveToTargetNode(),
                AttackTargetNode(),
            ]
        )
    """

    def tick(self, context: BehaviorContext) -> NodeStatus:
        """Execute children in sequence.

        Args:
            context: Execution context

        Returns:
            FAILURE if any child fails, RUNNING if child running, SUCCESS if all succeed
        """
        for child in self.children:
            status = child.tick(context=context)
            if status == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.SUCCESS


@dataclass
class SelectorNode(CompositeNode):
    """Execute children in sequence until one succeeds.

    Responsibilities:
    - Run children in order
    - Stop on first success
    - Return failure only if all fail

    Logic:
    - Returns SUCCESS if any child succeeds
    - Returns RUNNING if any child is running
    - Returns FAILURE if all children fail

    Usage:
        selector = SelectorNode(
            children=[
                AttackEnemyNode(),
                PatrolNode(),
                IdleNode(),
            ]
        )
    """

    def tick(self, context: BehaviorContext) -> NodeStatus:
        """Execute children until one succeeds.

        Args:
            context: Execution context

        Returns:
            SUCCESS if any child succeeds, RUNNING if child running, FAILURE if all fail
        """
        for child in self.children:
            status = child.tick(context=context)
            if status == NodeStatus.SUCCESS:
                return NodeStatus.SUCCESS
            if status == NodeStatus.RUNNING:
                return NodeStatus.RUNNING
        return NodeStatus.FAILURE


@dataclass
class ParallelNode(CompositeNode):
    """Execute all children in parallel (same frame).

    Responsibilities:
    - Run all children every tick
    - Combine results based on policy
    - Support partial success/failure

    Logic:
    - Returns SUCCESS if all children succeed
    - Returns FAILURE if any child fails
    - Returns RUNNING if any child is running

    Usage:
        parallel = ParallelNode(
            children=[
                ScanForEnemiesNode(),
                UpdateHealthBarNode(),
                PlayAnimationNode(),
            ]
        )
    """

    def tick(self, context: BehaviorContext) -> NodeStatus:
        """Execute all children in parallel.

        Args:
            context: Execution context

        Returns:
            SUCCESS if all succeed, FAILURE if any fails, RUNNING if any running
        """
        has_running = False
        for child in self.children:
            status = child.tick(context=context)
            if status == NodeStatus.FAILURE:
                return NodeStatus.FAILURE
            if status == NodeStatus.RUNNING:
                has_running = True

        if has_running:
            return NodeStatus.RUNNING
        return NodeStatus.SUCCESS

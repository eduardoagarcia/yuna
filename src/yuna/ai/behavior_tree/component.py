"""Behavior tree component for ECS integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yuna.ai.behavior_tree.node import BehaviorNode


@dataclass
class BehaviorTreeComponent:
    """Behavior tree attached to AI entity.

    Responsibilities:
    - Store tree root node
    - Track execution state
    - Control tick interval
    - Enable multi-frame execution

    Behavior trees execute via BehaviorTreeSystem which queries
    entities with this component and ticks their root nodes.

    Usage:
        tree_component = BehaviorTreeComponent(
            root=root_node,
            tick_interval=5,
        )

        world.add_component(
            entity_id=agent_id,
            component=tree_component,
        )
    """

    root: BehaviorNode | None = None
    tick_interval: int = 1
    _ticks_since_update: int = field(default=0, init=False, repr=False)
    enabled: bool = True

    def should_tick(self) -> bool:
        """Check if tree should tick this frame.

        Returns:
            True if tree should execute this frame
        """
        if not self.enabled or self.root is None:
            return False

        self._ticks_since_update += 1

        if self._ticks_since_update >= self.tick_interval:
            self._ticks_since_update = 0
            return True

        return False

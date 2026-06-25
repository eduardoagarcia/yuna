"""AI performance optimization tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from yuna.ecs.component import Component

if TYPE_CHECKING:
    from yuna.types.identifiers import EntityID


class AIScheduler:
    """Schedules AI updates across multiple frames.

    Staggers AI updates to distribute load. Instead of updating
    all 1000 NPCs every frame, update 100 per frame over 10 frames.

    Attributes:
        groups: Number of update groups
        current_group: Current group being updated
    """

    def __init__(self, groups: int = 10) -> None:
        """Initialize AI scheduler.

        Args:
            groups: Number of update groups
        """
        self._groups = groups
        self._current_group = 0
        self._entity_assignments: dict[EntityID, int] = {}

    def assign_entity(self, entity_id: EntityID) -> None:
        """Assign entity to update group.

        Args:
            entity_id: Entity to assign
        """
        group = hash(entity_id) % self._groups
        self._entity_assignments[entity_id] = group

    def should_update(self, entity_id: EntityID) -> bool:
        """Check if entity should update this frame.

        Args:
            entity_id: Entity to check

        Returns:
            True if entity's group is current
        """
        if entity_id not in self._entity_assignments:
            self.assign_entity(entity_id=entity_id)

        return self._entity_assignments[entity_id] == self._current_group

    def advance_frame(self) -> None:
        """Advance to next update group."""
        self._current_group = (self._current_group + 1) % self._groups


@dataclass
class AIOptimization(Component):
    """AI optimization settings for entity.

    Attributes:
        update_interval: Ticks between AI updates
        distance_scaling: Reduce update rate when far from player
        enabled_distance: Distance beyond which AI is disabled
    """

    update_interval: int = 1
    distance_scaling: bool = True
    enabled_distance: float = 100.0

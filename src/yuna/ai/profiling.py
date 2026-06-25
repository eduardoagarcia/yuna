"""AI-specific profiling statistics."""

from dataclasses import dataclass


@dataclass
class AIProfileStats:
    """AI profiling statistics.

    Tracks AI subsystem performance metrics per frame.
    Lightweight container for AI-specific timing and counts.

    Attributes:
        behavior_tree_time_ms: Time spent in behavior trees
        perception_time_ms: Time spent in perception
        pathfinding_time_ms: Time spent in pathfinding
        steering_time_ms: Time spent in steering
        entities_updated: Number of entities updated
        entities_skipped: Number of entities skipped (optimization)
    """

    behavior_tree_time_ms: float = 0.0
    perception_time_ms: float = 0.0
    pathfinding_time_ms: float = 0.0
    steering_time_ms: float = 0.0
    entities_updated: int = 0
    entities_skipped: int = 0

    def reset(self) -> None:
        """Reset statistics for new frame."""
        self.behavior_tree_time_ms = 0.0
        self.perception_time_ms = 0.0
        self.pathfinding_time_ms = 0.0
        self.steering_time_ms = 0.0
        self.entities_updated = 0
        self.entities_skipped = 0

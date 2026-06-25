"""Batch processor for modifier calculations across multiple entities."""

from typing import Any

from yuna.modifiers.config import ModifierConfig
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.profiling.monitor import get_performance_monitor
from yuna.types.identifiers import EntityID


class BatchModifierProcessor:
    """Process modifiers for multiple entities in batches.

    Optimizes modifier processing by batching entities together and
    processing them through a single pipeline execution.

    Benefits:
    - Reduced pipeline overhead
    - Better cache utilization
    - Profiling integration

    Usage:
        processor = BatchModifierProcessor(
            config=config,
            profiling_enabled=True,
        )

        # Queue modifiers for multiple entities
        processor.queue_modifier(modifier1)
        processor.queue_modifier(modifier2)
        processor.queue_modifier(modifier3)

        # Process all at once
        results = processor.process_batch(world=world, current_tick=100)

        # Results contain final values per (entity_id, stat)
        health = results[(entity_id, "health")]
    """

    def __init__(self, config: ModifierConfig, profiling_enabled: bool = False) -> None:
        """Initialize batch processor.

        Args:
            config: Modifier configuration
            profiling_enabled: Whether to track performance metrics
        """
        self._pipeline = ModifierPipeline(
            config=config, profiling_enabled=profiling_enabled
        )
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    def queue_modifier(self, modifier: Modifier) -> None:
        """Add modifier to batch queue.

        Args:
            modifier: Modifier to queue
        """
        self._pipeline.queue_modifier(modifier=modifier)

    def process_batch(
        self, world: Any | None = None, current_tick: int = 0
    ) -> dict[tuple[EntityID, str], float]:
        """Process all queued modifiers in single batch.

        Args:
            world: Game world (optional, for component writes)
            current_tick: Current game tick for expiration tracking

        Returns:
            Dictionary of final values per (entity_id, stat)
        """
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="modifier_batch", name="process"):
                self._monitor.record_count(
                    category="modifier_batch",
                    name="queue_size",
                    count=self._pipeline.get_queue_size(),
                )
                return self._pipeline.process(world=world, current_tick=current_tick)
        return self._pipeline.process(world=world, current_tick=current_tick)

    def clear_queue(self) -> None:
        """Clear all queued modifiers without processing."""
        self._pipeline.clear_queue()

    def get_queue_size(self) -> int:
        """Get number of queued modifiers.

        Returns:
            Number of modifiers in queue
        """
        return self._pipeline.get_queue_size()

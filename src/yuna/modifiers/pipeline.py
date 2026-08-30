"""Modifier processing pipeline."""

from typing import Any

from yuna.modifiers.config import ModifierConfig
from yuna.modifiers.context import ModifierContext
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.stages import (
    ApplyStage,
    ClampStage,
    CollectStage,
    ConditionStage,
    ExpansionStage,
    FilterStage,
    GroupStage,
    InterceptStage,
    RelationshipStage,
    ScalingStage,
    SortStage,
    StackStage,
)
from yuna.modifiers.tracker import ModifierTracker
from yuna.pipeline.context import PipelineContext
from yuna.pipeline.pipeline import Pipeline
from yuna.profiling.monitor import get_performance_monitor
from yuna.resources.pools import get_global_pools
from yuna.types.identifiers import EntityID


class ModifierPipeline:
    """Pipeline for processing stat modifications.

    Responsibilities:
    - Queue modifiers for batch processing
    - Execute all pipeline stages
    - Clear queue after processing
    - Emit stat change events

    Usage:
        config = ModifierConfig()
        config.register_stat(
            name="health",
            min_value=0.0,
            max_value=100.0,
            stacking_rule=StackingRule.ADD,
        )
        pipeline = ModifierPipeline(config=config)
        pipeline.queue_modifier(modifier=health_modifier)
        pipeline.process(world=game_world)
    """

    def __init__(self, config: ModifierConfig, profiling_enabled: bool = False) -> None:
        self._config = config
        pools = get_global_pools()
        self._queue: list[Modifier] = pools.modifier_list.acquire()
        self._tracker = ModifierTracker()
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None
        self._pipeline = Pipeline[ModifierContext, ModifierContext, PipelineContext]()
        self._pipeline.add_stage(
            stage=CollectStage(profiling_enabled=profiling_enabled)
        )
        self._pipeline.add_stage(stage=FilterStage(profiling_enabled=profiling_enabled))
        self._pipeline.add_stage(
            stage=ConditionStage(profiling_enabled=profiling_enabled)
        )
        self._pipeline.add_stage(
            stage=ExpansionStage(profiling_enabled=profiling_enabled)
        )
        self._pipeline.add_stage(
            stage=ScalingStage(profiling_enabled=profiling_enabled)
        )
        self._pipeline.add_stage(
            stage=RelationshipStage(profiling_enabled=profiling_enabled)
        )
        self._pipeline.add_stage(stage=SortStage(profiling_enabled=profiling_enabled))
        self._pipeline.add_stage(stage=GroupStage(profiling_enabled=profiling_enabled))
        self._pipeline.add_stage(stage=StackStage(profiling_enabled=profiling_enabled))
        self._pipeline.add_stage(
            stage=InterceptStage(profiling_enabled=profiling_enabled)
        )
        self._pipeline.add_stage(stage=ClampStage(profiling_enabled=profiling_enabled))
        self._pipeline.add_stage(stage=ApplyStage(profiling_enabled=profiling_enabled))

    def queue_modifier(self, modifier: Modifier) -> None:
        """Add modifier to processing queue.

        Args:
            modifier: Modifier to queue
        """
        self._queue.append(modifier)

    def process(
        self, world: Any | None = None, current_tick: int = 0
    ) -> dict[tuple[EntityID, str], float]:
        """Process all queued modifiers through pipeline.

        Args:
            world: Game world (optional, for component writes)
            current_tick: Current game tick for expiration tracking

        Returns:
            Dictionary of final values per (entity_id, stat)
        """
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="pipeline", name="modifiers"):
                return self._execute_process(world=world, current_tick=current_tick)
        return self._execute_process(world=world, current_tick=current_tick)

    def _execute_process(
        self, world: Any | None, current_tick: int
    ) -> dict[tuple[EntityID, str], float]:
        """Execute pipeline processing logic.

        A fresh queue is installed before the stages run, so modifiers
        queued from inside the pipeline (stage callbacks, interceptors)
        survive to the next flush instead of being cleared with the
        batch that spawned them.

        A stage that raises discards the batch it was processing: the
        pooled list is released either way, and the fresh queue keeps
        only what was added during the failed run.
        """
        self._tracker.clear_expired(current_tick=current_tick)

        pools = get_global_pools()
        all_modifiers = self._queue
        self._queue = pools.modifier_list.acquire()

        for modifier in all_modifiers:
            if modifier.duration_ticks is not None:
                self._tracker.track_modifier(
                    modifier=modifier, current_tick=current_tick
                )

        try:
            if not all_modifiers:
                return {}

            context = ModifierContext(
                modifiers=all_modifiers,
                config=self._config,
                world=world,
                current_tick=current_tick,
            )
            pipe_context = PipelineContext()
            result = self._pipeline.execute(value=context, context=pipe_context)
            return result.final_values
        finally:
            pools.modifier_list.release(obj=all_modifiers)

    def clear_queue(self) -> None:
        """Clear all queued modifiers without processing."""
        pools = get_global_pools()
        pools.modifier_list.release(obj=self._queue)
        self._queue = pools.modifier_list.acquire()

    def get_queue_size(self) -> int:
        """Get number of queued modifiers.

        Returns:
            Number of modifiers in queue
        """
        return len(self._queue)

    def insert_stage_before(
        self,
        before: str,
        stage: Any,
    ) -> None:
        """Insert custom stage before named standard stage.

        Allows games to inject game-specific logic at precise pipeline points.

        Args:
            before: Name of stage to insert before (use ModifierStage enum)
            stage: Custom stage implementing PipelineStage interface

        Raises:
            ValidationError: If stage name not found

        Example:
            from yuna.modifiers.types import ModifierStage

            pipeline.insert_stage_before(
                before=ModifierStage.CLAMP,
                stage=CustomAmplificationStage()
            )
        """
        self._pipeline.insert_stage_before(before=before, stage=stage)

    def insert_stage_after(
        self,
        after: str,
        stage: Any,
    ) -> None:
        """Insert custom stage after named standard stage.

        Allows games to inject game-specific logic at precise pipeline points.

        Args:
            after: Name of stage to insert after (use ModifierStage enum)
            stage: Custom stage implementing PipelineStage interface

        Raises:
            ValidationError: If stage name not found

        Example:
            from yuna.modifiers.types import ModifierStage

            pipeline.insert_stage_after(
                after=ModifierStage.STACK,
                stage=CustomAmplificationStage()
            )
        """
        self._pipeline.insert_stage_after(after=after, stage=stage)

    @property
    def config(self) -> ModifierConfig:
        """Get the modifier config.

        Returns:
            ModifierConfig instance
        """
        return self._config

    @property
    def tracker(self) -> ModifierTracker:
        """Get the modifier tracker.

        Returns:
            ModifierTracker instance
        """
        return self._tracker

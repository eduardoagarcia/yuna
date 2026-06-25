"""Pipeline for composing processing stages."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from yuna.exceptions import ValidationError

if TYPE_CHECKING:
    from yuna.pipeline.stage import PipelineStage


class Pipeline[TInput, TOutput, TContext]:
    """Composable pipeline for sequential data processing.

    Responsibilities:
    - Manage ordered collection of processing stages
    - Execute stages in sequence
    - Support before/after hooks
    - Allow dynamic stage insertion/removal

    Usage:
        pipeline = Pipeline[str, int, MyContext]()
        pipeline.add_stage(stage=parse_stage)
        pipeline.add_stage(stage=validate_stage)
        pipeline.before(hook=lambda ctx: print("Starting"))
        pipeline.after(hook=lambda ctx: print("Done"))

        result = pipeline.execute(input="42", context=my_context)
    """

    def __init__(self) -> None:
        self._stages: list[PipelineStage[Any, Any, TContext]] = []
        self._before_hooks: list[Callable[[TContext], None]] = []
        self._after_hooks: list[Callable[[TContext], None]] = []

    def add_stage(
        self,
        stage: PipelineStage[Any, Any, TContext],
    ) -> None:
        """Add stage to end of pipeline.

        Args:
            stage: Stage to add
        """
        self._stages.append(stage)

    def insert_stage(
        self,
        index: int,
        stage: PipelineStage[Any, Any, TContext],
    ) -> None:
        """Insert stage at specific position.

        Args:
            index: Position to insert at
            stage: Stage to insert
        """
        self._stages.insert(index, stage)

    def insert_stage_before(
        self,
        before: str,
        stage: PipelineStage[Any, Any, TContext],
    ) -> None:
        """Insert stage before named stage.

        Args:
            before: Name of stage to insert before (can use ModifierStage enum)
            stage: Stage to insert

        Raises:
            ValidationError: If stage name not found
        """
        for i, existing_stage in enumerate(self._stages):
            if existing_stage.name == before:
                self._stages.insert(i, stage)
                return
        raise ValidationError(
            reason=f"Stage '{before}' not found in pipeline",
            field="before",
            value=before,
        )

    def insert_stage_after(
        self,
        after: str,
        stage: PipelineStage[Any, Any, TContext],
    ) -> None:
        """Insert stage after named stage.

        Args:
            after: Name of stage to insert after (can use ModifierStage enum)
            stage: Stage to insert

        Raises:
            ValidationError: If stage name not found
        """
        for i, existing_stage in enumerate(self._stages):
            if existing_stage.name == after:
                self._stages.insert(i + 1, stage)
                return
        raise ValidationError(
            reason=f"Stage '{after}' not found in pipeline",
            field="after",
            value=after,
        )

    def remove_stage(self, name: str) -> None:
        """Remove stage by name.

        Args:
            name: Name of stage to remove

        Raises:
            ValidationError: If stage not found
        """
        for i, stage in enumerate(self._stages):
            if stage.name == name:
                self._stages.pop(i)
                return
        raise ValidationError(
            reason=f"Stage '{name}' not found",
            field="name",
            value=name,
        )

    def before(self, hook: Callable[[TContext], None]) -> None:
        """Add hook to run before pipeline execution.

        Args:
            hook: Callable that receives context
        """
        self._before_hooks.append(hook)

    def after(self, hook: Callable[[TContext], None]) -> None:
        """Add hook to run after pipeline execution.

        Args:
            hook: Callable that receives context
        """
        self._after_hooks.append(hook)

    def execute(self, value: TInput, context: TContext) -> TOutput:
        """Execute pipeline with input data and context.

        Args:
            value: Initial input value
            context: Pipeline context

        Returns:
            Final output after all stages
        """
        for hook in self._before_hooks:
            hook(context)

        current: Any = value
        for stage in self._stages:
            current = stage.process(value=current, context=context)

        for hook in self._after_hooks:
            hook(context)

        return cast(TOutput, current)

    def get_stage_count(self) -> int:
        """Get number of stages in pipeline.

        Returns:
            Number of stages
        """
        return len(self._stages)

    def get_stage_names(self) -> list[str]:
        """Get list of stage names in order.

        Returns:
            List of stage names
        """
        return [stage.name for stage in self._stages]

    def clear(self) -> None:
        """Remove all stages and hooks."""
        self._stages.clear()
        self._before_hooks.clear()
        self._after_hooks.clear()

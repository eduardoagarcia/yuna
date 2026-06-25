"""Pipeline registry for named pipelines."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yuna.exceptions import ValidationError

if TYPE_CHECKING:
    from yuna.pipeline.pipeline import Pipeline


class PipelineRegistry:
    """Registry for named pipelines.

    Responsibilities:
    - Store pipelines by name
    - Retrieve pipelines by name
    - Check pipeline existence
    - Clear registry (for testing)

    Usage:
        registry = PipelineRegistry()
        registry.register(name="validation", pipeline=validation_pipeline)
        pipeline = registry.get(name="validation")
        if registry.has(name="validation"):
            print("Pipeline exists")
    """

    def __init__(self) -> None:
        self._pipelines: dict[str, Pipeline[Any, Any, Any]] = {}

    def register(
        self,
        name: str,
        pipeline: Pipeline[Any, Any, Any],
    ) -> None:
        """Register named pipeline.

        Args:
            name: Pipeline identifier
            pipeline: Pipeline to register
        """
        self._pipelines[name] = pipeline

    def get(self, name: str) -> Pipeline[Any, Any, Any]:
        """Get pipeline by name.

        Args:
            name: Pipeline identifier

        Returns:
            Registered pipeline

        Raises:
            ValidationError: If pipeline not found
        """
        if name not in self._pipelines:
            raise ValidationError(
                reason=f"Pipeline '{name}' not found",
                field="name",
                value=name,
            )
        return self._pipelines[name]

    def has(self, name: str) -> bool:
        """Check if pipeline exists.

        Args:
            name: Pipeline identifier

        Returns:
            True if pipeline registered
        """
        return name in self._pipelines

    def clear(self) -> None:
        """Remove all registered pipelines."""
        self._pipelines.clear()

    def get_all_names(self) -> list[str]:
        """Get list of all registered pipeline names.

        Returns:
            List of pipeline names
        """
        return list(self._pipelines.keys())

    def get_count(self) -> int:
        """Get number of registered pipelines.

        Returns:
            Number of pipelines
        """
        return len(self._pipelines)

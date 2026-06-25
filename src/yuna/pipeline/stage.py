"""Pipeline stage abstraction."""

from abc import ABC, abstractmethod


class PipelineStage[TInput, TOutput, TContext](ABC):
    """Abstract base class for pipeline stages.

    Stages process data and transform input to output within a context.

    Type Parameters:
        TInput: Input data type
        TOutput: Output data type
        TContext: Pipeline context type

    Usage:
        class UppercaseStage(PipelineStage[str, str, MyContext]):
            @property
            def name(self) -> str:
                return "uppercase"

            def process(self, input: str, context: MyContext) -> str:
                return input.upper()
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get stage name identifier.

        Returns:
            Stage name
        """
        ...  # pragma: no cover

    @abstractmethod
    def process(self, value: TInput, context: TContext) -> TOutput:
        """Process input data and produce output.

        Args:
            value: Input value
            context: Pipeline context

        Returns:
            Processed output
        """
        ...  # pragma: no cover

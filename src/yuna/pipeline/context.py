"""Pipeline context base class."""


class PipelineContext:
    """Base class for pipeline context.

    Context carries state and configuration through pipeline stages.
    Extend this class to create specific pipeline contexts.

    Usage:
        class MyContext(PipelineContext):
            def __init__(self) -> None:
                self.value = 0
                self.metadata: dict[str, str] = {}
    """

    pass

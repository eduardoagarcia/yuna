"""Tests for pipeline stage."""

from faker import Faker

from yuna.pipeline.context import PipelineContext
from yuna.pipeline.stage import PipelineStage

fake = Faker()


class TestContext(PipelineContext):
    """Test context for pipeline."""

    def __init__(self) -> None:
        self.metadata: dict[str, str] = {}
        self.call_count = 0


class UppercaseStage(PipelineStage[str, str, TestContext]):
    """Test stage that uppercases strings."""

    @property
    def name(self) -> str:
        return "uppercase"

    def process(self, input: str, context: TestContext) -> str:
        context.call_count += 1
        return input.upper()


class MultiplyStage(PipelineStage[int, int, TestContext]):
    """Test stage that multiplies by factor."""

    def __init__(self, factor: int) -> None:
        self._factor = factor

    @property
    def name(self) -> str:
        return f"multiply_by_{self._factor}"

    def process(self, input: int, context: TestContext) -> int:
        context.call_count += 1
        return input * self._factor


class TypeTransformStage(PipelineStage[str, int, TestContext]):
    """Test stage that transforms string to int."""

    @property
    def name(self) -> str:
        return "str_to_int"

    def process(self, input: str, context: TestContext) -> int:
        context.call_count += 1
        return int(input)


def test_pipeline_stage_is_abstract() -> None:
    """Test PipelineStage cannot be instantiated."""
    msg = "Can't instantiate abstract class"
    try:
        PipelineStage[str, str, TestContext]()  # type: ignore[abstract]
        raise AssertionError(msg)
    except TypeError:
        pass


def test_concrete_stage_can_be_created() -> None:
    """Test concrete stage can be instantiated."""
    stage = UppercaseStage()
    assert stage is not None


def test_stage_has_name() -> None:
    """Test stage has name property."""
    stage = UppercaseStage()
    assert stage.name == "uppercase"


def test_stage_can_process_data() -> None:
    """Test stage processes data."""
    stage = UppercaseStage()
    context = TestContext()
    text = fake.word()
    result = stage.process(input=text, context=context)
    assert result == text.upper()


def test_stage_with_different_types() -> None:
    """Test stage with different input/output types."""
    stage = TypeTransformStage()
    context = TestContext()
    result = stage.process(input="42", context=context)
    assert result == 42


def test_stage_receives_context() -> None:
    """Test stage receives and can modify context."""
    stage = UppercaseStage()
    context = TestContext()
    assert context.call_count == 0
    stage.process(input=fake.word(), context=context)
    assert context.call_count == 1


def test_stage_with_configuration() -> None:
    """Test stage with constructor parameters."""
    factor = fake.random_int(min=2, max=10)
    stage = MultiplyStage(factor=factor)
    context = TestContext()
    value = fake.random_int(min=1, max=100)
    result = stage.process(input=value, context=context)
    assert result == value * factor


def test_stage_name_unique_per_instance() -> None:
    """Test stage name can be unique per instance."""
    stage_1 = MultiplyStage(factor=2)
    stage_2 = MultiplyStage(factor=3)
    assert stage_1.name != stage_2.name


def test_multiple_process_calls() -> None:
    """Test stage can process multiple inputs."""
    stage = UppercaseStage()
    context = TestContext()
    texts = [fake.word() for _ in range(5)]
    results = [stage.process(input=text, context=context) for text in texts]
    assert results == [text.upper() for text in texts]


def test_context_persists_across_stages() -> None:
    """Test context modifications persist."""
    stage_1 = UppercaseStage()
    stage_2 = UppercaseStage()
    context = TestContext()
    stage_1.process(input=fake.word(), context=context)
    assert context.call_count == 1
    stage_2.process(input=fake.word(), context=context)
    assert context.call_count == 2


def test_stage_with_empty_string() -> None:
    """Test stage handles empty input."""
    stage = UppercaseStage()
    context = TestContext()
    result = stage.process(input="", context=context)
    assert not result


def test_stage_with_zero_value() -> None:
    """Test stage handles zero value."""
    stage = MultiplyStage(factor=5)
    context = TestContext()
    result = stage.process(input=0, context=context)
    assert result == 0


def test_stage_with_negative_value() -> None:
    """Test stage handles negative values."""
    stage = MultiplyStage(factor=2)
    context = TestContext()
    value = fake.random_int(min=-100, max=-1)
    result = stage.process(input=value, context=context)
    assert result == value * 2


def test_incomplete_stage_without_name_raises_error() -> None:
    """Test incomplete stage without name raises TypeError."""

    class IncompleteStage(PipelineStage[str, str, TestContext]):
        def process(self, input: str, context: TestContext) -> str:
            return input

    msg = "Can't instantiate abstract class"
    try:
        IncompleteStage()  # type: ignore[abstract]
        raise AssertionError(msg)
    except TypeError:
        pass


def test_incomplete_stage_without_process_raises_error() -> None:
    """Test incomplete stage without process raises TypeError."""

    class IncompleteStage(PipelineStage[str, str, TestContext]):
        @property
        def name(self) -> str:
            return "incomplete"

    msg = "Can't instantiate abstract class"
    try:
        IncompleteStage()  # type: ignore[abstract]
        raise AssertionError(msg)
    except TypeError:
        pass

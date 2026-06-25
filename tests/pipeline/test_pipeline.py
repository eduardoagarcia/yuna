"""Tests for pipeline."""

from faker import Faker

from yuna.exceptions import ValidationError
from yuna.pipeline.context import PipelineContext
from yuna.pipeline.pipeline import Pipeline
from yuna.pipeline.stage import PipelineStage

fake = Faker()


class TestContext(PipelineContext):
    """Test context for pipeline."""

    def __init__(self) -> None:
        self.operations: list[str] = []
        self.before_called = 0
        self.after_called = 0


class AddStage(PipelineStage[int, int, TestContext]):
    """Test stage that adds value."""

    def __init__(self, value: int) -> None:
        self._value = value

    @property
    def name(self) -> str:
        return f"add_{self._value}"

    def process(self, value: int, context: TestContext) -> int:
        context.operations.append(f"add_{self._value}")
        return value + self._value


class MultiplyStage(PipelineStage[int, int, TestContext]):
    """Test stage that multiplies by factor."""

    def __init__(self, factor: int) -> None:
        self._factor = factor

    @property
    def name(self) -> str:
        return f"multiply_{self._factor}"

    def process(self, value: int, context: TestContext) -> int:
        context.operations.append(f"multiply_{self._factor}")
        return value * self._factor


class SquareStage(PipelineStage[int, int, TestContext]):
    """Test stage that squares value."""

    @property
    def name(self) -> str:
        return "square"

    def process(self, value: int, context: TestContext) -> int:
        context.operations.append("square")
        return value * value


def test_pipeline_creation() -> None:
    """Test Pipeline can be instantiated."""
    pipeline = Pipeline[int, int, TestContext]()
    assert pipeline is not None


def test_add_stage() -> None:
    """Test adding stage to pipeline."""
    pipeline = Pipeline[int, int, TestContext]()
    stage = AddStage(value=5)
    pipeline.add_stage(stage=stage)
    assert pipeline.get_stage_count() == 1


def test_add_multiple_stages() -> None:
    """Test adding multiple stages."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=5))
    pipeline.add_stage(stage=MultiplyStage(factor=2))
    pipeline.add_stage(stage=SquareStage())
    assert pipeline.get_stage_count() == 3


def test_execute_single_stage() -> None:
    """Test executing pipeline with single stage."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=10))
    context = TestContext()
    result = pipeline.execute(value=5, context=context)
    assert result == 15


def test_execute_multiple_stages() -> None:
    """Test data flows through multiple stages."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=3))
    pipeline.add_stage(stage=MultiplyStage(factor=2))
    context = TestContext()
    result = pipeline.execute(value=5, context=context)
    assert result == 16


def test_stage_order_matters() -> None:
    """Test stage execution order affects result."""
    pipeline_1 = Pipeline[int, int, TestContext]()
    pipeline_1.add_stage(stage=AddStage(value=2))
    pipeline_1.add_stage(stage=MultiplyStage(factor=3))
    context_1 = TestContext()
    result_1 = pipeline_1.execute(value=5, context=context_1)
    pipeline_2 = Pipeline[int, int, TestContext]()
    pipeline_2.add_stage(stage=MultiplyStage(factor=3))
    pipeline_2.add_stage(stage=AddStage(value=2))
    context_2 = TestContext()
    result_2 = pipeline_2.execute(value=5, context=context_2)
    assert result_1 != result_2


def test_execute_empty_pipeline() -> None:
    """Test executing pipeline with no stages."""
    pipeline = Pipeline[int, int, TestContext]()
    context = TestContext()
    value = fake.random_int(min=1, max=100)
    result = pipeline.execute(value=value, context=context)
    assert result == value


def test_before_hook() -> None:
    """Test before hook is called."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    context = TestContext()

    def before_hook(ctx: TestContext) -> None:
        ctx.before_called += 1

    pipeline.before(hook=before_hook)
    pipeline.execute(value=5, context=context)
    assert context.before_called == 1


def test_after_hook() -> None:
    """Test after hook is called."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    context = TestContext()

    def after_hook(ctx: TestContext) -> None:
        ctx.after_called += 1

    pipeline.after(hook=after_hook)
    pipeline.execute(value=5, context=context)
    assert context.after_called == 1


def test_multiple_before_hooks() -> None:
    """Test multiple before hooks are called."""
    pipeline = Pipeline[int, int, TestContext]()
    context = TestContext()

    def hook_1(ctx: TestContext) -> None:
        ctx.before_called += 1

    def hook_2(ctx: TestContext) -> None:
        ctx.before_called += 10

    pipeline.before(hook=hook_1)
    pipeline.before(hook=hook_2)
    pipeline.execute(value=5, context=context)
    assert context.before_called == 11


def test_multiple_after_hooks() -> None:
    """Test multiple after hooks are called."""
    pipeline = Pipeline[int, int, TestContext]()
    context = TestContext()

    def hook_1(ctx: TestContext) -> None:
        ctx.after_called += 1

    def hook_2(ctx: TestContext) -> None:
        ctx.after_called += 10

    pipeline.after(hook=hook_1)
    pipeline.after(hook=hook_2)
    pipeline.execute(value=5, context=context)
    assert context.after_called == 11


def test_hooks_called_in_order() -> None:
    """Test before hooks run before stages, after hooks run after."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    context = TestContext()

    def before_hook(ctx: TestContext) -> None:
        ctx.operations.append("before")

    def after_hook(ctx: TestContext) -> None:
        ctx.operations.append("after")

    pipeline.before(hook=before_hook)
    pipeline.after(hook=after_hook)
    pipeline.execute(value=5, context=context)
    assert context.operations == ["before", "add_1", "after"]


def test_insert_stage_at_beginning() -> None:
    """Test inserting stage at index 0."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.add_stage(stage=AddStage(value=2))
    pipeline.insert_stage(index=0, stage=MultiplyStage(factor=10))
    names = pipeline.get_stage_names()
    assert names[0] == "multiply_10"


def test_insert_stage_in_middle() -> None:
    """Test inserting stage in middle of pipeline."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.add_stage(stage=AddStage(value=3))
    pipeline.insert_stage(index=1, stage=AddStage(value=2))
    context = TestContext()
    pipeline.execute(value=0, context=context)
    assert context.operations == ["add_1", "add_2", "add_3"]


def test_insert_stage_at_end() -> None:
    """Test inserting stage at end."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.insert_stage(index=1, stage=AddStage(value=2))
    names = pipeline.get_stage_names()
    assert names[-1] == "add_2"


def test_remove_stage() -> None:
    """Test removing stage by name."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.add_stage(stage=AddStage(value=2))
    pipeline.add_stage(stage=AddStage(value=3))
    pipeline.remove_stage(name="add_2")
    assert pipeline.get_stage_count() == 2


def test_remove_stage_affects_execution() -> None:
    """Test removing stage changes pipeline result."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.add_stage(stage=MultiplyStage(factor=100))
    pipeline.add_stage(stage=AddStage(value=3))
    context_1 = TestContext()
    result_1 = pipeline.execute(value=0, context=context_1)
    pipeline.remove_stage(name="multiply_100")
    context_2 = TestContext()
    result_2 = pipeline.execute(value=0, context=context_2)
    assert result_1 != result_2


def test_remove_nonexistent_stage_raises_error() -> None:
    """Test removing non-existent stage raises ValidationError."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    try:
        pipeline.remove_stage(name="nonexistent")
        msg = "Expected ValidationError"
        raise AssertionError(msg)
    except ValidationError as e:
        assert "not found" in str(e)


def test_get_stage_names() -> None:
    """Test getting list of stage names."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.add_stage(stage=MultiplyStage(factor=2))
    pipeline.add_stage(stage=SquareStage())
    names = pipeline.get_stage_names()
    assert names == ["add_1", "multiply_2", "square"]


def test_get_stage_names_empty_pipeline() -> None:
    """Test getting stage names from empty pipeline."""
    pipeline = Pipeline[int, int, TestContext]()
    names = pipeline.get_stage_names()
    assert names == []


def test_get_stage_count() -> None:
    """Test getting stage count."""
    pipeline = Pipeline[int, int, TestContext]()
    assert pipeline.get_stage_count() == 0
    pipeline.add_stage(stage=AddStage(value=1))
    assert pipeline.get_stage_count() == 1
    pipeline.add_stage(stage=AddStage(value=2))
    assert pipeline.get_stage_count() == 2


def test_clear_pipeline() -> None:
    """Test clearing all stages and hooks."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.add_stage(stage=AddStage(value=2))
    pipeline.before(hook=lambda ctx: None)
    pipeline.after(hook=lambda ctx: None)
    pipeline.clear()
    assert pipeline.get_stage_count() == 0


def test_clear_pipeline_removes_hooks() -> None:
    """Test clear removes hooks."""
    pipeline = Pipeline[int, int, TestContext]()
    context = TestContext()

    pipeline.before(hook=lambda ctx: ctx.operations.append("before"))
    pipeline.after(hook=lambda ctx: ctx.operations.append("after"))
    pipeline.clear()
    pipeline.execute(value=5, context=context)
    assert context.operations == []


def test_execute_multiple_times() -> None:
    """Test pipeline can be executed multiple times."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=10))
    context = TestContext()
    result_1 = pipeline.execute(value=5, context=context)
    result_2 = pipeline.execute(value=3, context=context)
    result_3 = pipeline.execute(value=7, context=context)
    assert result_1 == 15
    assert result_2 == 13
    assert result_3 == 17


def test_complex_pipeline() -> None:
    """Test complex pipeline with multiple stages and hooks."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=2))
    pipeline.add_stage(stage=MultiplyStage(factor=3))
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.add_stage(stage=SquareStage())
    context = TestContext()

    pipeline.before(hook=lambda ctx: ctx.operations.append("start"))
    pipeline.after(hook=lambda ctx: ctx.operations.append("end"))
    result = pipeline.execute(value=5, context=context)
    assert result == 484
    assert context.operations == [
        "start",
        "add_2",
        "multiply_3",
        "add_1",
        "square",
        "end",
    ]


def test_pipeline_with_zero_input() -> None:
    """Test pipeline with zero as input."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=5))
    pipeline.add_stage(stage=MultiplyStage(factor=2))
    context = TestContext()
    result = pipeline.execute(value=0, context=context)
    assert result == 10


def test_pipeline_with_negative_input() -> None:
    """Test pipeline with negative input."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=10))
    pipeline.add_stage(stage=MultiplyStage(factor=2))
    context = TestContext()
    result = pipeline.execute(value=-5, context=context)
    assert result == 10


def test_remove_first_stage() -> None:
    """Test removing first stage."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.add_stage(stage=AddStage(value=2))
    pipeline.remove_stage(name="add_1")
    names = pipeline.get_stage_names()
    assert names == ["add_2"]


def test_remove_last_stage() -> None:
    """Test removing last stage."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.add_stage(stage=AddStage(value=2))
    pipeline.remove_stage(name="add_2")
    names = pipeline.get_stage_names()
    assert names == ["add_1"]


def test_remove_only_stage() -> None:
    """Test removing only stage leaves empty pipeline."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.remove_stage(name="add_1")
    assert pipeline.get_stage_count() == 0


def test_insert_stage_before() -> None:
    """Test inserting stage before named stage."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.add_stage(stage=AddStage(value=3))
    pipeline.insert_stage_before(before="add_3", stage=AddStage(value=2))
    context = TestContext()
    pipeline.execute(value=0, context=context)
    assert context.operations == ["add_1", "add_2", "add_3"]


def test_insert_stage_before_first_stage() -> None:
    """Test inserting stage before first stage."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=2))
    pipeline.add_stage(stage=AddStage(value=3))
    pipeline.insert_stage_before(before="add_2", stage=AddStage(value=1))
    context = TestContext()
    pipeline.execute(value=0, context=context)
    assert context.operations == ["add_1", "add_2", "add_3"]


def test_insert_stage_before_nonexistent_raises_error() -> None:
    """Test inserting before non-existent stage raises ValidationError."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    try:
        pipeline.insert_stage_before(before="nonexistent", stage=AddStage(value=2))
        msg = "Expected ValidationError"
        raise AssertionError(msg)
    except ValidationError as e:
        assert "not found" in str(e)


def test_insert_stage_after() -> None:
    """Test inserting stage after named stage."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.add_stage(stage=AddStage(value=3))
    pipeline.insert_stage_after(after="add_1", stage=AddStage(value=2))
    context = TestContext()
    pipeline.execute(value=0, context=context)
    assert context.operations == ["add_1", "add_2", "add_3"]


def test_insert_stage_after_last_stage() -> None:
    """Test inserting stage after last stage."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    pipeline.add_stage(stage=AddStage(value=2))
    pipeline.insert_stage_after(after="add_2", stage=AddStage(value=3))
    context = TestContext()
    pipeline.execute(value=0, context=context)
    assert context.operations == ["add_1", "add_2", "add_3"]


def test_insert_stage_after_nonexistent_raises_error() -> None:
    """Test inserting after non-existent stage raises ValidationError."""
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=1))
    try:
        pipeline.insert_stage_after(after="nonexistent", stage=AddStage(value=2))
        msg = "Expected ValidationError"
        raise AssertionError(msg)
    except ValidationError as e:
        assert "not found" in str(e)

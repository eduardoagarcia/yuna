"""Tests for pipeline registry."""

from faker import Faker

from yuna.exceptions import ValidationError
from yuna.pipeline.context import PipelineContext
from yuna.pipeline.pipeline import Pipeline
from yuna.pipeline.registry import PipelineRegistry
from yuna.pipeline.stage import PipelineStage

fake = Faker()


class TestContext(PipelineContext):
    """Test context for pipeline."""

    pass


class AddStage(PipelineStage[int, int, TestContext]):
    """Test stage that adds value."""

    def __init__(self, value: int) -> None:
        self._value = value

    @property
    def name(self) -> str:
        return f"add_{self._value}"

    def process(self, value: int, context: TestContext) -> int:
        return value + self._value


def test_pipeline_registry_creation() -> None:
    """Test PipelineRegistry can be instantiated."""
    registry = PipelineRegistry()
    assert registry is not None


def test_register_pipeline() -> None:
    """Test registering a pipeline."""
    registry = PipelineRegistry()
    pipeline = Pipeline[int, int, TestContext]()
    name = fake.word()
    registry.register(name=name, pipeline=pipeline)
    assert registry.has(name=name)


def test_get_pipeline() -> None:
    """Test getting registered pipeline."""
    registry = PipelineRegistry()
    pipeline = Pipeline[int, int, TestContext]()
    name = fake.word()
    registry.register(name=name, pipeline=pipeline)
    retrieved = registry.get(name=name)
    assert retrieved is pipeline


def test_get_nonexistent_pipeline_raises_error() -> None:
    """Test getting non-existent pipeline raises ValidationError."""
    registry = PipelineRegistry()
    name = fake.word()
    try:
        registry.get(name=name)
        msg = "Expected ValidationError"
        raise AssertionError(msg)
    except ValidationError as e:
        assert name in str(e)


def test_has_returns_false_for_missing_pipeline() -> None:
    """Test has returns False for unregistered pipeline."""
    registry = PipelineRegistry()
    assert registry.has(name=fake.word()) is False


def test_register_multiple_pipelines() -> None:
    """Test registering multiple pipelines."""
    registry = PipelineRegistry()
    pipeline_1 = Pipeline[int, int, TestContext]()
    pipeline_2 = Pipeline[int, int, TestContext]()
    name_1 = fake.word()
    name_2 = fake.word()
    if name_1 == name_2:
        name_2 = f"{name_2}_2"
    registry.register(name=name_1, pipeline=pipeline_1)
    registry.register(name=name_2, pipeline=pipeline_2)
    assert registry.get_count() == 2


def test_register_overwrites_existing_pipeline() -> None:
    """Test registering same name overwrites existing."""
    registry = PipelineRegistry()
    pipeline_1 = Pipeline[int, int, TestContext]()
    pipeline_2 = Pipeline[int, int, TestContext]()
    name = fake.word()
    registry.register(name=name, pipeline=pipeline_1)
    registry.register(name=name, pipeline=pipeline_2)
    retrieved = registry.get(name=name)
    assert retrieved is pipeline_2


def test_clear_registry() -> None:
    """Test clearing all pipelines."""
    registry = PipelineRegistry()
    pipeline_1 = Pipeline[int, int, TestContext]()
    pipeline_2 = Pipeline[int, int, TestContext]()
    registry.register(name=fake.word(), pipeline=pipeline_1)
    registry.register(name=fake.word(), pipeline=pipeline_2)
    registry.clear()
    assert registry.get_count() == 0


def test_clear_empty_registry() -> None:
    """Test clearing empty registry."""
    registry = PipelineRegistry()
    registry.clear()
    assert registry.get_count() == 0


def test_get_all_names() -> None:
    """Test getting all registered pipeline names."""
    registry = PipelineRegistry()
    pipeline = Pipeline[int, int, TestContext]()
    name_1 = fake.unique.word()
    name_2 = fake.unique.word()
    name_3 = fake.unique.word()
    registry.register(name=name_1, pipeline=pipeline)
    registry.register(name=name_2, pipeline=pipeline)
    registry.register(name=name_3, pipeline=pipeline)
    names = registry.get_all_names()
    assert set(names) == {name_1, name_2, name_3}


def test_get_all_names_empty_registry() -> None:
    """Test getting names from empty registry."""
    registry = PipelineRegistry()
    names = registry.get_all_names()
    assert names == []


def test_get_count() -> None:
    """Test getting count of registered pipelines."""
    registry = PipelineRegistry()
    pipeline = Pipeline[int, int, TestContext]()
    assert registry.get_count() == 0
    registry.register(name=fake.unique.word(), pipeline=pipeline)
    assert registry.get_count() == 1
    registry.register(name=fake.unique.word(), pipeline=pipeline)
    assert registry.get_count() == 2


def test_registered_pipeline_works() -> None:
    """Test registered pipeline can execute."""
    registry = PipelineRegistry()
    pipeline = Pipeline[int, int, TestContext]()
    pipeline.add_stage(stage=AddStage(value=10))
    name = fake.word()
    registry.register(name=name, pipeline=pipeline)
    retrieved = registry.get(name=name)
    context = TestContext()
    result = retrieved.execute(value=5, context=context)
    assert result == 15


def test_register_pipeline_with_empty_name() -> None:
    """Test registering pipeline with empty string name."""
    registry = PipelineRegistry()
    pipeline = Pipeline[int, int, TestContext]()
    registry.register(name="", pipeline=pipeline)
    assert registry.has(name="")


def test_has_after_clear() -> None:
    """Test has returns False after clear."""
    registry = PipelineRegistry()
    pipeline = Pipeline[int, int, TestContext]()
    name = fake.word()
    registry.register(name=name, pipeline=pipeline)
    registry.clear()
    assert registry.has(name=name) is False


def test_get_after_clear_raises_error() -> None:
    """Test get raises error after clear."""
    registry = PipelineRegistry()
    pipeline = Pipeline[int, int, TestContext]()
    name = fake.word()
    registry.register(name=name, pipeline=pipeline)
    registry.clear()
    try:
        registry.get(name=name)
        msg = "Expected ValidationError"
        raise AssertionError(msg)
    except ValidationError:
        pass


def test_register_same_pipeline_multiple_names() -> None:
    """Test registering same pipeline under different names."""
    registry = PipelineRegistry()
    pipeline = Pipeline[int, int, TestContext]()
    name_1 = fake.word()
    name_2 = fake.word()
    registry.register(name=name_1, pipeline=pipeline)
    registry.register(name=name_2, pipeline=pipeline)
    retrieved_1 = registry.get(name=name_1)
    retrieved_2 = registry.get(name=name_2)
    assert retrieved_1 is retrieved_2


def test_register_multiple_times_same_name() -> None:
    """Test count doesn't increase when overwriting."""
    registry = PipelineRegistry()
    pipeline_1 = Pipeline[int, int, TestContext]()
    pipeline_2 = Pipeline[int, int, TestContext]()
    name = fake.word()
    registry.register(name=name, pipeline=pipeline_1)
    assert registry.get_count() == 1
    registry.register(name=name, pipeline=pipeline_2)
    assert registry.get_count() == 1


def test_get_all_names_after_overwrite() -> None:
    """Test get_all_names reflects current state after overwrite."""
    registry = PipelineRegistry()
    pipeline_1 = Pipeline[int, int, TestContext]()
    pipeline_2 = Pipeline[int, int, TestContext]()
    name = fake.word()
    registry.register(name=name, pipeline=pipeline_1)
    registry.register(name=name, pipeline=pipeline_2)
    names = registry.get_all_names()
    assert names.count(name) == 1

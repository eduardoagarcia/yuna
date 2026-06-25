"""Tests for stat interceptor protocol."""

from typing import Any

from faker import Faker

from yuna.modifiers.config import ModifierConfig
from yuna.modifiers.context import ModifierContext
from yuna.modifiers.interceptor import StatInterceptor
from yuna.types.identifiers import EntityID

fake = Faker()


def test_stat_interceptor_protocol_compliance() -> None:
    """Test custom interceptor implements StatInterceptor protocol."""

    def test_interceptor(
        entity_id: EntityID, stat: str, value: float, context: ModifierContext
    ) -> float:
        return value * 2

    interceptor: StatInterceptor = test_interceptor
    assert callable(interceptor)


def test_stat_interceptor_callable() -> None:
    """Test stat interceptor can be called."""
    entity_id = EntityID(fake.uuid4())
    stat_name = fake.word()
    value = fake.pyfloat(min_value=1.0, max_value=100.0)
    config = ModifierConfig()
    ctx = ModifierContext(modifiers=[], config=config)

    def test_interceptor(
        entity_id: EntityID, stat: str, value: float, context: ModifierContext
    ) -> float:
        return value + 10

    interceptor: StatInterceptor = test_interceptor
    result = interceptor(entity_id=entity_id, stat=stat_name, value=value, context=ctx)
    assert result == value + 10


def test_stat_interceptor_receives_correct_parameters() -> None:
    """Test stat interceptor receives correct parameters."""
    entity_id = EntityID(fake.uuid4())
    stat_name = fake.word()
    value = fake.pyfloat(min_value=1.0, max_value=100.0)
    config = ModifierConfig()
    ctx = ModifierContext(modifiers=[], config=config)
    received_params: dict[str, Any] = {}

    def test_interceptor(
        entity_id: EntityID, stat: str, value: float, context: ModifierContext
    ) -> float:
        received_params["entity_id"] = entity_id
        received_params["stat"] = stat
        received_params["value"] = value
        received_params["context"] = context
        return value

    interceptor: StatInterceptor = test_interceptor
    interceptor(entity_id=entity_id, stat=stat_name, value=value, context=ctx)
    assert received_params["entity_id"] == entity_id
    assert received_params["stat"] == stat_name
    assert received_params["value"] == value
    assert received_params["context"] == ctx


def test_stat_interceptor_can_modify_value() -> None:
    """Test stat interceptor can modify value."""
    entity_id = EntityID(fake.uuid4())
    stat_name = fake.word()
    original_value = 50.0
    modified_value = 75.0
    config = ModifierConfig()
    ctx = ModifierContext(modifiers=[], config=config)

    def test_interceptor(
        entity_id: EntityID, stat: str, value: float, context: ModifierContext
    ) -> float:
        return modified_value

    interceptor: StatInterceptor = test_interceptor
    result = interceptor(
        entity_id=entity_id, stat=stat_name, value=original_value, context=ctx
    )
    assert result == modified_value


def test_stat_interceptor_can_nullify_value() -> None:
    """Test stat interceptor can nullify value."""
    entity_id = EntityID(fake.uuid4())
    stat_name = fake.word()
    original_value = fake.pyfloat(min_value=1.0, max_value=100.0)
    config = ModifierConfig()
    ctx = ModifierContext(modifiers=[], config=config)

    def test_interceptor(
        entity_id: EntityID, stat: str, value: float, context: ModifierContext
    ) -> float:
        return 0.0

    interceptor: StatInterceptor = test_interceptor
    result = interceptor(
        entity_id=entity_id, stat=stat_name, value=original_value, context=ctx
    )
    assert result == 0.0


def test_stat_interceptor_can_amplify_value() -> None:
    """Test stat interceptor can amplify value."""
    entity_id = EntityID(fake.uuid4())
    stat_name = fake.word()
    original_value = 10.0
    config = ModifierConfig()
    ctx = ModifierContext(modifiers=[], config=config)

    def test_interceptor(
        entity_id: EntityID, stat: str, value: float, context: ModifierContext
    ) -> float:
        return value * 5

    interceptor: StatInterceptor = test_interceptor
    result = interceptor(
        entity_id=entity_id, stat=stat_name, value=original_value, context=ctx
    )
    assert result == 50.0


def test_stat_interceptor_with_context_access() -> None:
    """Test stat interceptor can access context."""
    entity_id = EntityID(fake.uuid4())
    stat_name = fake.word()
    value = fake.pyfloat(min_value=1.0, max_value=100.0)
    config = ModifierConfig()
    ctx = ModifierContext(modifiers=[], config=config, current_tick=100)

    def test_interceptor(
        entity_id: EntityID, stat: str, value: float, context: ModifierContext
    ) -> float:
        if context.current_tick > 50:
            return value * 2
        return value

    interceptor: StatInterceptor = test_interceptor
    result = interceptor(entity_id=entity_id, stat=stat_name, value=value, context=ctx)
    assert result == value * 2

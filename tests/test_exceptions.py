"""Tests for custom engine exceptions."""

import pytest
from faker import Faker

from yuna.exceptions import (
    ComponentNotFoundError,
    ConfigError,
    ConfigKeyNotFoundError,
    ConfigSchemaError,
    ConfigValidationError,
    EngineError,
    EntityNotFoundError,
    NetworkError,
    SerializationError,
    ServiceNotFoundError,
    StateError,
    ValidationError,
)

fake = Faker()


def test_engine_error_basic() -> None:
    """Test basic EngineError creation."""
    message = fake.sentence()
    error = EngineError(message=message)

    assert str(error) == message
    assert error.message == message
    assert error.context == {}


def test_engine_error_with_context() -> None:
    """Test EngineError with context dict."""
    message = fake.sentence()
    context = {"key1": fake.word(), "key2": fake.word()}

    error = EngineError(message=message, context=context)

    assert error.message == message
    assert error.context == context
    assert "key1" in str(error)
    assert "key2" in str(error)


def test_engine_error_str_with_context() -> None:
    """Test EngineError string representation includes context."""
    error = EngineError(
        message="Test error",
        context={"entity_id": "123", "component": "Position"},
    )

    error_str = str(error)

    assert "Test error" in error_str
    assert "entity_id=123" in error_str
    assert "component=Position" in error_str


def test_engine_error_inheritance() -> None:
    """Test EngineError inherits from Exception."""
    error = EngineError(message="test")

    assert isinstance(error, Exception)


def test_entity_not_found_error_basic() -> None:
    """Test EntityNotFoundError with default message."""
    entity_id = fake.uuid4()

    error = EntityNotFoundError(entity_id=entity_id)

    assert error.entity_id == entity_id
    assert entity_id in str(error)
    assert "Entity not found" in str(error)


def test_entity_not_found_error_custom_message() -> None:
    """Test EntityNotFoundError with custom message."""
    entity_id = fake.uuid4()
    message = fake.sentence()

    error = EntityNotFoundError(entity_id=entity_id, message=message)

    assert error.entity_id == entity_id
    assert error.message == message
    assert message in str(error)


def test_entity_not_found_error_context() -> None:
    """Test EntityNotFoundError has entity_id in context."""
    entity_id = fake.uuid4()

    error = EntityNotFoundError(entity_id=entity_id)

    assert error.context["entity_id"] == entity_id


def test_entity_not_found_error_inheritance() -> None:
    """Test EntityNotFoundError inherits from EngineError."""
    error = EntityNotFoundError(entity_id="test")

    assert isinstance(error, EngineError)
    assert isinstance(error, Exception)


def test_component_not_found_error_without_entity() -> None:
    """Test ComponentNotFoundError without entity_id."""
    component_type = fake.word()

    error = ComponentNotFoundError(component_type=component_type)

    assert error.component_type == component_type
    assert error.entity_id is None
    assert component_type in str(error)
    assert "not registered" in str(error)


def test_component_not_found_error_with_entity() -> None:
    """Test ComponentNotFoundError with entity_id."""
    component_type = fake.word()
    entity_id = fake.uuid4()

    error = ComponentNotFoundError(
        component_type=component_type,
        entity_id=entity_id,
    )

    assert error.component_type == component_type
    assert error.entity_id == entity_id
    assert component_type in str(error)
    assert entity_id in str(error)


def test_component_not_found_error_custom_message() -> None:
    """Test ComponentNotFoundError with custom message."""
    component_type = fake.word()
    entity_id = fake.uuid4()
    message = fake.sentence()

    error = ComponentNotFoundError(
        component_type=component_type,
        entity_id=entity_id,
        message=message,
    )

    assert error.message == message
    assert message in str(error)


def test_component_not_found_error_context() -> None:
    """Test ComponentNotFoundError context includes component_type and entity_id."""
    component_type = fake.word()
    entity_id = fake.uuid4()

    error = ComponentNotFoundError(
        component_type=component_type,
        entity_id=entity_id,
    )

    assert error.context["component_type"] == component_type
    assert error.context["entity_id"] == entity_id


def test_component_not_found_error_inheritance() -> None:
    """Test ComponentNotFoundError inherits from EngineError."""
    error = ComponentNotFoundError(component_type="test")

    assert isinstance(error, EngineError)
    assert isinstance(error, Exception)


def test_service_not_found_error_basic() -> None:
    """Test ServiceNotFoundError with default message."""
    service_name = fake.word()

    error = ServiceNotFoundError(service_name=service_name)

    assert error.service_name == service_name
    assert service_name in str(error)
    assert "not registered" in str(error)


def test_service_not_found_error_custom_message() -> None:
    """Test ServiceNotFoundError with custom message."""
    service_name = fake.word()
    message = fake.sentence()

    error = ServiceNotFoundError(service_name=service_name, message=message)

    assert error.service_name == service_name
    assert error.message == message
    assert message in str(error)


def test_service_not_found_error_context() -> None:
    """Test ServiceNotFoundError has service_name in context."""
    service_name = fake.word()

    error = ServiceNotFoundError(service_name=service_name)

    assert error.context["service_name"] == service_name


def test_service_not_found_error_inheritance() -> None:
    """Test ServiceNotFoundError inherits from EngineError."""
    error = ServiceNotFoundError(service_name="test")

    assert isinstance(error, EngineError)
    assert isinstance(error, Exception)


def test_validation_error_basic() -> None:
    """Test ValidationError with only reason."""
    reason = fake.sentence()

    error = ValidationError(reason=reason)

    assert error.reason == reason
    assert error.field is None
    assert error.value is None
    assert reason in str(error)


def test_validation_error_with_field() -> None:
    """Test ValidationError with field."""
    reason = fake.sentence()
    field = fake.word()

    error = ValidationError(reason=reason, field=field)

    assert error.reason == reason
    assert error.field == field
    assert field in str(error)


def test_validation_error_with_value() -> None:
    """Test ValidationError with value."""
    reason = fake.sentence()
    value = fake.word()

    error = ValidationError(reason=reason, value=value)

    assert error.reason == reason
    assert error.value == value
    assert value in str(error)


def test_validation_error_with_all_fields() -> None:
    """Test ValidationError with all fields."""
    reason = fake.sentence()
    field = fake.word()
    value = fake.word()

    error = ValidationError(reason=reason, field=field, value=value)

    assert error.reason == reason
    assert error.field == field
    assert error.value == value
    assert reason in str(error)
    assert field in str(error)
    assert value in str(error)


def test_validation_error_context() -> None:
    """Test ValidationError context includes field and value."""
    reason = fake.sentence()
    field = fake.word()
    value = fake.word()

    error = ValidationError(reason=reason, field=field, value=value)

    assert error.context["field"] == field
    assert error.context["value"] == value


def test_validation_error_inheritance() -> None:
    """Test ValidationError inherits from EngineError."""
    error = ValidationError(reason="test")

    assert isinstance(error, EngineError)
    assert isinstance(error, Exception)


def test_serialization_error_basic() -> None:
    """Test SerializationError without component_type."""
    operation = fake.word()
    reason = fake.sentence()

    error = SerializationError(operation=operation, reason=reason)

    assert error.operation == operation
    assert error.reason == reason
    assert error.component_type is None
    assert operation in str(error)
    assert reason in str(error)


def test_serialization_error_with_component_type() -> None:
    """Test SerializationError with component_type."""
    operation = fake.word()
    reason = fake.sentence()
    component_type = fake.word()

    error = SerializationError(
        operation=operation,
        reason=reason,
        component_type=component_type,
    )

    assert error.operation == operation
    assert error.reason == reason
    assert error.component_type == component_type
    assert component_type in str(error)


def test_serialization_error_context() -> None:
    """Test SerializationError context includes operation and component_type."""
    operation = fake.word()
    reason = fake.sentence()
    component_type = fake.word()

    error = SerializationError(
        operation=operation,
        reason=reason,
        component_type=component_type,
    )

    assert error.context["operation"] == operation
    assert error.context["component_type"] == component_type


def test_serialization_error_inheritance() -> None:
    """Test SerializationError inherits from EngineError."""
    error = SerializationError(operation="test", reason="test")

    assert isinstance(error, EngineError)
    assert isinstance(error, Exception)


def test_network_error_basic() -> None:
    """Test NetworkError without observer_id."""
    operation = fake.word()
    reason = fake.sentence()

    error = NetworkError(operation=operation, reason=reason)

    assert error.operation == operation
    assert error.reason == reason
    assert error.observer_id is None
    assert operation in str(error)
    assert reason in str(error)


def test_network_error_with_observer() -> None:
    """Test NetworkError with observer_id."""
    operation = fake.word()
    reason = fake.sentence()
    observer_id = fake.uuid4()

    error = NetworkError(
        operation=operation,
        reason=reason,
        observer_id=observer_id,
    )

    assert error.operation == operation
    assert error.reason == reason
    assert error.observer_id == observer_id
    assert observer_id in str(error)


def test_network_error_context() -> None:
    """Test NetworkError context includes operation and observer_id."""
    operation = fake.word()
    reason = fake.sentence()
    observer_id = fake.uuid4()

    error = NetworkError(
        operation=operation,
        reason=reason,
        observer_id=observer_id,
    )

    assert error.context["operation"] == operation
    assert error.context["observer_id"] == observer_id


def test_network_error_inheritance() -> None:
    """Test NetworkError inherits from EngineError."""
    error = NetworkError(operation="test", reason="test")

    assert isinstance(error, EngineError)
    assert isinstance(error, Exception)


def test_state_error_basic() -> None:
    """Test StateError without state."""
    operation = fake.word()
    reason = fake.sentence()

    error = StateError(operation=operation, reason=reason)

    assert error.operation == operation
    assert error.reason == reason
    assert error.state is None
    assert operation in str(error)
    assert reason in str(error)


def test_state_error_with_state() -> None:
    """Test StateError with state."""
    operation = fake.word()
    reason = fake.sentence()
    state = fake.word()

    error = StateError(operation=operation, reason=reason, state=state)

    assert error.operation == operation
    assert error.reason == reason
    assert error.state == state
    assert state in str(error)


def test_state_error_context() -> None:
    """Test StateError context includes operation and state."""
    operation = fake.word()
    reason = fake.sentence()
    state = fake.word()

    error = StateError(operation=operation, reason=reason, state=state)

    assert error.context["operation"] == operation
    assert error.context["state"] == state


def test_state_error_inheritance() -> None:
    """Test StateError inherits from EngineError."""
    error = StateError(operation="test", reason="test")

    assert isinstance(error, EngineError)
    assert isinstance(error, Exception)


def test_all_exceptions_are_catchable_as_engine_error() -> None:
    """Test all custom exceptions can be caught as EngineError."""
    exceptions = [
        EntityNotFoundError(entity_id="test"),
        ComponentNotFoundError(component_type="test"),
        ServiceNotFoundError(service_name="test"),
        ValidationError(reason="test"),
        SerializationError(operation="test", reason="test"),
        NetworkError(operation="test", reason="test"),
        StateError(operation="test", reason="test"),
        ConfigError(message="test"),
        ConfigSchemaError(message="test"),
        ConfigValidationError(reason="test"),
        ConfigKeyNotFoundError(key="test"),
    ]

    for exc in exceptions:
        assert isinstance(exc, EngineError)

        with pytest.raises(EngineError):
            raise exc


def test_exception_can_be_raised_and_caught() -> None:
    """Test exceptions can be raised and caught normally."""

    with pytest.raises(EntityNotFoundError) as exc_info:
        raise EntityNotFoundError(entity_id="test-123")

    assert exc_info.value.entity_id == "test-123"


def test_exception_context_preserved_through_raise() -> None:
    """Test exception context is preserved when raised."""
    entity_id = fake.uuid4()

    with pytest.raises(EntityNotFoundError) as exc_info:
        raise EntityNotFoundError(entity_id=entity_id, message="Custom message")

    assert exc_info.value.entity_id == entity_id
    assert exc_info.value.message == "Custom message"
    assert exc_info.value.context["entity_id"] == entity_id


def test_config_error_basic() -> None:
    """Test basic ConfigError creation."""
    message = fake.sentence()
    error = ConfigError(message=message)

    assert str(error) == message
    assert error.message == message
    assert error.context == {}


def test_config_error_with_context() -> None:
    """Test ConfigError with context dict."""
    message = fake.sentence()
    context = {"key": fake.word()}

    error = ConfigError(message=message, context=context)

    assert error.message == message
    assert error.context == context
    assert "key" in str(error)


def test_config_error_inheritance() -> None:
    """Test ConfigError inherits from EngineError."""
    error = ConfigError(message="test")

    assert isinstance(error, EngineError)
    assert isinstance(error, Exception)


def test_config_schema_error_basic() -> None:
    """Test basic ConfigSchemaError creation."""
    message = fake.sentence()
    error = ConfigSchemaError(message=message)

    assert str(error) == message
    assert error.message == message


def test_config_schema_error_inheritance() -> None:
    """Test ConfigSchemaError inherits from ConfigError."""
    error = ConfigSchemaError(message="test")

    assert isinstance(error, ConfigError)
    assert isinstance(error, EngineError)
    assert isinstance(error, Exception)


def test_config_validation_error_basic() -> None:
    """Test ConfigValidationError with only reason."""
    reason = fake.sentence()

    error = ConfigValidationError(reason=reason)

    assert error.reason == reason
    assert error.field is None
    assert error.value is None
    assert reason in str(error)


def test_config_validation_error_with_field() -> None:
    """Test ConfigValidationError with field."""
    reason = fake.sentence()
    field = f"{fake.word()}.{fake.word()}"

    error = ConfigValidationError(reason=reason, field=field)

    assert error.reason == reason
    assert error.field == field
    assert field in str(error)


def test_config_validation_error_with_value() -> None:
    """Test ConfigValidationError with value."""
    reason = fake.sentence()
    value = str(fake.random_int())

    error = ConfigValidationError(reason=reason, value=value)

    assert error.reason == reason
    assert error.value == value
    assert value in str(error)


def test_config_validation_error_with_all_fields() -> None:
    """Test ConfigValidationError with all fields."""
    reason = fake.sentence()
    field = f"{fake.word()}.{fake.word()}"
    value = str(fake.random_int())

    error = ConfigValidationError(reason=reason, field=field, value=value)

    assert error.reason == reason
    assert error.field == field
    assert error.value == value
    assert reason in str(error)
    assert field in str(error)
    assert value in str(error)


def test_config_validation_error_context() -> None:
    """Test ConfigValidationError context includes field and value."""
    reason = fake.sentence()
    field = f"{fake.word()}.{fake.word()}"
    value = str(fake.random_int())

    error = ConfigValidationError(reason=reason, field=field, value=value)

    assert error.context["field"] == field
    assert error.context["value"] == value


def test_config_validation_error_inheritance() -> None:
    """Test ConfigValidationError inherits from ConfigError."""
    error = ConfigValidationError(reason="test")

    assert isinstance(error, ConfigError)
    assert isinstance(error, EngineError)
    assert isinstance(error, Exception)


def test_config_key_not_found_error_basic() -> None:
    """Test ConfigKeyNotFoundError with default message."""
    key = f"{fake.word()}.{fake.word()}"

    error = ConfigKeyNotFoundError(key=key)

    assert error.key == key
    assert key in str(error)
    assert "not registered" in str(error)


def test_config_key_not_found_error_custom_message() -> None:
    """Test ConfigKeyNotFoundError with custom message."""
    key = f"{fake.word()}.{fake.word()}"
    message = fake.sentence()

    error = ConfigKeyNotFoundError(key=key, message=message)

    assert error.key == key
    assert error.message == message
    assert message in str(error)


def test_config_key_not_found_error_context() -> None:
    """Test ConfigKeyNotFoundError has key in context."""
    key = f"{fake.word()}.{fake.word()}"

    error = ConfigKeyNotFoundError(key=key)

    assert error.context["key"] == key


def test_config_key_not_found_error_inheritance() -> None:
    """Test ConfigKeyNotFoundError inherits from ConfigError."""
    error = ConfigKeyNotFoundError(key="test")

    assert isinstance(error, ConfigError)
    assert isinstance(error, EngineError)
    assert isinstance(error, Exception)


def test_all_config_exceptions_are_catchable_as_config_error() -> None:
    """Test all config exceptions can be caught as ConfigError."""
    exceptions = [
        ConfigError(message="test"),
        ConfigSchemaError(message="test"),
        ConfigValidationError(reason="test"),
        ConfigKeyNotFoundError(key="test"),
    ]

    for exc in exceptions:
        assert isinstance(exc, ConfigError)

        with pytest.raises(ConfigError):
            raise exc

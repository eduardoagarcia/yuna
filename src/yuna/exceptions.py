"""Custom exception hierarchy for the game engine.

This module defines a hierarchy of exceptions used throughout the engine
to provide clear, consistent error handling.

Exception Hierarchy:
    EngineError (base)
    ├── EntityNotFoundError
    ├── ComponentNotFoundError
    ├── ServiceNotFoundError
    ├── ValidationError
    ├── SerializationError
    ├── NetworkError
    ├── StateError
    ├── ConfigError
    │   ├── ConfigSchemaError
    │   ├── ConfigValidationError
    │   └── ConfigKeyNotFoundError

Usage Guidelines:
    - Lookup operations: Return None for expected misses
    - Validation operations: Return (bool, reason) tuple
    - State mutations: Raise exceptions for invalid state
    - Always provide helpful error messages with context
"""

from __future__ import annotations


class EngineError(Exception):
    """Base exception for all engine errors.

    All custom engine exceptions should inherit from this class.
    This allows callers to catch all engine-specific errors with a
    single except clause if needed.

    Attributes:
        message: Human-readable error description
        context: Optional dictionary with additional error context

    Usage:
        raise EngineError("Something went wrong")
        raise EngineError("Error occurred", context={"entity_id": "123"})
    """

    def __init__(self, message: str, context: dict[str, str] | None = None) -> None:
        """Initialize engine error.

        Args:
            message: Human-readable error description
            context: Optional dictionary with additional error context
        """
        self.message = message
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation of error."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message


class EntityNotFoundError(EngineError):
    """Raised when an entity does not exist.

    This error indicates that an operation was attempted on an entity
    that doesn't exist in the world. This is typically a programming
    error or invalid game state.

    Usage:
        raise EntityNotFoundError(
            entity_id="player-123",
            message="Cannot update position for non-existent entity",
        )
    """

    def __init__(self, entity_id: str, message: str | None = None) -> None:
        """Initialize entity not found error.

        Args:
            entity_id: ID of the entity that was not found
            message: Optional custom error message
        """
        default_message = f"Entity not found: {entity_id}"
        super().__init__(
            message=message or default_message,
            context={"entity_id": entity_id},
        )
        self.entity_id = entity_id


class ComponentNotFoundError(EngineError):
    """Raised when a component does not exist.

    This error indicates that an operation was attempted on a component
    that either doesn't exist on an entity, or a component type that
    isn't registered with the engine.

    Usage:
        raise ComponentNotFoundError(
            component_type="Position",
            entity_id="player-123",
            message="Entity does not have Position component",
        )
    """

    def __init__(
        self,
        component_type: str,
        entity_id: str | None = None,
        message: str | None = None,
    ) -> None:
        """Initialize component not found error.

        Args:
            component_type: Type of component that was not found
            entity_id: Optional ID of entity that doesn't have the component
            message: Optional custom error message
        """
        if entity_id:
            default_message = (
                f"Component {component_type} not found on entity {entity_id}"
            )
            context = {"component_type": component_type, "entity_id": entity_id}
        else:
            default_message = f"Component type not registered: {component_type}"
            context = {"component_type": component_type}

        super().__init__(
            message=message or default_message,
            context=context,
        )
        self.component_type = component_type
        self.entity_id = entity_id


class ServiceNotFoundError(EngineError):
    """Raised when a service is not registered.

    This error indicates that an operation was attempted on a service
    that hasn't been registered with the engine. This is typically a
    configuration or initialization error.

    Usage:
        raise ServiceNotFoundError(
            service_name="PhysicsService",
            message="Physics service must be registered before use",
        )
    """

    def __init__(self, service_name: str, message: str | None = None) -> None:
        """Initialize service not found error.

        Args:
            service_name: Name of the service that was not found
            message: Optional custom error message
        """
        default_message = f"Service not registered: {service_name}"
        super().__init__(
            message=message or default_message,
            context={"service_name": service_name},
        )
        self.service_name = service_name


class ValidationError(EngineError):
    """Raised when command or data validation fails.

    This error indicates that input data, commands, or parameters
    failed validation checks. This is typically user error or invalid
    client input.

    Usage:
        raise ValidationError(
            field="position",
            reason="Position must be within world bounds",
            value="(-100, -100)",
        )
    """

    def __init__(
        self,
        reason: str,
        field: str | None = None,
        value: str | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            reason: Human-readable explanation of why validation failed
            field: Optional name of field that failed validation
            value: Optional string representation of invalid value
        """
        context: dict[str, str] = {}
        if field:
            context["field"] = field
        if value:
            context["value"] = value

        super().__init__(message=reason, context=context)
        self.reason = reason
        self.field = field
        self.value = value


class SerializationError(EngineError):
    """Raised when serialization or deserialization fails.

    This error indicates that converting data to/from a serialized
    format (JSON, binary, etc.) failed. This could be due to invalid
    data format, missing serializers, or version incompatibility.

    Usage:
        raise SerializationError(
            operation="deserialize",
            component_type="Position",
            reason="Missing required field 'x'",
        )
    """

    def __init__(
        self,
        operation: str,
        reason: str,
        component_type: str | None = None,
    ) -> None:
        """Initialize serialization error.

        Args:
            operation: Operation that failed (serialize/deserialize)
            reason: Human-readable explanation of failure
            component_type: Optional component type being serialized
        """
        context = {"operation": operation}
        if component_type:
            context["component_type"] = component_type

        super().__init__(message=reason, context=context)
        self.operation = operation
        self.reason = reason
        self.component_type = component_type


class NetworkError(EngineError):
    """Raised when network operations fail.

    This error indicates that a network-related operation failed,
    such as replication, interest management, or message delivery.

    Usage:
        raise NetworkError(
            operation="replicate",
            reason="Observer not registered",
            observer_id="client-123",
        )
    """

    def __init__(
        self,
        operation: str,
        reason: str,
        observer_id: str | None = None,
    ) -> None:
        """Initialize network error.

        Args:
            operation: Network operation that failed
            reason: Human-readable explanation of failure
            observer_id: Optional ID of observer/client involved
        """
        context = {"operation": operation}
        if observer_id:
            context["observer_id"] = observer_id

        super().__init__(message=reason, context=context)
        self.operation = operation
        self.reason = reason
        self.observer_id = observer_id


class StateError(EngineError):
    """Raised when invalid state transition is attempted.

    This error indicates that an operation would result in invalid
    game state, such as adding a component that already exists or
    transitioning to an invalid state.

    Usage:
        raise StateError(
            state="running",
            operation="start",
            reason="Cannot start engine that is already running",
        )
    """

    def __init__(
        self,
        operation: str,
        reason: str,
        state: str | None = None,
    ) -> None:
        """Initialize state error.

        Args:
            operation: Operation that caused invalid state
            reason: Human-readable explanation of why state is invalid
            state: Optional current state when error occurred
        """
        context = {"operation": operation}
        if state:
            context["state"] = state

        super().__init__(message=reason, context=context)
        self.operation = operation
        self.reason = reason
        self.state = state


class WorldWriteProtectionError(StateError):
    """Raised when a write-protected section is violated.

    During a write-protected section the executing thread may only write
    to its designated owner entity. Writes to any other entity, or
    entity-less structural writes, raise this error so the violation
    surfaces immediately at its origin instead of producing
    order-dependent state.

    Usage:
        raise WorldWriteProtectionError(owner="entity-a", target="entity-b")
    """

    def __init__(
        self,
        owner: str | None,
        target: str | None,
    ) -> None:
        """Initialize write-protection error.

        Args:
            owner: Entity the current thread is permitted to write
            target: Entity the blocked write targeted
        """
        super().__init__(
            operation="write_protected_section",
            reason=(
                "Write to a non-owner or structural target during a "
                "write-protected section"
            ),
            state=f"owner={owner} target={target}",
        )
        self.owner = owner
        self.target = target


class ConfigError(EngineError):
    """Raised when configuration operation fails.

    This error is the base class for all configuration-related errors.
    It indicates issues with config schema, validation, or access.

    Usage:
        raise ConfigError("Configuration error occurred")
    """

    pass


class ConfigSchemaError(ConfigError):
    """Raised when config schema definition is invalid.

    This error indicates that a config key registration or schema
    operation failed due to invalid schema definition.

    Usage:
        raise ConfigSchemaError(
            message="Config key already registered",
            context={"key": "cache.size"},
        )
    """

    pass


class ConfigValidationError(ConfigError):
    """Raised when config value validation fails.

    This error indicates that a config value failed validation
    against its constraints (min/max, type, custom validators).

    Usage:
        raise ConfigValidationError(
            reason="Value exceeds maximum",
            field="cache.size",
            value="9999",
        )
    """

    def __init__(
        self,
        reason: str,
        field: str | None = None,
        value: str | None = None,
    ) -> None:
        """Initialize config validation error.

        Args:
            reason: Human-readable explanation of validation failure
            field: Optional config key that failed validation
            value: Optional string representation of invalid value
        """
        context: dict[str, str] = {}
        if field:
            context["field"] = field
        if value:
            context["value"] = value

        super().__init__(message=reason, context=context)
        self.reason = reason
        self.field = field
        self.value = value


class ConfigKeyNotFoundError(ConfigError):
    """Raised when config key does not exist in schema.

    This error indicates that an operation was attempted on a config
    key that hasn't been registered in the schema.

    Usage:
        raise ConfigKeyNotFoundError(
            key="unknown.setting",
            message="Config key not registered",
        )
    """

    def __init__(self, key: str, message: str | None = None) -> None:
        """Initialize config key not found error.

        Args:
            key: Config key that was not found
            message: Optional custom error message
        """
        default_message = f"Config key not registered: {key}"
        super().__init__(
            message=message or default_message,
            context={"key": key},
        )
        self.key = key

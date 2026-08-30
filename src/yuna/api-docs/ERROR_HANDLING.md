# Error Handling Guidelines

This document defines consistent error handling patterns for the game engine.

## Philosophy

The engine uses a consistent approach to error handling based on the type of operation:

1. **Lookup Operations**: Return `None` for expected misses
2. **Validation Operations**: Return `(bool, reason)` tuple for validation results
3. **State Mutations**: Raise exceptions for invalid state or unexpected errors

## Exception Hierarchy

```
EngineError (base exception)
├── EntityNotFoundError       - Entity doesn't exist
├── ComponentNotFoundError    - Component doesn't exist
├── ServiceNotFoundError      - Service not registered
├── ValidationError           - Command/data validation failed
├── SerializationError        - Serialization/deserialization failed
├── NetworkError              - Network operation failed
└── StateError                - Invalid state transition
```

## When to Use Each Exception

### EngineError

Base exception for all engine errors. Use directly only when no specific subclass fits.

**When to use:**
- Generic engine errors that don't fit other categories
- As a catch-all in exception handlers

**Example:**
```python
try:
    result = some_complex_operation()
except EngineError as e:
    # Handle any engine error
    logger.error(f"Engine error: {e}")
```

### EntityNotFoundError

Raised when an operation is attempted on a non-existent entity.

**When to use:**
- Attempting to modify entity that doesn't exist
- Querying components on deleted entity
- Invalid entity references in commands

**When NOT to use:**
- Optional entity lookups (return None instead)
- Entity existence checks (return bool instead)

**Example:**
```python
def update_position(entity_id: EntityID, position: Position) -> None:
    if not world.has_entity(entity_id):
        raise EntityNotFoundError(
            entity_id=str(entity_id),
            message="Cannot update position for non-existent entity"
        )

    world.set_position(entity_id=entity_id, position=position)
```

**Counter-example (use None instead):**
```python
def get_entity(entity_id: EntityID) -> Entity | None:
    # Return None for expected misses
    return entities.get(entity_id)
```

### ComponentNotFoundError

Raised when a component doesn't exist on an entity or a component type isn't registered.

**When to use:**
- Required component is missing on entity
- Component type not registered with serializer
- Invalid component type reference

**When NOT to use:**
- Optional component queries (return None instead)
- Component existence checks (return bool instead)

**Example:**
```python
def serialize_component(component_type: str, component: Any) -> dict:
    if component_type not in serializers:
        raise ComponentNotFoundError(
            component_type=component_type,
            message=f"No serializer registered for {component_type}"
        )

    return serializers[component_type].to_dict(component)
```

**Counter-example (use None instead):**
```python
def get_component(entity_id: EntityID, component_type: str) -> Any | None:
    # Return None for expected misses
    return components.get((entity_id, component_type))
```

### ServiceNotFoundError

Raised when attempting to use a service that hasn't been registered.

**When to use:**
- Service lookup fails during initialization
- Required service missing from registry
- Invalid service name reference

**Example:**
```python
def get_service(service_name: str) -> Service:
    if service_name not in services:
        raise ServiceNotFoundError(
            service_name=service_name,
            message=f"Service {service_name} must be registered before use"
        )

    return services[service_name]
```

### ValidationError

Raised when input data, commands, or parameters fail validation.

**When to use:**
- Invalid command parameters
- Data violates constraints
- Type validation failures
- Range/boundary violations

**When NOT to use:**
- For validation results in validation functions (return tuple instead)

**Example:**
```python
def move_entity(entity_id: EntityID, target: Position) -> None:
    if not world.is_valid_position(target):
        raise ValidationError(
            field="target",
            reason="Target position is outside world bounds",
            value=f"({target.x}, {target.y})"
        )

    world.set_position(entity_id=entity_id, position=target)
```

**For validation functions, return tuple instead:**
```python
def validate_position(position: Position) -> tuple[bool, str]:
    if position.x < 0 or position.x > world.width:
        return False, "X coordinate outside world bounds"
    if position.y < 0 or position.y > world.height:
        return False, "Y coordinate outside world bounds"
    return (True,
```

### SerializationError

Raised when serialization or deserialization operations fail.

**When to use:**
- Missing required fields in data
- Invalid data format
- Type conversion failures
- Version incompatibility

**Example:**
```python
def deserialize_position(data: dict) -> Position:
    if "x" not in data or "y" not in data:
        raise SerializationError(
            operation="deserialize",
            component_type="Position",
            reason="Missing required fields 'x' and 'y'"
        )

    try:
        return Position(x=float(data["x"]), y=float(data["y"]))
    except (ValueError, TypeError) as e:
        raise SerializationError(
            operation="deserialize",
            component_type="Position",
            reason=f"Invalid data types: {e}"
        )
```

### NetworkError

Raised when network operations fail.

**When to use:**
- Observer/client not registered
- Replication failures
- Interest management errors
- Message delivery failures

**Example:**
```python
def replicate_to_observer(observer_id: str, entities: list[Entity]) -> None:
    if observer_id not in observers:
        raise NetworkError(
            operation="replicate",
            reason="Observer not registered",
            observer_id=observer_id
        )

    observers[observer_id].send(entities)
```

### StateError

Raised when attempting an invalid state transition.

**When to use:**
- Operation not allowed in current state
- Duplicate registration/initialization
- Invalid state transitions
- Resource already exists/missing

**Example:**
```python
def start_engine() -> None:
    if engine.is_running:
        raise StateError(
            operation="start",
            state="running",
            reason="Cannot start engine that is already running"
        )

    engine.is_running = True
```

## Error Handling Patterns

### Pattern 1: Lookup Operations

Return `None` for expected misses:

```python
def get_entity(entity_id: EntityID) -> Entity | None:
    return entities.get(entity_id)

def get_component(entity_id: EntityID, component_type: str) -> Any | None:
    return components.get((entity_id, component_type))
```

### Pattern 2: Validation Operations

Return `(bool, reason)` tuple:

```python
def validate_command(command: Command) -> tuple[bool, str]:
    if not command.entity_id:
        return False, "Entity ID is required"

    if not world.has_entity(command.entity_id):
        return False, f"Entity {command.entity_id} does not exist"

    return True, ""

# Usage
is_valid, reason = validate_command(command)
if not is_valid:
    logger.warning(f"Invalid command: {reason}")

```

### Pattern 3: State Mutations

Raise exceptions for invalid state:

```python
def add_component(entity_id: EntityID, component: Component) -> None:
    if not world.has_entity(entity_id):
        raise EntityNotFoundError(
            entity_id=str(entity_id),
            message="Cannot add component to non-existent entity"
        )

    if world.has_component(entity_id=entity_id, component_type=type(component).__name__):
        raise StateError(
            operation="add_component",
            reason=f"Entity {entity_id} already has {type(component).__name__} component"
        )

    world.components[(entity_id, type(component).__name__)] = component
```

### Pattern 4: Error Context

Always provide helpful context:

```python
# Good: Provides context about what failed and why
raise ValidationError(
    field="position",
    reason="Position must be within world bounds (0-100, 0-100)",
    value=f"({pos.x}, {pos.y})"
)

# Bad: Vague error message
raise ValidationError(reason="Invalid position")
```

### Pattern 5: Error Propagation

Let exceptions bubble up, catch at appropriate level:

```python
# Low-level function: raise specific exception
def deserialize_component(data: dict) -> Component:
    if "type" not in data:
        raise SerializationError(
            operation="deserialize",
            reason="Missing required field 'type'"
        )
    return Component(**data)

# Mid-level function: let it propagate
def load_entity(data: dict) -> Entity:
    entity = Entity(id=data["id"])
    for comp_data in data["components"]:
        # Let SerializationError propagate
        component = deserialize_component(comp_data)
        entity.add_component(component)
    return entity

# High-level function: catch and handle
def load_world(path: str) -> World:
    try:
        data = load_file(path)
        entities = [load_entity(e) for e in data["entities"]]
        return World(entities=entities)
    except SerializationError as e:
        logger.error(f"Failed to load world: {e}")
        return World.empty()
    except EngineError as e:
        logger.error(f"Engine error loading world: {e}")
        raise
```

## Logging Recommendations

### Log Levels

- **DEBUG**: Validation failures, expected errors, recoverable issues
- **INFO**: State changes, successful operations
- **WARNING**: Unexpected but handled errors, degraded functionality
- **ERROR**: Exceptions that prevent operation completion
- **CRITICAL**: Fatal errors that require shutdown

### Logging Exceptions

```python
import logging

logger = logging.getLogger(__name__)

# Log validation errors at DEBUG level
try:
    validate_command(command)
except ValidationError as e:
    logger.debug(f"Command validation failed: {e}")

# Log state errors at WARNING level
try:
    add_component(entity_id, component)
except StateError as e:
    logger.warning(f"Invalid state transition: {e}")

# Log unexpected errors at ERROR level
try:
    process_tick()
except EngineError as e:
    logger.error(f"Error processing tick: {e}", exc_info=True)

# Log critical errors at CRITICAL level
try:
    initialize_engine()
except EngineError as e:
    logger.critical(f"Failed to initialize engine: {e}", exc_info=True)
    raise
```

## Testing Exceptions

Test that exceptions are raised correctly:

```python
def test_entity_not_found_raises_error():
    world = World()
    entity_id = EntityID("non-existent")

    with pytest.raises(EntityNotFoundError) as exc_info:
        world.get_component(entity_id=entity_id, component_type="Position")

    assert exc_info.value.entity_id == str(entity_id)
    assert "non-existent" in str(exc_info.value)

def test_validation_error_has_context():
    with pytest.raises(ValidationError) as exc_info:
        validate_position(Position(x=-10, y=20))

    assert exc_info.value.field == "x"
    assert "bounds" in exc_info.value.reason.lower()
```

## Summary

- **Lookup operations**: Return `None`
- **Validation operations**: Return `(bool, reason)`
- **State mutations**: Raise exceptions
- **Always provide context**: Include relevant IDs, values, and reasons
- **Log appropriately**: Match log level to severity
- **Test exceptions**: Verify they're raised with correct context

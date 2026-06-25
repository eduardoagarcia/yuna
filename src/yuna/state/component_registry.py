"""Component serialization registry for type-safe serialization."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from yuna.exceptions import ValidationError
from yuna.state.versioning import (
    extract_version_from_data,
    get_component_instance_version,
)

ComponentSerializer = Callable[[Any], dict[str, Any]]
ComponentDeserializer = Callable[[dict[str, Any]], Any]


class ComponentSerializerRegistry:
    """Centralized registry for component serialization.

    Responsibilities:
    - Register component serializers and deserializers
    - Provide type-safe serialization
    - Validate component schemas
    - Auto-registration via decorator

    Usage:
        registry = ComponentSerializerRegistry()

        @registry.register("Position")
        class PositionSerializer:
            @staticmethod
            def to_dict(component: Position) -> dict[str, Any]:
                return {"x": component.x, "y": component.y}

            @staticmethod
            def from_dict(data: dict[str, Any]) -> Position:
                return Position(x=data["x"], y=data["y"])

        data = registry.serialize_component(component_type="Position", component=pos)
        pos = registry.deserialize_component(component_type="Position", data=data)
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._serializers: dict[str, ComponentSerializer] = {}
        self._deserializers: dict[str, ComponentDeserializer] = {}

    def register_serializer(
        self,
        component_type: str,
        to_dict: ComponentSerializer,
        from_dict: ComponentDeserializer,
    ) -> None:
        """Register a component serializer.

        Args:
            component_type: Name of component type
            to_dict: Function to serialize component to dict
            from_dict: Function to deserialize dict to component

        Raises:
            ValidationError: If component type already registered
        """
        if component_type in self._serializers:
            raise ValidationError(
                field="component_type",
                value=component_type,
                reason="Serializer already registered for this component type",
            )

        self._serializers[component_type] = to_dict
        self._deserializers[component_type] = from_dict

    def unregister_serializer(self, component_type: str) -> None:
        """Unregister a component serializer.

        Args:
            component_type: Name of component type to unregister

        Raises:
            ValidationError: If component type not registered
        """
        if component_type not in self._serializers:
            raise ValidationError(
                field="component_type",
                value=component_type,
                reason="No serializer registered for this component type",
            )

        del self._serializers[component_type]
        del self._deserializers[component_type]

    def is_registered(self, component_type: str) -> bool:
        """Check if component type has registered serializer.

        Args:
            component_type: Name of component type

        Returns:
            True if serializer is registered
        """
        return component_type in self._serializers

    def serialize_component(
        self,
        component_type: str,
        component: Any,
    ) -> dict[str, Any]:
        """Serialize component using registered serializer.

        Args:
            component_type: Name of component type
            component: Component instance to serialize

        Returns:
            Serialized component data with version field

        Raises:
            ValidationError: If no serializer registered for component type
        """
        if component_type not in self._serializers:
            raise ValidationError(
                field="component_type",
                value=component_type,
                reason="No serializer registered for this component type",
            )

        data = self._serializers[component_type](component)
        version = get_component_instance_version(component=component)
        return {"__version__": version, **data}

    def deserialize_component(
        self,
        component_type: str,
        data: dict[str, Any],
    ) -> Any:
        """Deserialize component using registered deserializer.

        Args:
            component_type: Name of component type
            data: Serialized component data with optional version field

        Returns:
            Deserialized component instance

        Raises:
            ValidationError: If no deserializer registered for component type
        """
        if component_type not in self._deserializers:
            raise ValidationError(
                field="component_type",
                value=component_type,
                reason="No deserializer registered for this component type",
            )

        _, clean_data = extract_version_from_data(data=data)
        return self._deserializers[component_type](clean_data)

    def get_registered_types(self) -> list[str]:
        """Get list of all registered component types.

        Returns:
            List of component type names
        """
        return sorted(self._serializers.keys())

    def register(
        self,
        component_type: str,
    ) -> Callable[[type], type]:
        """Decorator for auto-registration of component serializers.

        The decorated class must have static methods to_dict and from_dict.

        Args:
            component_type: Name of component type

        Returns:
            Decorator function

        Usage:
            @registry.register("Position")
            class PositionSerializer:
                @staticmethod
                def to_dict(component: Position) -> dict[str, Any]:
                    return {"x": component.x, "y": component.y}

                @staticmethod
                def from_dict(data: dict[str, Any]) -> Position:
                    return Position(x=data["x"], y=data["y"])
        """

        def decorator(cls: type) -> type:
            to_dict_method = getattr(cls, "to_dict", None)
            from_dict_method = getattr(cls, "from_dict", None)

            if to_dict_method is None:
                raise ValidationError(
                    field="to_dict",
                    value=cls.__name__,
                    reason="Serializer class must have to_dict method",
                )
            if from_dict_method is None:
                raise ValidationError(
                    field="from_dict",
                    value=cls.__name__,
                    reason="Serializer class must have from_dict method",
                )

            self.register_serializer(
                component_type=component_type,
                to_dict=to_dict_method,
                from_dict=from_dict_method,
            )
            return cls

        return decorator

"""Built-in component serializers for common types."""

from __future__ import annotations

from dataclasses import asdict, fields, is_dataclass
from typing import Any

from yuna.exceptions import SerializationError
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2


class Vector2Serializer:
    """Serializer for Vector2 components."""

    @staticmethod
    def to_dict(component: Vector2) -> dict[str, Any]:
        """Serialize Vector2 to dictionary.

        Args:
            component: Vector2 instance

        Returns:
            Dictionary with x and y keys
        """
        return {"x": component.x, "y": component.y}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Vector2:
        """Deserialize Vector2 from dictionary.

        Args:
            data: Dictionary with x and y keys

        Returns:
            Vector2 instance
        """
        return Vector2(x=data["x"], y=data["y"])


class EntityIDSerializer:
    """Serializer for EntityID components."""

    @staticmethod
    def to_dict(component: EntityID) -> dict[str, Any]:
        """Serialize EntityID to dictionary.

        Args:
            component: EntityID instance

        Returns:
            Dictionary with id key
        """
        return {"id": str(component)}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> EntityID:
        """Deserialize EntityID from dictionary.

        Args:
            data: Dictionary with id key

        Returns:
            EntityID instance
        """
        return EntityID(data["id"])


class GenericDataclassSerializer:
    """Generic fallback serializer for dataclass components.

    Automatically serializes any dataclass by converting fields to dict.
    This is used as a fallback when no specific serializer is registered.
    """

    @staticmethod
    def to_dict(component: Any) -> dict[str, Any]:
        """Serialize dataclass to dictionary.

        Args:
            component: Dataclass instance

        Returns:
            Dictionary representation

        Raises:
            SerializationError: If component is not a dataclass
        """
        if not is_dataclass(obj=component):
            raise SerializationError(
                operation="serialize",
                component_type=type(component).__name__,
                reason="Component must be a dataclass",
            )
        return asdict(obj=component)  # type: ignore[arg-type]

    @staticmethod
    def from_dict(component_type: Any, data: dict[str, Any]) -> Any:
        """Deserialize dataclass from dictionary.

        Args:
            component_type: Dataclass type to create
            data: Dictionary data

        Returns:
            Dataclass instance

        Raises:
            SerializationError: If component_type is not a dataclass
        """
        if not is_dataclass(obj=component_type):
            raise SerializationError(
                operation="deserialize",
                component_type=component_type.__name__,
                reason="Component type must be a dataclass",
            )

        field_names = {f.name for f in fields(component_type)}
        filtered_data = {
            key: value for key, value in data.items() if key in field_names
        }
        return component_type(**filtered_data)  # type: ignore[operator]

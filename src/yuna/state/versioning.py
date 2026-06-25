"""Component versioning for save file compatibility."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VersionedComponent:
    """Base class for versioned components.

    Components that extend this class will have automatic version tracking
    in serialized data, enabling backward compatibility when component
    schemas change.

    Attributes:
        __version__: Component schema version number

    Usage:
        @dataclass
        class Position(VersionedComponent):
            x: float
            y: float
            __version__ = 1
    """

    __version__: int = field(default=1, init=False, repr=False, compare=False)


def version(version_number: int) -> Callable[[type], type]:
    """Decorator to set component version.

    Args:
        version_number: Version number for this component schema

    Returns:
        Decorator function

    Usage:
        @version(2)
        @dataclass
        class Position:
            x: float
            y: float
            z: float
    """

    def decorator(cls: type) -> type:
        cls.__version__ = version_number  # type: ignore[attr-defined]
        return cls

    return decorator


def get_component_version(component_type: type) -> int:
    """Get version number of a component type.

    Args:
        component_type: Component class to check

    Returns:
        Version number, or 1 if not versioned

    Usage:
        version = get_component_version(Position)
    """
    return getattr(component_type, "__version__", 1)


def get_component_instance_version(component: Any) -> int:
    """Get version number from a component instance.

    Args:
        component: Component instance to check

    Returns:
        Version number, or 1 if not versioned

    Usage:
        version = get_component_instance_version(position)
    """
    return getattr(type(component), "__version__", 1)


def add_version_to_data(
    component_type: type,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Add version field to serialized component data.

    Args:
        component_type: Component class
        data: Serialized component data

    Returns:
        Data dict with __version__ field added

    Usage:
        data = add_version_to_data(Position, {"x": 1.0, "y": 2.0})
    """
    version_num = get_component_version(component_type=component_type)
    return {"__version__": version_num, **data}


def extract_version_from_data(data: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Extract version field from serialized data.

    Args:
        data: Serialized component data

    Returns:
        Tuple of (version_number, data_without_version)

    Usage:
        version, clean_data = extract_version_from_data(data)
    """
    version_num = data.get("__version__", 1)
    clean_data = {k: v for k, v in data.items() if k != "__version__"}
    return version_num, clean_data

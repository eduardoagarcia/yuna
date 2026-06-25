"""Base component protocol for ECS components."""

from typing import Protocol


class Component(Protocol):
    """Protocol defining the interface for ECS components.

    Components are pure data containers with no behavior.
    They should be implemented as dataclasses or simple classes
    containing only data fields.

    Responsibilities:
    - Store entity data
    - Provide type identity for component queries

    Usage:
        @dataclass
        class Position(Component):
            x: float
            y: float

        @dataclass
        class Health(Component):
            current: int
            maximum: int
    """

    ...  # pragma: no cover

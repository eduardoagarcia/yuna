"""Service lifetime management enumerations."""

from enum import Enum


class ServiceLifetime(Enum):
    """Defines the lifetime scope of a registered service.

    SINGLETON: Single instance shared across entire application
    PER_WORLD: New instance created per game world
    TRANSIENT: New instance created on every resolve call
    """

    SINGLETON = "singleton"
    PER_WORLD = "per_world"
    TRANSIENT = "transient"

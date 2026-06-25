"""Type-safe identifiers for ECS entities, components, and systems."""

from typing import NewType

EntityID = NewType("EntityID", str)
ComponentID = NewType("ComponentID", str)
SystemID = NewType("SystemID", str)

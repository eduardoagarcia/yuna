"""Double-buffered component storage for parallel processing."""

from __future__ import annotations

from threading import Lock
from typing import TypeVar

from yuna.ecs.component import Component
from yuna.ecs.store import ComponentStore
from yuna.types.identifiers import EntityID

T = TypeVar("T", bound=Component)


class DoubleBufferedStore:
    """Double-buffered component store with read/write separation.

    Responsibilities:
    - Provide read-only access to current state
    - Provide write-only access to next state
    - Atomically swap buffers between frames
    - Enable parallel system processing without race conditions

    The double buffer pattern allows systems to read from a stable state
    while writing to a separate buffer. After all systems complete,
    the buffers are swapped atomically.

    Usage:
        store = DoubleBufferedStore()

        # Systems read from current state
        position = store.read(entity_id=entity1, component_type=Position)

        # Systems write to next state
        store.write(
            entity_id=entity1,
            component_type=Position,
            component=Position(x=10, y=20)
        )

        # After all systems complete, swap buffers
        store.swap()
    """

    def __init__(self) -> None:
        self._read_buffer = ComponentStore()
        self._write_buffer = ComponentStore()
        self._swap_lock = Lock()

    def read(self, entity_id: EntityID, component_type: type[T]) -> T | None:
        """Read component from current state (read buffer).

        Args:
            entity_id: Entity to read from
            component_type: Type of component to read

        Returns:
            Component instance or None if not found
        """
        return self._read_buffer.get(entity_id=entity_id, component_type=component_type)

    def write(
        self, entity_id: EntityID, component_type: type[Component], component: Component
    ) -> None:
        """Write component to next state (write buffer).

        Args:
            entity_id: Entity to write to
            component_type: Type of component to write
            component: Component instance to write
        """
        self._write_buffer.add(entity_id=entity_id, component=component)

    def has(self, entity_id: EntityID, component_type: type[Component]) -> bool:
        """Check if entity has component in current state.

        Args:
            entity_id: Entity to check
            component_type: Type of component to check for

        Returns:
            True if entity has component in read buffer
        """
        return self._read_buffer.has(entity_id=entity_id, component_type=component_type)

    def get_all(self, component_type: type[T]) -> dict[EntityID, T]:
        """Get all components of type from current state.

        Args:
            component_type: Type of components to get

        Returns:
            Dictionary mapping entity IDs to components from read buffer
        """
        return self._read_buffer.get_all(component_type=component_type)

    def swap(self) -> None:
        """Atomically swap read and write buffers.

        After swap:
        - Write buffer becomes read buffer (next state becomes current)
        - Read buffer becomes write buffer (cleared for next frame)

        This operation is thread-safe via lock.
        """
        with self._swap_lock:
            self._read_buffer, self._write_buffer = (
                self._write_buffer,
                ComponentStore(),
            )

    def clear_write_buffer(self) -> None:
        """Clear the write buffer without swapping.

        Useful for discarding pending writes.
        """
        with self._swap_lock:
            self._write_buffer = ComponentStore()

    def copy_to_write_buffer(self) -> None:
        """Copy current read buffer to write buffer.

        Useful when you want to preserve current state in next frame
        and only apply incremental changes.
        """
        with self._swap_lock:
            for component_type in self._read_buffer.get_component_types():
                for entity_id, component in self._read_buffer.get_all(
                    component_type=component_type
                ).items():
                    self._write_buffer.add(entity_id=entity_id, component=component)

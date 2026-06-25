"""Component lifecycle hooks for reactive programming."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from yuna.exceptions import ValidationError

if TYPE_CHECKING:
    from yuna.ecs.component import Component
    from yuna.types.identifiers import EntityID


class ComponentLifecycle:
    """Manages lifecycle callbacks for component add/remove events.

    Responsibilities:
    - Register callbacks for component types
    - Invoke callbacks when components added/removed
    - Support multiple callbacks per component type
    - Unregister callbacks when no longer needed

    Usage:
        lifecycle = ComponentLifecycle()

        def on_position_added(entity_id, component_type, component):
            print(f"Position added to {entity_id}: {component}")

        lifecycle.register_added_callback(
            component_type=Position,
            callback=on_position_added,
        )

        lifecycle.on_component_added(
            entity_id=entity1,
            component_type=Position,
            component=Position(x=10, y=20),
        )
    """

    def __init__(self) -> None:
        self._added_callbacks: dict[
            type, list[Callable[[EntityID, type, Any], None]]
        ] = {}
        self._removed_callbacks: dict[
            type, list[Callable[[EntityID, type, Any], None]]
        ] = {}

    def register_added_callback(
        self,
        component_type: type,
        callback: Callable[[EntityID, type, Any], None],
    ) -> None:
        """Register callback to invoke when component type is added.

        Args:
            component_type: Type of component to watch
            callback: Function to call when component added
                      Signature: (entity_id, component_type, component) -> None
        """
        if component_type not in self._added_callbacks:
            self._added_callbacks[component_type] = []
        self._added_callbacks[component_type].append(callback)

    def register_removed_callback(
        self,
        component_type: type,
        callback: Callable[[EntityID, type, Any], None],
    ) -> None:
        """Register callback to invoke when component type is removed.

        Args:
            component_type: Type of component to watch
            callback: Function to call when component removed
                      Signature: (entity_id, component_type, component) -> None
        """
        if component_type not in self._removed_callbacks:
            self._removed_callbacks[component_type] = []
        self._removed_callbacks[component_type].append(callback)

    def unregister_added_callback(
        self,
        component_type: type,
        callback: Callable[[EntityID, type, Any], None],
    ) -> None:
        """Unregister callback for component add events.

        Args:
            component_type: Type of component to stop watching
            callback: Callback to remove

        Raises:
            ValidationError: If callback not registered for this component type
        """
        if component_type not in self._added_callbacks:
            raise ValidationError(
                reason=f"No added callbacks registered for {component_type.__name__}",
                field="component_type",
                value=component_type.__name__,
            )

        if callback not in self._added_callbacks[component_type]:
            raise ValidationError(
                reason=(
                    f"Callback not registered for {component_type.__name__} add events"
                ),
                field="callback",
            )

        self._added_callbacks[component_type].remove(callback)

        if not self._added_callbacks[component_type]:
            del self._added_callbacks[component_type]

    def unregister_removed_callback(
        self,
        component_type: type,
        callback: Callable[[EntityID, type, Any], None],
    ) -> None:
        """Unregister callback for component remove events.

        Args:
            component_type: Type of component to stop watching
            callback: Callback to remove

        Raises:
            ValidationError: If callback not registered for this component type
        """
        if component_type not in self._removed_callbacks:
            raise ValidationError(
                reason=f"No removed callbacks registered for {component_type.__name__}",
                field="component_type",
                value=component_type.__name__,
            )

        if callback not in self._removed_callbacks[component_type]:
            raise ValidationError(
                reason=(
                    f"Callback not registered for {component_type.__name__} "
                    "remove events"
                ),
                field="callback",
            )

        self._removed_callbacks[component_type].remove(callback)

        if not self._removed_callbacks[component_type]:
            del self._removed_callbacks[component_type]

    def on_component_added(
        self,
        entity_id: EntityID,
        component_type: type,
        component: Component,
    ) -> None:
        """Invoke all registered callbacks for component add event.

        Args:
            entity_id: Entity that received component
            component_type: Type of component added
            component: Component instance that was added
        """
        if component_type in self._added_callbacks:
            for callback in self._added_callbacks[component_type]:
                callback(entity_id, component_type, component)

    def on_component_removed(
        self,
        entity_id: EntityID,
        component_type: type,
        component: Component,
    ) -> None:
        """Invoke all registered callbacks for component remove event.

        Args:
            entity_id: Entity that lost component
            component_type: Type of component removed
            component: Component instance that was removed
        """
        if component_type in self._removed_callbacks:
            for callback in self._removed_callbacks[component_type]:
                callback(entity_id, component_type, component)

    def has_added_callbacks(self, component_type: type) -> bool:
        """Check if component type has any registered add callbacks.

        Args:
            component_type: Type to check

        Returns:
            True if callbacks registered for add events
        """
        return component_type in self._added_callbacks

    def has_removed_callbacks(self, component_type: type) -> bool:
        """Check if component type has any registered remove callbacks.

        Args:
            component_type: Type to check

        Returns:
            True if callbacks registered for remove events
        """
        return component_type in self._removed_callbacks

    def get_added_callback_count(self, component_type: type) -> int:
        """Get number of registered add callbacks for component type.

        Args:
            component_type: Type to check

        Returns:
            Number of callbacks registered for add events
        """
        return len(self._added_callbacks.get(component_type, []))

    def get_removed_callback_count(self, component_type: type) -> int:
        """Get number of registered remove callbacks for component type.

        Args:
            component_type: Type to check

        Returns:
            Number of callbacks registered for remove events
        """
        return len(self._removed_callbacks.get(component_type, []))

    def clear(self) -> None:
        """Clear all registered callbacks."""
        self._added_callbacks.clear()
        self._removed_callbacks.clear()

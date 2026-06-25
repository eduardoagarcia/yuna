"""Network replication management."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from yuna.network.authority import Authority, NetworkRole

if TYPE_CHECKING:
    from yuna.types.identifiers import EntityID


class ReplicationManager:
    """Manages component replication across network.

    Responsibilities:
    - Track which components are replicated
    - Extract replicated state from entities
    - Apply replicated state to entities
    - Enforce authority rules
    - Track entity ownership
    - Throttle updates based on update_rate

    Usage:
        manager = ReplicationManager(role=NetworkRole.SERVER)
        manager.register_replicated_component(component_type="Position")
        state = manager.get_replicated_state(
            entity_id=entity,
            components={"Position": position_data},
        )
        manager.apply_replicated_state(
            entity_id=entity,
            state=state,
            components={"Position": position_data},
        )
    """

    def __init__(self, role: NetworkRole) -> None:
        """Initialize replication manager.

        Args:
            role: Network role (SERVER, CLIENT, or PEER)
        """
        self._role = role
        self._replicated_components: set[str] = set()
        self._entity_owners: dict[EntityID, str] = {}
        self._last_update_times: dict[tuple[EntityID, str], float] = {}

    def register_replicated_component(self, component_type: str) -> None:
        """Register component type for replication.

        Args:
            component_type: Name of component to replicate
        """
        self._replicated_components.add(component_type)

    def get_replicated_state(
        self,
        entity_id: EntityID,
        components: dict[str, Any],
        observer_id: str | None = None,
    ) -> dict[str, Any]:
        """Get entity's replicated component state.

        Args:
            entity_id: Entity to get state for
            components: All components for this entity
            observer_id: ID of observing client (for owner_only filtering)

        Returns:
            Dictionary of replicated component data
        """
        replicated_state: dict[str, Any] = {}

        for component_type, component_data in components.items():
            if not self._should_replicate_component(
                component_type=component_type,
                component_data=component_data,
                entity_id=entity_id,
                observer_id=observer_id,
            ):
                continue

            if not self._should_update_now(
                entity_id=entity_id,
                component_type=component_type,
                component_data=component_data,
            ):
                continue

            replicated_state[component_type] = component_data

        return replicated_state

    def apply_replicated_state(
        self,
        entity_id: EntityID,
        state: dict[str, Any],
        components: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply replicated state to entity components.

        Args:
            entity_id: Entity to apply state to
            state: Replicated state to apply
            components: Current components (will be modified)

        Returns:
            Updated components dictionary
        """
        for component_type, component_data in state.items():
            if not self._check_authority(
                entity_id=entity_id,
                component_data=component_data,
            ):
                continue

            components[component_type] = component_data

        return components

    @staticmethod
    def should_replicate(component_data: Any, role: NetworkRole) -> bool:
        """Check if component should replicate for given role.

        Args:
            component_data: Component data to check
            role: Network role to check for

        Returns:
            True if component should replicate
        """
        if not hasattr(component_data, "replicate"):
            return False

        if not component_data.replicate:
            return False

        return True

    def check_authority(
        self,
        entity_id: EntityID,
        component_data: Any,
        role: NetworkRole,
    ) -> bool:
        """Check if role has authority to modify component.

        Args:
            entity_id: Entity being modified
            component_data: Component being modified
            role: Network role attempting modification

        Returns:
            True if role has authority
        """
        if not hasattr(component_data, "authority"):
            return self._role == NetworkRole.SERVER

        authority = component_data.authority

        if authority == Authority.SERVER:
            return role == NetworkRole.SERVER

        if authority == Authority.CLIENT:
            owner_id = self._entity_owners.get(entity_id)
            return role == NetworkRole.CLIENT and owner_id is not None

        if authority == Authority.SHARED:
            return True

        return False

    def set_entity_owner(self, entity_id: EntityID, owner_id: str) -> None:
        """Set ownership of entity.

        Args:
            entity_id: Entity to set owner for
            owner_id: ID of owning client
        """
        self._entity_owners[entity_id] = owner_id

    def get_entity_owner(self, entity_id: EntityID) -> str | None:
        """Get owner of entity.

        Args:
            entity_id: Entity to get owner for

        Returns:
            Owner ID or None if no owner
        """
        return self._entity_owners.get(entity_id)

    def _should_replicate_component(
        self,
        component_type: str,
        component_data: Any,
        entity_id: EntityID,
        observer_id: str | None,
    ) -> bool:
        """Check if component should be replicated.

        Args:
            component_type: Type of component
            component_data: Component data
            entity_id: Entity ID
            observer_id: Observer client ID

        Returns:
            True if component should be replicated
        """
        if component_type not in self._replicated_components:
            return False

        if not self.should_replicate(
            component_data=component_data,
            role=self._role,
        ):
            return False

        if hasattr(component_data, "owner_only") and component_data.owner_only:
            owner_id = self._entity_owners.get(entity_id)
            if observer_id != owner_id:
                return False

        return True

    def _should_update_now(
        self,
        entity_id: EntityID,
        component_type: str,
        component_data: Any,
    ) -> bool:
        """Check if component should update based on update_rate.

        Args:
            entity_id: Entity ID
            component_type: Component type
            component_data: Component data

        Returns:
            True if component should update now
        """
        if not hasattr(component_data, "update_rate"):
            return True

        update_rate = component_data.update_rate

        if update_rate <= 0.0:
            return True

        key = (entity_id, component_type)
        current_time = time.time()

        if key not in self._last_update_times:
            self._last_update_times[key] = current_time
            return True

        last_update = self._last_update_times[key]
        time_since_update = current_time - last_update
        min_interval = 1.0 / update_rate

        if time_since_update >= min_interval:
            self._last_update_times[key] = current_time
            return True

        return False

    def _check_authority(
        self,
        entity_id: EntityID,
        component_data: Any,
    ) -> bool:
        """Check if current role has authority to apply update.

        Args:
            entity_id: Entity ID
            component_data: Component data

        Returns:
            True if has authority
        """
        return self.check_authority(
            entity_id=entity_id,
            component_data=component_data,
            role=self._role,
        )

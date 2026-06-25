"""Tests for network replication."""

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

from faker import Faker

from yuna.network.authority import Authority, NetworkRole
from yuna.network.component_tags import NetworkedComponent
from yuna.network.replication import ReplicationManager
from yuna.types.identifiers import EntityID

fake = Faker()


@dataclass
class Position(NetworkedComponent):
    """Test position component."""

    x: float = 0.0
    y: float = 0.0


@dataclass
class Health(NetworkedComponent):
    """Test health component."""

    current: int = 100
    maximum: int = 100
    authority: Authority = Authority.CLIENT


@dataclass
class ServerOnlyComponent(NetworkedComponent):
    """Test server-only component."""

    data: str = ""
    authority: Authority = Authority.SERVER


@dataclass
class OwnerOnlyComponent(NetworkedComponent):
    """Test owner-only component."""

    secret: str = ""
    owner_only: bool = True


@dataclass
class ThrottledComponent(NetworkedComponent):
    """Test component with update rate."""

    value: int = 0
    update_rate: float = 10.0


@dataclass
class NonReplicatedComponent(NetworkedComponent):
    """Test non-replicated component."""

    data: str = ""
    replicate: bool = False


@dataclass
class PlainComponent:
    """Test plain component without network metadata."""

    data: str = ""


@dataclass
class ComponentWithoutUpdateRate:
    """Test component with replicate but no update_rate."""

    data: str = ""
    replicate: bool = True


def test_replication_manager_creation() -> None:
    """Test ReplicationManager can be instantiated."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    assert manager is not None


def test_register_replicated_component() -> None:
    """Test registering component type for replication."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    manager.register_replicated_component(component_type="Position")
    assert "Position" in manager._replicated_components


def test_register_multiple_components() -> None:
    """Test registering multiple component types."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    manager.register_replicated_component(component_type="Position")
    manager.register_replicated_component(component_type="Health")
    assert "Position" in manager._replicated_components
    assert "Health" in manager._replicated_components


def test_get_replicated_state_empty_when_not_registered() -> None:
    """Test get_replicated_state returns empty for unregistered components."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())

    position = Position(x=1.0, y=2.0)
    components = {"Position": position}

    state = manager.get_replicated_state(entity_id=entity_id, components=components)

    assert state == {}


def test_get_replicated_state_includes_registered_components() -> None:
    """Test get_replicated_state includes registered components."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())

    manager.register_replicated_component(component_type="Position")

    position = Position(x=1.0, y=2.0)
    components = {"Position": position}

    state = manager.get_replicated_state(entity_id=entity_id, components=components)

    assert "Position" in state
    assert state["Position"] == position


def test_get_replicated_state_excludes_non_replicated() -> None:
    """Test get_replicated_state excludes non-replicated components."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())

    manager.register_replicated_component(component_type="NonReplicatedComponent")

    component = NonReplicatedComponent(data=fake.text())
    components = {"NonReplicatedComponent": component}

    state = manager.get_replicated_state(entity_id=entity_id, components=components)

    assert state == {}


def test_get_replicated_state_filters_owner_only_components() -> None:
    """Test get_replicated_state filters owner-only components."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())
    owner_id = fake.uuid4()
    observer_id = fake.uuid4()

    manager.register_replicated_component(component_type="OwnerOnlyComponent")
    manager.set_entity_owner(entity_id=entity_id, owner_id=owner_id)

    component = OwnerOnlyComponent(secret=fake.text())
    components = {"OwnerOnlyComponent": component}

    state = manager.get_replicated_state(
        entity_id=entity_id,
        components=components,
        observer_id=observer_id,
    )

    assert state == {}


def test_get_replicated_state_includes_owner_only_for_owner() -> None:
    """Test get_replicated_state includes owner-only for owner."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())
    owner_id = fake.uuid4()

    manager.register_replicated_component(component_type="OwnerOnlyComponent")
    manager.set_entity_owner(entity_id=entity_id, owner_id=owner_id)

    component = OwnerOnlyComponent(secret=fake.text())
    components = {"OwnerOnlyComponent": component}

    state = manager.get_replicated_state(
        entity_id=entity_id,
        components=components,
        observer_id=owner_id,
    )

    assert "OwnerOnlyComponent" in state


@patch("yuna.network.replication.time.time")
def test_get_replicated_state_throttles_updates(mock_time: MagicMock) -> None:
    """Test get_replicated_state throttles based on update_rate."""
    mock_time.return_value = 0.0

    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())

    manager.register_replicated_component(component_type="ThrottledComponent")

    component = ThrottledComponent(value=42, update_rate=10.0)
    components = {"ThrottledComponent": component}

    state_1 = manager.get_replicated_state(
        entity_id=entity_id,
        components=components,
    )
    assert "ThrottledComponent" in state_1

    mock_time.return_value = 0.05

    state_2 = manager.get_replicated_state(
        entity_id=entity_id,
        components=components,
    )
    assert state_2 == {}

    mock_time.return_value = 0.11

    state_3 = manager.get_replicated_state(
        entity_id=entity_id,
        components=components,
    )
    assert "ThrottledComponent" in state_3


def test_apply_replicated_state() -> None:
    """Test applying replicated state to components."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())

    position = Position(x=1.0, y=2.0)
    state = {"Position": position}
    components: dict[str, object] = {}

    updated_components = manager.apply_replicated_state(
        entity_id=entity_id,
        state=state,
        components=components,
    )

    assert "Position" in updated_components
    assert updated_components["Position"] == position


def test_apply_replicated_state_respects_authority() -> None:
    """Test apply_replicated_state respects authority rules."""
    manager = ReplicationManager(role=NetworkRole.CLIENT)
    entity_id = EntityID(fake.uuid4())

    server_component = ServerOnlyComponent(data=fake.text())
    state = {"ServerOnlyComponent": server_component}
    components: dict[str, object] = {}

    updated_components = manager.apply_replicated_state(
        entity_id=entity_id,
        state=state,
        components=components,
    )

    assert "ServerOnlyComponent" not in updated_components


def test_should_replicate_true_for_networked_component() -> None:
    """Test should_replicate returns True for networked components."""
    manager = ReplicationManager(role=NetworkRole.SERVER)

    position = Position(x=1.0, y=2.0)

    assert (
        manager.should_replicate(
            component_data=position,
            role=NetworkRole.SERVER,
        )
        is True
    )


def test_should_replicate_false_for_non_replicated() -> None:
    """Test should_replicate returns False when replicate=False."""
    manager = ReplicationManager(role=NetworkRole.SERVER)

    component = NonReplicatedComponent(data=fake.text())

    assert (
        manager.should_replicate(
            component_data=component,
            role=NetworkRole.SERVER,
        )
        is False
    )


def test_should_replicate_false_for_plain_component() -> None:
    """Test should_replicate returns False for plain components."""
    manager = ReplicationManager(role=NetworkRole.SERVER)

    component = PlainComponent(data=fake.text())

    assert (
        manager.should_replicate(
            component_data=component,
            role=NetworkRole.SERVER,
        )
        is False
    )


def test_check_authority_server_can_modify_server_authority() -> None:
    """Test server can modify SERVER authority components."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())

    component = ServerOnlyComponent(data=fake.text())

    assert (
        manager.check_authority(
            entity_id=entity_id,
            component_data=component,
            role=NetworkRole.SERVER,
        )
        is True
    )


def test_check_authority_client_cannot_modify_server_authority() -> None:
    """Test client cannot modify SERVER authority components."""
    manager = ReplicationManager(role=NetworkRole.CLIENT)
    entity_id = EntityID(fake.uuid4())

    component = ServerOnlyComponent(data=fake.text())

    assert (
        manager.check_authority(
            entity_id=entity_id,
            component_data=component,
            role=NetworkRole.CLIENT,
        )
        is False
    )


def test_check_authority_client_can_modify_owned_client_authority() -> None:
    """Test client can modify CLIENT authority for owned entities."""
    manager = ReplicationManager(role=NetworkRole.CLIENT)
    entity_id = EntityID(fake.uuid4())
    owner_id = fake.uuid4()

    manager.set_entity_owner(entity_id=entity_id, owner_id=owner_id)

    component = Health(current=100, maximum=100)

    assert (
        manager.check_authority(
            entity_id=entity_id,
            component_data=component,
            role=NetworkRole.CLIENT,
        )
        is True
    )


def test_check_authority_anyone_can_modify_shared_authority() -> None:
    """Test anyone can modify SHARED authority components."""
    manager = ReplicationManager(role=NetworkRole.CLIENT)
    entity_id = EntityID(fake.uuid4())

    component = Position(x=1.0, y=2.0, authority=Authority.SHARED)

    assert (
        manager.check_authority(
            entity_id=entity_id,
            component_data=component,
            role=NetworkRole.CLIENT,
        )
        is True
    )


def test_check_authority_plain_component_requires_server() -> None:
    """Test plain components require server authority."""
    manager = ReplicationManager(role=NetworkRole.CLIENT)
    entity_id = EntityID(fake.uuid4())

    component = PlainComponent(data=fake.text())

    assert (
        manager.check_authority(
            entity_id=entity_id,
            component_data=component,
            role=NetworkRole.CLIENT,
        )
        is False
    )


def test_check_authority_invalid_authority_returns_false() -> None:
    """Test check_authority returns False for invalid authority."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())

    component = Position(x=1.0, y=2.0)
    component.authority = "invalid"  # type: ignore[assignment]

    assert (
        manager.check_authority(
            entity_id=entity_id,
            component_data=component,
            role=NetworkRole.SERVER,
        )
        is False
    )


def test_set_entity_owner() -> None:
    """Test setting entity owner."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())
    owner_id = fake.uuid4()

    manager.set_entity_owner(entity_id=entity_id, owner_id=owner_id)

    assert manager.get_entity_owner(entity_id=entity_id) == owner_id


def test_get_entity_owner_none_when_not_set() -> None:
    """Test get_entity_owner returns None when not set."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())

    assert manager.get_entity_owner(entity_id=entity_id) is None


def test_set_entity_owner_overwrites_previous() -> None:
    """Test setting entity owner overwrites previous owner."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())
    owner_id_1 = fake.uuid4()
    owner_id_2 = fake.uuid4()

    manager.set_entity_owner(entity_id=entity_id, owner_id=owner_id_1)
    manager.set_entity_owner(entity_id=entity_id, owner_id=owner_id_2)

    assert manager.get_entity_owner(entity_id=entity_id) == owner_id_2


def test_multiple_entities_different_owners() -> None:
    """Test multiple entities can have different owners."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id_1 = EntityID(fake.uuid4())
    entity_id_2 = EntityID(fake.uuid4())
    owner_id_1 = fake.uuid4()
    owner_id_2 = fake.uuid4()

    manager.set_entity_owner(entity_id=entity_id_1, owner_id=owner_id_1)
    manager.set_entity_owner(entity_id=entity_id_2, owner_id=owner_id_2)

    assert manager.get_entity_owner(entity_id=entity_id_1) == owner_id_1
    assert manager.get_entity_owner(entity_id=entity_id_2) == owner_id_2


def test_get_replicated_state_multiple_components() -> None:
    """Test get_replicated_state with multiple components."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())

    manager.register_replicated_component(component_type="Position")
    manager.register_replicated_component(component_type="Health")

    position = Position(x=1.0, y=2.0)
    health = Health(current=100, maximum=100)
    components = {"Position": position, "Health": health}

    state = manager.get_replicated_state(entity_id=entity_id, components=components)

    assert "Position" in state
    assert "Health" in state


def test_apply_replicated_state_updates_existing_components() -> None:
    """Test apply_replicated_state updates existing components."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())

    old_position = Position(x=1.0, y=2.0)
    new_position = Position(x=3.0, y=4.0)

    components = {"Position": old_position}
    state = {"Position": new_position}

    updated_components = manager.apply_replicated_state(
        entity_id=entity_id,
        state=state,
        components=components,
    )

    assert updated_components["Position"] == new_position


def test_networked_component_defaults() -> None:
    """Test NetworkedComponent has correct defaults."""
    position = Position(x=1.0, y=2.0)

    assert position.replicate is True
    assert position.authority == Authority.SERVER
    assert position.owner_only is False
    assert position.reliable is True
    assert position.update_rate == 0.0


def test_get_replicated_state_with_plain_component() -> None:
    """Test get_replicated_state with component without replicate attribute."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())

    manager.register_replicated_component(component_type="PlainComponent")

    component = PlainComponent(data=fake.text())
    components = {"PlainComponent": component}

    state = manager.get_replicated_state(entity_id=entity_id, components=components)

    assert state == {}


def test_get_replicated_state_without_update_rate() -> None:
    """Test get_replicated_state with component without update_rate."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())

    manager.register_replicated_component(component_type="ComponentWithoutUpdateRate")

    component = ComponentWithoutUpdateRate(data=fake.text())
    components = {"ComponentWithoutUpdateRate": component}

    state = manager.get_replicated_state(entity_id=entity_id, components=components)

    assert "ComponentWithoutUpdateRate" in state


def test_get_replicated_state_zero_update_rate() -> None:
    """Test get_replicated_state with zero update_rate always updates."""
    manager = ReplicationManager(role=NetworkRole.SERVER)
    entity_id = EntityID(fake.uuid4())

    manager.register_replicated_component(component_type="Position")

    position = Position(x=1.0, y=2.0, update_rate=0.0)
    components = {"Position": position}

    state_1 = manager.get_replicated_state(
        entity_id=entity_id,
        components=components,
    )
    assert "Position" in state_1

    state_2 = manager.get_replicated_state(
        entity_id=entity_id,
        components=components,
    )
    assert "Position" in state_2

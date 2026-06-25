"""Tests for component migration system."""

from typing import Any

import pytest
from faker import Faker

from yuna.exceptions import ValidationError
from yuna.state.migrations import Migration, MigrationRegistry

fake = Faker()


def test_migration_creation() -> None:
    """Test Migration dataclass creation."""

    def upgrade_func(data: dict[str, Any]) -> dict[str, Any]:
        data["z"] = 0.0
        return data

    migration = Migration(
        from_version=1,
        to_version=2,
        upgrade=upgrade_func,
    )

    assert migration.from_version == 1
    assert migration.to_version == 2
    assert migration.upgrade == upgrade_func


def test_registry_initial_state() -> None:
    """Test registry starts empty."""
    registry = MigrationRegistry()

    assert registry.get_registered_migrations(component_type="Position") == []


def test_register_migration() -> None:
    """Test registering a migration."""
    registry = MigrationRegistry()

    def upgrade(data: dict[str, Any]) -> dict[str, Any]:
        return data

    migration = Migration(from_version=1, to_version=2, upgrade=upgrade)

    registry.register_migration(component_type="Position", migration=migration)

    assert (1, 2) in registry.get_registered_migrations(component_type="Position")


def test_register_migration_duplicate() -> None:
    """Test registering duplicate migration raises error."""
    registry = MigrationRegistry()

    def upgrade(data: dict[str, Any]) -> dict[str, Any]:
        return data

    migration = Migration(from_version=1, to_version=2, upgrade=upgrade)

    registry.register_migration(component_type="Position", migration=migration)

    with pytest.raises(ValidationError, match="already registered"):
        registry.register_migration(component_type="Position", migration=migration)


def test_register_migration_different_components() -> None:
    """Test registering migrations for different components."""
    registry = MigrationRegistry()

    def upgrade(data: dict[str, Any]) -> dict[str, Any]:
        return data

    migration_a = Migration(from_version=1, to_version=2, upgrade=upgrade)
    migration_b = Migration(from_version=1, to_version=2, upgrade=upgrade)

    registry.register_migration(component_type="ComponentA", migration=migration_a)
    registry.register_migration(component_type="ComponentB", migration=migration_b)

    assert (1, 2) in registry.get_registered_migrations(component_type="ComponentA")
    assert (1, 2) in registry.get_registered_migrations(component_type="ComponentB")


def test_unregister_migration() -> None:
    """Test unregistering a migration."""
    registry = MigrationRegistry()

    def upgrade(data: dict[str, Any]) -> dict[str, Any]:
        return data

    migration = Migration(from_version=1, to_version=2, upgrade=upgrade)

    registry.register_migration(component_type="Position", migration=migration)
    registry.unregister_migration(
        component_type="Position",
        from_version=1,
        to_version=2,
    )

    assert registry.get_registered_migrations(component_type="Position") == []


def test_unregister_migration_not_registered() -> None:
    """Test unregistering non-existent migration raises error."""
    registry = MigrationRegistry()

    with pytest.raises(ValidationError, match="No migrations registered"):
        registry.unregister_migration(
            component_type="Position",
            from_version=1,
            to_version=2,
        )


def test_unregister_migration_wrong_version() -> None:
    """Test unregistering wrong version raises error."""
    registry = MigrationRegistry()

    def upgrade(data: dict[str, Any]) -> dict[str, Any]:
        return data

    migration = Migration(from_version=1, to_version=2, upgrade=upgrade)

    registry.register_migration(component_type="Position", migration=migration)

    with pytest.raises(
        ValidationError, match="No migration registered for this version range"
    ):
        registry.unregister_migration(
            component_type="Position",
            from_version=2,
            to_version=3,
        )


def test_is_registered() -> None:
    """Test checking if migration is registered."""
    registry = MigrationRegistry()

    def upgrade(data: dict[str, Any]) -> dict[str, Any]:
        return data

    migration = Migration(from_version=1, to_version=2, upgrade=upgrade)

    assert (
        registry.is_registered(
            component_type="Position",
            from_version=1,
            to_version=2,
        )
        is False
    )

    registry.register_migration(component_type="Position", migration=migration)

    assert (
        registry.is_registered(
            component_type="Position",
            from_version=1,
            to_version=2,
        )
        is True
    )


def test_get_registered_migrations() -> None:
    """Test getting list of registered migrations."""
    registry = MigrationRegistry()

    def upgrade(data: dict[str, Any]) -> dict[str, Any]:
        return data

    migration1 = Migration(from_version=1, to_version=2, upgrade=upgrade)
    migration2 = Migration(from_version=2, to_version=3, upgrade=upgrade)
    migration3 = Migration(from_version=1, to_version=3, upgrade=upgrade)

    registry.register_migration(component_type="Position", migration=migration1)
    registry.register_migration(component_type="Position", migration=migration2)
    registry.register_migration(component_type="Position", migration=migration3)

    migrations = registry.get_registered_migrations(component_type="Position")

    assert migrations == [(1, 2), (1, 3), (2, 3)]


def test_find_migration_path_direct() -> None:
    """Test finding direct migration path."""
    registry = MigrationRegistry()

    def upgrade(data: dict[str, Any]) -> dict[str, Any]:
        data["z"] = 0.0
        return data

    migration = Migration(from_version=1, to_version=2, upgrade=upgrade)

    registry.register_migration(component_type="Position", migration=migration)

    path = registry.find_migration_path(
        component_type="Position",
        from_version=1,
        to_version=2,
    )

    assert len(path) == 1
    assert path[0].from_version == 1
    assert path[0].to_version == 2


def test_find_migration_path_chain() -> None:
    """Test finding chained migration path."""
    registry = MigrationRegistry()

    def upgrade_1_to_2(data: dict[str, Any]) -> dict[str, Any]:
        data["z"] = 0.0
        return data

    def upgrade_2_to_3(data: dict[str, Any]) -> dict[str, Any]:
        data["rotation"] = 0.0
        return data

    migration1 = Migration(from_version=1, to_version=2, upgrade=upgrade_1_to_2)
    migration2 = Migration(from_version=2, to_version=3, upgrade=upgrade_2_to_3)

    registry.register_migration(component_type="Position", migration=migration1)
    registry.register_migration(component_type="Position", migration=migration2)

    path = registry.find_migration_path(
        component_type="Position",
        from_version=1,
        to_version=3,
    )

    assert len(path) == 2
    assert path[0].from_version == 1
    assert path[0].to_version == 2
    assert path[1].from_version == 2
    assert path[1].to_version == 3


def test_find_migration_path_same_version() -> None:
    """Test finding migration path when versions are same."""
    registry = MigrationRegistry()

    path = registry.find_migration_path(
        component_type="Position",
        from_version=1,
        to_version=1,
    )

    assert path == []


def test_find_migration_path_no_path() -> None:
    """Test finding migration path when no path exists."""
    registry = MigrationRegistry()

    def upgrade(data: dict[str, Any]) -> dict[str, Any]:
        return data

    migration = Migration(from_version=1, to_version=2, upgrade=upgrade)

    registry.register_migration(component_type="Position", migration=migration)

    with pytest.raises(ValidationError, match="No migration path"):
        registry.find_migration_path(
            component_type="Position",
            from_version=1,
            to_version=3,
        )


def test_find_migration_path_no_migrations() -> None:
    """Test finding migration path when no migrations registered."""
    registry = MigrationRegistry()

    with pytest.raises(ValidationError, match="No migrations registered"):
        registry.find_migration_path(
            component_type="Position",
            from_version=1,
            to_version=2,
        )


def test_find_migration_path_shortest() -> None:
    """Test finding shortest migration path."""
    registry = MigrationRegistry()

    def upgrade(data: dict[str, Any]) -> dict[str, Any]:
        return data

    migration_direct = Migration(from_version=1, to_version=3, upgrade=upgrade)
    migration_1_to_2 = Migration(from_version=1, to_version=2, upgrade=upgrade)
    migration_2_to_3 = Migration(from_version=2, to_version=3, upgrade=upgrade)

    registry.register_migration(component_type="Position", migration=migration_direct)
    registry.register_migration(component_type="Position", migration=migration_1_to_2)
    registry.register_migration(component_type="Position", migration=migration_2_to_3)

    path = registry.find_migration_path(
        component_type="Position",
        from_version=1,
        to_version=3,
    )

    assert len(path) == 1
    assert path[0].from_version == 1
    assert path[0].to_version == 3


def test_migrate_component_direct() -> None:
    """Test migrating component with direct migration."""
    registry = MigrationRegistry()

    def upgrade_1_to_2(data: dict[str, Any]) -> dict[str, Any]:
        data["z"] = 0.0
        return data

    migration = Migration(from_version=1, to_version=2, upgrade=upgrade_1_to_2)

    registry.register_migration(component_type="Position", migration=migration)

    data = {"x": 1.0, "y": 2.0, "__version__": 1}

    result = registry.migrate_component(
        component_type="Position",
        data=data,
        target_version=2,
    )

    assert result == {"x": 1.0, "y": 2.0, "z": 0.0, "__version__": 2}


def test_migrate_component_chain() -> None:
    """Test migrating component with chained migrations."""
    registry = MigrationRegistry()

    def upgrade_1_to_2(data: dict[str, Any]) -> dict[str, Any]:
        data["z"] = 0.0
        return data

    def upgrade_2_to_3(data: dict[str, Any]) -> dict[str, Any]:
        data["rotation"] = 0.0
        return data

    migration1 = Migration(from_version=1, to_version=2, upgrade=upgrade_1_to_2)
    migration2 = Migration(from_version=2, to_version=3, upgrade=upgrade_2_to_3)

    registry.register_migration(component_type="Position", migration=migration1)
    registry.register_migration(component_type="Position", migration=migration2)

    data = {"x": 1.0, "y": 2.0, "__version__": 1}

    result = registry.migrate_component(
        component_type="Position",
        data=data,
        target_version=3,
    )

    assert result == {
        "x": 1.0,
        "y": 2.0,
        "z": 0.0,
        "rotation": 0.0,
        "__version__": 3,
    }


def test_migrate_component_same_version() -> None:
    """Test migrating component when already at target version."""
    registry = MigrationRegistry()

    data = {"x": 1.0, "y": 2.0, "__version__": 2}

    result = registry.migrate_component(
        component_type="Position",
        data=data,
        target_version=2,
    )

    assert result == {"x": 1.0, "y": 2.0, "__version__": 2}


def test_migrate_component_no_version_field() -> None:
    """Test migrating component without version field."""
    registry = MigrationRegistry()

    def upgrade_1_to_2(data: dict[str, Any]) -> dict[str, Any]:
        data["z"] = 0.0
        return data

    migration = Migration(from_version=1, to_version=2, upgrade=upgrade_1_to_2)

    registry.register_migration(component_type="Position", migration=migration)

    data = {"x": 1.0, "y": 2.0}

    result = registry.migrate_component(
        component_type="Position",
        data=data,
        target_version=2,
    )

    assert result == {"x": 1.0, "y": 2.0, "z": 0.0, "__version__": 2}


def test_migrate_component_preserves_original() -> None:
    """Test migrate_component does not modify original dict."""
    registry = MigrationRegistry()

    def upgrade_1_to_2(data: dict[str, Any]) -> dict[str, Any]:
        data["z"] = 0.0
        return data

    migration = Migration(from_version=1, to_version=2, upgrade=upgrade_1_to_2)

    registry.register_migration(component_type="Position", migration=migration)

    original_data = {"x": 1.0, "y": 2.0, "__version__": 1}

    registry.migrate_component(
        component_type="Position",
        data=original_data,
        target_version=2,
    )

    assert original_data == {"x": 1.0, "y": 2.0, "__version__": 1}


def test_migration_decorator() -> None:
    """Test @migration decorator auto-registration."""
    registry = MigrationRegistry()

    @registry.migration(component_type="Position", from_version=1, to_version=2)
    def upgrade_position_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
        data["z"] = 0.0
        return data

    assert (
        registry.is_registered(
            component_type="Position",
            from_version=1,
            to_version=2,
        )
        is True
    )


def test_migration_decorator_preserves_function() -> None:
    """Test @migration decorator preserves function."""
    registry = MigrationRegistry()

    @registry.migration(component_type="Position", from_version=1, to_version=2)
    def upgrade_position_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
        data["z"] = 0.0
        return data

    data = {"x": 1.0, "y": 2.0}
    result = upgrade_position_v1_to_v2(data)

    assert result == {"x": 1.0, "y": 2.0, "z": 0.0}


def test_migration_decorator_with_migration() -> None:
    """Test decorator registration works with migrate_component."""
    registry = MigrationRegistry()

    @registry.migration(component_type="Position", from_version=1, to_version=2)
    def upgrade_position_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
        data["z"] = 0.0
        return data

    data = {"x": 1.0, "y": 2.0, "__version__": 1}

    result = registry.migrate_component(
        component_type="Position",
        data=data,
        target_version=2,
    )

    assert result == {"x": 1.0, "y": 2.0, "z": 0.0, "__version__": 2}


def test_migration_decorator_multiple() -> None:
    """Test multiple decorator registrations."""
    registry = MigrationRegistry()

    @registry.migration(component_type="Position", from_version=1, to_version=2)
    def upgrade_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
        data["z"] = 0.0
        return data

    @registry.migration(component_type="Position", from_version=2, to_version=3)
    def upgrade_v2_to_v3(data: dict[str, Any]) -> dict[str, Any]:
        data["rotation"] = 0.0
        return data

    migrations = registry.get_registered_migrations(component_type="Position")

    assert (1, 2) in migrations
    assert (2, 3) in migrations


def test_complex_migration_chain() -> None:
    """Test complex multi-step migration chain."""
    registry = MigrationRegistry()

    @registry.migration(component_type="Position", from_version=1, to_version=2)
    def upgrade_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
        data["z"] = 0.0
        return data

    @registry.migration(component_type="Position", from_version=2, to_version=3)
    def upgrade_v2_to_v3(data: dict[str, Any]) -> dict[str, Any]:
        data["rotation"] = 0.0
        return data

    @registry.migration(component_type="Position", from_version=3, to_version=4)
    def upgrade_v3_to_v4(data: dict[str, Any]) -> dict[str, Any]:
        data["scale"] = 1.0
        return data

    data = {"x": 1.0, "y": 2.0, "__version__": 1}

    result = registry.migrate_component(
        component_type="Position",
        data=data,
        target_version=4,
    )

    assert result == {
        "x": 1.0,
        "y": 2.0,
        "z": 0.0,
        "rotation": 0.0,
        "scale": 1.0,
        "__version__": 4,
    }


def test_migration_modifies_existing_fields() -> None:
    """Test migration that modifies existing fields."""
    registry = MigrationRegistry()

    @registry.migration(component_type="Position", from_version=1, to_version=2)
    def upgrade_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
        data["x"] = data["x"] * 2.0
        data["y"] = data["y"] * 2.0
        return data

    data = {"x": 1.0, "y": 2.0, "__version__": 1}

    result = registry.migrate_component(
        component_type="Position",
        data=data,
        target_version=2,
    )

    assert result == {"x": 2.0, "y": 4.0, "__version__": 2}


def test_migration_removes_fields() -> None:
    """Test migration that removes fields."""
    registry = MigrationRegistry()

    @registry.migration(component_type="Position", from_version=1, to_version=2)
    def upgrade_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
        del data["deprecated_field"]
        return data

    data = {"x": 1.0, "y": 2.0, "deprecated_field": "old", "__version__": 1}

    result = registry.migrate_component(
        component_type="Position",
        data=data,
        target_version=2,
    )

    assert result == {"x": 1.0, "y": 2.0, "__version__": 2}
    assert "deprecated_field" not in result


def test_find_migration_path_multiple_paths() -> None:
    """Test finding migration path when multiple paths exist."""
    registry = MigrationRegistry()

    def upgrade(data: dict[str, Any]) -> dict[str, Any]:
        return data

    migration_1_to_2 = Migration(from_version=1, to_version=2, upgrade=upgrade)
    migration_1_to_3 = Migration(from_version=1, to_version=3, upgrade=upgrade)
    migration_2_to_3 = Migration(from_version=2, to_version=3, upgrade=upgrade)
    migration_3_to_4 = Migration(from_version=3, to_version=4, upgrade=upgrade)

    registry.register_migration(component_type="Position", migration=migration_1_to_2)
    registry.register_migration(component_type="Position", migration=migration_1_to_3)
    registry.register_migration(component_type="Position", migration=migration_2_to_3)
    registry.register_migration(component_type="Position", migration=migration_3_to_4)

    path = registry.find_migration_path(
        component_type="Position",
        from_version=1,
        to_version=4,
    )

    assert len(path) == 2
    assert path[0].from_version == 1
    assert path[0].to_version == 3
    assert path[1].from_version == 3
    assert path[1].to_version == 4

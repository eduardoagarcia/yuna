"""Component migration system for schema version upgrades."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from yuna.exceptions import ValidationError


@dataclass
class Migration:
    """Represents a single version migration.

    Attributes:
        from_version: Source version number
        to_version: Target version number
        upgrade: Function to upgrade data from source to target version

    Usage:
        def upgrade_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
            data["z"] = 0.0
            return data

        migration = Migration(
            from_version=1,
            to_version=2,
            upgrade=upgrade_v1_to_v2,
        )
    """

    from_version: int
    to_version: int
    upgrade: Callable[[dict[str, Any]], dict[str, Any]]


class MigrationRegistry:
    """Registry for component migrations.

    Responsibilities:
    - Register migrations for component types
    - Build migration chains for multi-version upgrades
    - Apply migrations to component data
    - Auto-registration via decorator

    Usage:
        registry = MigrationRegistry()

        @registry.migration(component_type="Position", from_version=1, to_version=2)
        def upgrade_position_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
            data["z"] = 0.0
            return data

        upgraded = registry.migrate_component(
            component_type="Position",
            data={"x": 1.0, "y": 2.0, "__version__": 1},
            target_version=2,
        )
    """

    def __init__(self) -> None:
        """Initialize empty migration registry."""
        self._migrations: dict[str, dict[tuple[int, int], Migration]] = {}

    def register_migration(
        self,
        component_type: str,
        migration: Migration,
    ) -> None:
        """Register a migration for a component type.

        Args:
            component_type: Name of component type
            migration: Migration to register

        Raises:
            ValidationError: If migration already registered
        """
        if component_type not in self._migrations:
            self._migrations[component_type] = {}

        migration_key = (migration.from_version, migration.to_version)
        if migration_key in self._migrations[component_type]:
            raise ValidationError(
                field="migration",
                value=(
                    f"{component_type} v{migration.from_version}→v"
                    f"{migration.to_version}"
                ),
                reason="Migration already registered for this version range",
            )

        self._migrations[component_type][migration_key] = migration

    def unregister_migration(
        self,
        component_type: str,
        from_version: int,
        to_version: int,
    ) -> None:
        """Unregister a migration.

        Args:
            component_type: Name of component type
            from_version: Source version
            to_version: Target version

        Raises:
            ValidationError: If migration not registered
        """
        if component_type not in self._migrations:
            raise ValidationError(
                field="component_type",
                value=component_type,
                reason="No migrations registered for this component type",
            )

        migration_key = (from_version, to_version)
        if migration_key not in self._migrations[component_type]:
            raise ValidationError(
                field="migration",
                value=f"{component_type} v{from_version}→v{to_version}",
                reason="No migration registered for this version range",
            )

        del self._migrations[component_type][migration_key]

        if not self._migrations[component_type]:
            del self._migrations[component_type]

    def is_registered(
        self,
        component_type: str,
        from_version: int,
        to_version: int,
    ) -> bool:
        """Check if migration is registered.

        Args:
            component_type: Name of component type
            from_version: Source version
            to_version: Target version

        Returns:
            True if migration is registered
        """
        if component_type not in self._migrations:
            return False
        return (from_version, to_version) in self._migrations[component_type]

    def get_registered_migrations(
        self,
        component_type: str,
    ) -> list[tuple[int, int]]:
        """Get list of registered migrations for a component type.

        Args:
            component_type: Name of component type

        Returns:
            List of (from_version, to_version) tuples
        """
        if component_type not in self._migrations:
            return []
        return sorted(self._migrations[component_type].keys())

    def find_migration_path(
        self,
        component_type: str,
        from_version: int,
        to_version: int,
    ) -> list[Migration]:
        """Find migration path from source to target version.

        Uses breadth-first search to find shortest migration chain.

        Args:
            component_type: Name of component type
            from_version: Source version
            to_version: Target version

        Returns:
            List of migrations in order to apply

        Raises:
            ValidationError: If no migration path exists
        """
        if from_version == to_version:
            return []

        if component_type not in self._migrations:
            raise ValidationError(
                field="component_type",
                value=component_type,
                reason="No migrations registered for this component type",
            )

        migrations = self._migrations[component_type]
        visited: set[int] = set()
        queue: list[tuple[int, list[Migration]]] = [(from_version, [])]

        while queue:
            current_version, path = queue.pop(0)

            if current_version == to_version:
                return path

            if current_version in visited:
                continue

            visited.add(current_version)

            for (start, end), migration in migrations.items():
                if start == current_version and end not in visited:
                    queue.append((end, path + [migration]))

        raise ValidationError(
            field="migration_path",
            value=f"{component_type} v{from_version}→v{to_version}",
            reason="No migration path exists for this version range",
        )

    def migrate_component(
        self,
        component_type: str,
        data: dict[str, Any],
        target_version: int,
    ) -> dict[str, Any]:
        """Migrate component data to target version.

        Args:
            component_type: Name of component type
            data: Component data with __version__ field
            target_version: Target version number

        Returns:
            Migrated component data

        Raises:
            ValueError: If no migration path exists
        """
        current_version = data.get("__version__", 1)

        if current_version == target_version:
            return data

        migration_path = self.find_migration_path(
            component_type=component_type,
            from_version=current_version,
            to_version=target_version,
        )

        migrated_data = {k: v for k, v in data.items() if k != "__version__"}

        for migration in migration_path:
            migrated_data = migration.upgrade(migrated_data)

        migrated_data["__version__"] = target_version
        return migrated_data

    def migration(
        self,
        component_type: str,
        from_version: int,
        to_version: int,
    ) -> Callable[
        [Callable[[dict[str, Any]], dict[str, Any]]],
        Callable[[dict[str, Any]], dict[str, Any]],
    ]:
        """Decorator for auto-registration of migrations.

        Args:
            component_type: Name of component type
            from_version: Source version
            to_version: Target version

        Returns:
            Decorator function

        Usage:
            @registry.migration(component_type="Position", from_version=1, to_version=2)
            def upgrade_position_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
                data["z"] = 0.0
                return data
        """

        def decorator(
            upgrade_func: Callable[[dict[str, Any]], dict[str, Any]],
        ) -> Callable[[dict[str, Any]], dict[str, Any]]:
            migration = Migration(
                from_version=from_version,
                to_version=to_version,
                upgrade=upgrade_func,
            )
            self.register_migration(
                component_type=component_type,
                migration=migration,
            )
            return upgrade_func

        return decorator

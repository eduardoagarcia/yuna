"""Prefab manager for entity template instantiation."""

import json
from pathlib import Path
from typing import Any

import yaml

from yuna.ecs.world import ECSWorld
from yuna.exceptions import StateError, ValidationError
from yuna.prefabs.prefab import Prefab
from yuna.types.identifiers import EntityID


class PrefabManager:
    """Manages prefab definitions and entity instantiation.

    Responsibilities:
    - Register prefab templates
    - Instantiate entities from prefabs
    - Support property overrides
    - Load prefabs from JSON/YAML files
    - Handle hierarchical prefab structures
    - Integrate with ECS world for entity creation

    Usage:
        manager = PrefabManager(world=ecs_world)
        manager.register_component_type(name="Position", component_class=Position)

        player_prefab = Prefab(
            name="player",
            components={"Position": {"x": 0.0, "y": 0.0}},
        )
        manager.register_prefab(prefab=player_prefab)

        entity_id = manager.instantiate(
            prefab_name="player",
            overrides={"Position": {"x": 10.0}},
        )
    """

    def __init__(self, world: ECSWorld) -> None:
        self._world = world
        self._prefabs: dict[str, Prefab] = {}
        self._component_types: dict[str, type] = {}

    def register_component_type(self, name: str, component_class: type) -> None:
        """Register a component type for prefab instantiation.

        Args:
            name: Component type name (as used in prefabs)
            component_class: Component class to instantiate

        Raises:
            StateError: If name already registered with different class
        """
        if (
            name in self._component_types
            and self._component_types[name] != component_class
        ):
            raise StateError(
                operation="register_component_type",
                reason=(
                    f"Component type '{name}' already registered with different class"
                ),
            )
        self._component_types[name] = component_class

    def register_prefab(self, prefab: Prefab) -> None:
        """Register a prefab template.

        Args:
            prefab: Prefab definition to register

        Raises:
            StateError: If prefab with same name already exists
        """
        if prefab.name in self._prefabs:
            raise StateError(
                operation="register_prefab",
                reason=f"Prefab '{prefab.name}' already registered",
            )
        self._prefabs[prefab.name] = prefab

    def instantiate(
        self, prefab_name: str, overrides: dict[str, dict[str, Any]] | None = None
    ) -> EntityID:
        """Create entity from prefab template.

        Args:
            prefab_name: Name of prefab to instantiate
            overrides: Component property overrides (component_name -> {prop: value})

        Returns:
            Created entity ID

        Raises:
            ValidationError: If prefab not found or component type not registered
        """
        if prefab_name not in self._prefabs:
            raise ValidationError(
                reason=f"Prefab '{prefab_name}' not found",
                field="prefab_name",
                value=prefab_name,
            )

        prefab = self._prefabs[prefab_name]
        entity_id = self._world.create_entity()

        overrides = overrides or {}

        for component_name, component_data in prefab.components.items():
            if component_name not in self._component_types:
                raise ValidationError(
                    reason=(
                        f"Component type '{component_name}' not registered. "
                        "Call register_component_type() first."
                    ),
                    field="component_name",
                    value=component_name,
                )

            component_class = self._component_types[component_name]

            merged_data = {**component_data}
            if component_name in overrides:
                merged_data.update(overrides[component_name])

            component_instance = component_class(**merged_data)
            self._world.add_component(entity_id=entity_id, component=component_instance)

        return entity_id

    def instantiate_hierarchy(
        self, prefab_name: str, overrides: dict[str, dict[str, Any]] | None = None
    ) -> EntityID:
        """Create entity from prefab with all children.

        Args:
            prefab_name: Name of prefab to instantiate
            overrides: Component property overrides for root entity

        Returns:
            Root entity ID

        Raises:
            ValidationError: If prefab or any child prefab not found
        """
        if prefab_name not in self._prefabs:
            raise ValidationError(
                reason=f"Prefab '{prefab_name}' not found",
                field="prefab_name",
                value=prefab_name,
            )

        root_id = self.instantiate(prefab_name=prefab_name, overrides=overrides)

        prefab = self._prefabs[prefab_name]
        for child_name in prefab.children:
            self.instantiate_hierarchy(prefab_name=child_name)

        return root_id

    def load_from_dict(self, data: dict[str, Any]) -> list[str]:
        """Load prefabs from dictionary.

        Args:
            data: Dictionary with prefab definitions

        Returns:
            List of loaded prefab names

        Raises:
            ValueError: If data format invalid
        """
        loaded = []
        prefabs_data = data.get("prefabs", [])

        for prefab_data in prefabs_data:
            prefab = Prefab(
                name=prefab_data["name"],
                components=prefab_data.get("components", {}),
                behaviors=prefab_data.get("behaviors", []),
                children=prefab_data.get("children", []),
                metadata=prefab_data.get("metadata", {}),
            )
            self.register_prefab(prefab=prefab)
            loaded.append(prefab.name)

        return loaded

    def load_from_file(self, path: str | Path) -> list[str]:
        """Load prefabs from JSON or YAML file.

        Args:
            path: Path to prefab definition file (.json or .yaml/.yml)

        Returns:
            List of loaded prefab names

        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If file format not supported or data invalid
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Prefab file not found: {path}")

        suffix = file_path.suffix.lower()

        if suffix == ".json":
            with open(file_path) as f:
                data = json.load(f)
        elif suffix in {".yaml", ".yml"}:
            with open(file_path) as f:
                data = yaml.safe_load(f)
        else:
            raise ValidationError(
                reason=f"Unsupported file format: {suffix}. Use .json, .yaml, or .yml",
                field="path",
                value=suffix,
            )

        return self.load_from_dict(data=data)

    def get_prefab(self, name: str) -> Prefab:
        """Retrieve prefab definition.

        Args:
            name: Prefab name

        Returns:
            Prefab definition

        Raises:
            ValidationError: If prefab not found
        """
        if name not in self._prefabs:
            raise ValidationError(
                reason=f"Prefab '{name}' not found",
                field="name",
                value=name,
            )
        return self._prefabs[name]

    def has_prefab(self, name: str) -> bool:
        """Check if prefab exists.

        Args:
            name: Prefab name

        Returns:
            True if prefab registered, False otherwise
        """
        return name in self._prefabs

    def clear(self) -> None:
        """Remove all registered prefabs."""
        self._prefabs.clear()

    @property
    def prefab_count(self) -> int:
        """Get number of registered prefabs.

        Returns:
            Number of prefabs
        """
        return len(self._prefabs)

    @property
    def component_type_count(self) -> int:
        """Get number of registered component types.

        Returns:
            Number of component types
        """
        return len(self._component_types)

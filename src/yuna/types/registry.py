"""Type registry for managing entity type definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from yuna.exceptions import StateError, ValidationError
from yuna.types.type_object import EntityType

if TYPE_CHECKING:
    pass


class TypeRegistry:
    """Manages entity type definitions and creation.

    Responsibilities:
    - Store entity type definitions by name
    - Register new types
    - Retrieve type definitions
    - Load types from JSON/YAML configuration files
    - Validate type definitions

    Usage:
        registry = TypeRegistry()

        # Register type programmatically
        player_type = EntityType(
            name="player",
            components={"Position": {"x": 0.0, "y": 0.0}},
            behaviors=["movement"]
        )
        registry.register_type(entity_type=player_type)

        # Load types from file
        registry.load_from_file(path="entity_types.json")

        # Get type definition
        player_def = registry.get_type(name="player")
    """

    def __init__(self) -> None:
        self._types: dict[str, EntityType] = {}

    def register_type(self, entity_type: EntityType) -> None:
        """Register an entity type.

        Args:
            entity_type: Entity type definition to register

        Raises:
            StateError: If type with same name already exists
        """
        if entity_type.name in self._types:
            raise StateError(
                operation="register_type",
                reason=f"Entity type '{entity_type.name}' is already registered",
            )

        self._types[entity_type.name] = entity_type

    def get_type(self, name: str) -> EntityType:
        """Get entity type by name.

        Args:
            name: Name of entity type to retrieve

        Returns:
            Entity type definition

        Raises:
            ValidationError: If type with given name does not exist
        """
        if name not in self._types:
            raise ValidationError(
                reason=f"Entity type '{name}' not found in registry",
                field="name",
                value=name,
            )

        return self._types[name]

    def has_type(self, name: str) -> bool:
        """Check if type exists in registry.

        Args:
            name: Name of entity type to check

        Returns:
            True if type exists, False otherwise
        """
        return name in self._types

    def get_all_types(self) -> dict[str, EntityType]:
        """Get all registered types.

        Returns:
            Dictionary mapping type names to EntityType definitions
        """
        return self._types.copy()

    def unregister_type(self, name: str) -> None:
        """Remove entity type from registry.

        Args:
            name: Name of entity type to remove

        Raises:
            ValidationError: If type does not exist
        """
        if name not in self._types:
            raise ValidationError(
                reason=f"Entity type '{name}' not found in registry",
                field="name",
                value=name,
            )

        del self._types[name]

    def clear(self) -> None:
        """Remove all registered types."""
        self._types.clear()

    def load_from_dict(self, data: dict[str, Any]) -> None:
        """Load entity types from dictionary.

        Args:
            data: Dictionary with type definitions
                  Format: {"type_name": {"components": {...}, "behaviors": [...]}}

        Raises:
            ValidationError: If data format is invalid
        """
        if not isinstance(data, dict):
            raise ValidationError(
                reason="Data must be a dictionary",
                field="data",
                value=str(type(data)),
            )

        for type_name, type_data in data.items():
            if not isinstance(type_data, dict):
                raise ValidationError(
                    reason=f"Type data for '{type_name}' must be a dictionary",
                    field="type_data",
                    value=str(type(type_data)),
                )

            entity_type = EntityType(
                name=type_name,
                components=type_data.get("components", {}),
                behaviors=type_data.get("behaviors", []),
            )

            self.register_type(entity_type=entity_type)

    def load_from_json(self, json_string: str) -> None:
        """Load entity types from JSON string.

        Args:
            json_string: JSON string containing type definitions

        Raises:
            ValidationError: If JSON is invalid
        """
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValidationError(
                reason=f"Invalid JSON: {e}",
                field="json_string",
            ) from e

        self.load_from_dict(data=data)

    def load_from_yaml(self, yaml_string: str) -> None:
        """Load entity types from YAML string.

        Args:
            yaml_string: YAML string containing type definitions

        Raises:
            ValidationError: If YAML is invalid
        """
        try:
            data = yaml.safe_load(yaml_string)
        except yaml.YAMLError as e:
            raise ValidationError(
                reason=f"Invalid YAML: {e}",
                field="yaml_string",
            ) from e

        if data is None:
            data = {}

        self.load_from_dict(data=data)

    def load_from_file(self, path: str | Path) -> None:
        """Load entity types from JSON or YAML file.

        File format is determined by extension (.json or .yaml/.yml).

        Args:
            path: Path to configuration file

        Raises:
            ValidationError: If file format is not supported or invalid
            FileNotFoundError: If file does not exist
        """
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content = file_path.read_text()

        if file_path.suffix == ".json":
            self.load_from_json(json_string=content)
        elif file_path.suffix in {".yaml", ".yml"}:
            self.load_from_yaml(yaml_string=content)
        else:
            raise ValidationError(
                reason=(
                    f"Unsupported file format: {file_path.suffix}. Use .json, .yaml, "
                    "or .yml"
                ),
                field="path",
                value=str(file_path.suffix),
            )

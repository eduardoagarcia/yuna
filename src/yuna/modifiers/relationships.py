"""Modifier relationship types and helpers."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yuna.modifiers.modifier import Modifier


class RelationshipType(Enum):
    """Types of modifier relationships.

    Relationships define dependencies and interactions between modifiers:

    REQUIRES: Modifier only applies if target exists (dependency)
    BLOCKS: Modifier prevents target from applying (veto)
    REPLACES: Modifier removes target when applied (upgrade)
    TRIGGERS: Modifier injects additional modifier (cascade)
    EXCLUSIVE_WITH: Only one modifier can be active (mutex, strength-based)

    Relationships are entity-isolated - they only affect modifiers on the
    same entity. Processing order: REQUIRES → BLOCKS → REPLACES → TRIGGERS
    → EXCLUSIVE_WITH.
    """

    REQUIRES = auto()
    BLOCKS = auto()
    REPLACES = auto()
    TRIGGERS = auto()
    EXCLUSIVE_WITH = auto()


@dataclass(frozen=True)
class ModifierRelationship:
    """Relationship between modifiers.

    Attributes:
        relationship_type: Type of relationship
        target_modifier_id: Specific modifier ID (if applicable)
        target_tags: Tags to match (if applicable)
        target_category: Category to match (if applicable)
        strength: Relationship strength (for conflict resolution)

    Usage:
        # Requires specific modifier
        relationship = ModifierRelationship(
            relationship_type=RelationshipType.REQUIRES,
            target_modifier_id="power_source_active",
        )

        # Blocks by category
        relationship = ModifierRelationship(
            relationship_type=RelationshipType.BLOCKS,
            target_category="negative_status",
        )

        # Exclusive with category (higher strength wins)
        relationship = ModifierRelationship(
            relationship_type=RelationshipType.EXCLUSIVE_WITH,
            target_category="operation_mode",
            strength=2.0,
        )
    """

    relationship_type: RelationshipType
    target_modifier_id: str | None = None
    target_tags: frozenset[str] | None = None
    target_category: str | None = None
    strength: float = 1.0


class Relationships:
    """Factory for common modifier relationships.

    Provides helper methods to create ModifierRelationship instances with
    correct configuration. Each relationship type has three targeting modes:
    - by modifier_id: Targets specific modifier instance
    - by tag: Targets any modifier with matching tag
    - by category: Targets any modifier in category

    Common patterns:
    - Dependencies: Use requires_* for prerequisite modifiers
    - Immunity: Use blocks_* to prevent negative effects
    - Upgrades: Use replaces_* to remove old versions
    - Combos: Use triggers_modifier to create synergies
    - Modes: Use exclusive_with_category for mutually exclusive states

    All relationships are entity-scoped - they only interact with modifiers
    on the same entity. Higher strength wins in exclusive conflicts.
    """

    @staticmethod
    def requires_modifier(modifier_id: str) -> ModifierRelationship:
        """Require specific modifier to be active.

        Args:
            modifier_id: ID of required modifier

        Returns:
            Relationship requiring specific modifier

        Example:
            modifier = Modifier(
                ...,
                relationships=(
                    Relationships.requires_modifier("power_source"),
                ),
            )
        """
        return ModifierRelationship(
            relationship_type=RelationshipType.REQUIRES,
            target_modifier_id=modifier_id,
        )

    @staticmethod
    def requires_tag(tag: str) -> ModifierRelationship:
        """Require any modifier with tag to be active.

        Args:
            tag: Tag that must be present

        Returns:
            Relationship requiring tag

        Example:
            modifier = Modifier(
                ...,
                relationships=(
                    Relationships.requires_tag("powered_on"),
                ),
            )
        """
        return ModifierRelationship(
            relationship_type=RelationshipType.REQUIRES,
            target_tags=frozenset({tag}),
        )

    @staticmethod
    def requires_category(category: str) -> ModifierRelationship:
        """Require any modifier in category to be active.

        Args:
            category: Category that must be present

        Returns:
            Relationship requiring category

        Example:
            modifier = Modifier(
                ...,
                relationships=(
                    Relationships.requires_category("core_system"),
                ),
            )
        """
        return ModifierRelationship(
            relationship_type=RelationshipType.REQUIRES,
            target_category=category,
        )

    @staticmethod
    def blocks_modifier(modifier_id: str) -> ModifierRelationship:
        """Block specific modifier from being active.

        Args:
            modifier_id: ID of modifier to block

        Returns:
            Relationship blocking specific modifier

        Example:
            modifier = Modifier(
                ...,
                relationships=(
                    Relationships.blocks_modifier("low_power_mode"),
                ),
            )
        """
        return ModifierRelationship(
            relationship_type=RelationshipType.BLOCKS,
            target_modifier_id=modifier_id,
        )

    @staticmethod
    def blocks_tag(tag: str) -> ModifierRelationship:
        """Block all modifiers with tag.

        Args:
            tag: Tag to block

        Returns:
            Relationship blocking tag

        Example:
            modifier = Modifier(
                ...,
                relationships=(
                    Relationships.blocks_tag("debuff"),
                ),
            )
        """
        return ModifierRelationship(
            relationship_type=RelationshipType.BLOCKS,
            target_tags=frozenset({tag}),
        )

    @staticmethod
    def blocks_category(category: str) -> ModifierRelationship:
        """Block all modifiers in category.

        Args:
            category: Category to block

        Returns:
            Relationship blocking category

        Example:
            modifier = Modifier(
                ...,
                relationships=(
                    Relationships.blocks_category("negative_status"),
                ),
            )
        """
        return ModifierRelationship(
            relationship_type=RelationshipType.BLOCKS,
            target_category=category,
        )

    @staticmethod
    def replaces_modifier(modifier_id: str) -> ModifierRelationship:
        """Replace specific modifier.

        Args:
            modifier_id: ID of modifier to replace

        Returns:
            Relationship replacing specific modifier

        Example:
            modifier = Modifier(
                ...,
                relationships=(
                    Relationships.replaces_modifier("old_version"),
                ),
            )
        """
        return ModifierRelationship(
            relationship_type=RelationshipType.REPLACES,
            target_modifier_id=modifier_id,
        )

    @staticmethod
    def replaces_tag(tag: str) -> ModifierRelationship:
        """Replace older modifiers with tag.

        Args:
            tag: Tag to replace

        Returns:
            Relationship replacing tag

        Example:
            modifier = Modifier(
                ...,
                relationships=(
                    Relationships.replaces_tag("upgrade_v1"),
                ),
            )
        """
        return ModifierRelationship(
            relationship_type=RelationshipType.REPLACES,
            target_tags=frozenset({tag}),
        )

    @staticmethod
    def replaces_category(category: str) -> ModifierRelationship:
        """Replace modifiers in category.

        Args:
            category: Category to replace

        Returns:
            Relationship replacing category

        Example:
            modifier = Modifier(
                ...,
                relationships=(
                    Relationships.replaces_category("old_system"),
                ),
            )
        """
        return ModifierRelationship(
            relationship_type=RelationshipType.REPLACES,
            target_category=category,
        )

    @staticmethod
    def triggers_modifier(modifier: Modifier) -> ModifierRelationship:
        """Trigger another modifier when applied.

        Args:
            modifier: Modifier to trigger

        Returns:
            Relationship triggering modifier

        Example:
            triggered = Modifier(...)
            modifier = Modifier(
                ...,
                relationships=(
                    Relationships.triggers_modifier(triggered),
                ),
            )
        """
        return ModifierRelationship(
            relationship_type=RelationshipType.TRIGGERS,
            target_modifier_id=modifier.modifier_id,
        )

    @staticmethod
    def exclusive_with_modifier(
        modifier_id: str, strength: float = 1.0
    ) -> ModifierRelationship:
        """Mutually exclusive with specific modifier.

        Args:
            modifier_id: ID of modifier to be exclusive with
            strength: Strength for conflict resolution (higher wins)

        Returns:
            Relationship with mutual exclusivity

        Example:
            modifier = Modifier(
                ...,
                relationships=(
                    Relationships.exclusive_with_modifier("other_mode", strength=2.0),
                ),
            )
        """
        return ModifierRelationship(
            relationship_type=RelationshipType.EXCLUSIVE_WITH,
            target_modifier_id=modifier_id,
            strength=strength,
        )

    @staticmethod
    def exclusive_with_tag(tag: str, strength: float = 1.0) -> ModifierRelationship:
        """Mutually exclusive with modifiers having tag.

        Args:
            tag: Tag to be exclusive with
            strength: Strength for conflict resolution (higher wins)

        Returns:
            Relationship with mutual exclusivity

        Example:
            modifier = Modifier(
                ...,
                relationships=(
                    Relationships.exclusive_with_tag("incompatible", strength=1.5),
                ),
            )
        """
        return ModifierRelationship(
            relationship_type=RelationshipType.EXCLUSIVE_WITH,
            target_tags=frozenset({tag}),
            strength=strength,
        )

    @staticmethod
    def exclusive_with_category(
        category: str, strength: float = 1.0
    ) -> ModifierRelationship:
        """Mutually exclusive with category (only one can be active).

        Args:
            category: Category to be exclusive with
            strength: Strength for conflict resolution (higher wins)

        Returns:
            Relationship with mutual exclusivity

        Example:
            modifier = Modifier(
                ...,
                category="operation_mode",
                relationships=(
                    Relationships.exclusive_with_category("operation_mode"),
                ),
            )
        """
        return ModifierRelationship(
            relationship_type=RelationshipType.EXCLUSIVE_WITH,
            target_category=category,
            strength=strength,
        )

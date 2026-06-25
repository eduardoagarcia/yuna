"""Modifier dataclass for stat modifications."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from yuna.modifiers.types import (
    ModificationType,
    ModifierPriority,
)
from yuna.types.identifiers import EntityID

if TYPE_CHECKING:
    from yuna.modifiers.context import ModifierContext
    from yuna.modifiers.relationships import ModifierRelationship


@dataclass(frozen=True)
class StatEffect:
    """Secondary stat effect from a modifier.

    Represents additional stat modifications triggered by a primary modifier.
    Supports scaling based on another stat's value.

    Attributes:
        stat: Target stat name
        value: Modification value (base value before scaling)
        modification_type: How to apply value
        scaling_stat: Optional stat to scale value by (uses current stat value)
        scaling_factor: Multiplier for scaling stat value

    Usage:
        # Fixed value effect
        effect = StatEffect(
            stat="efficiency",
            value=5.0,
            modification_type=ModificationType.PERCENTAGE,
        )

        # Scaled effect: 10% of max_capacity → throughput
        effect = StatEffect(
            stat="throughput",
            value=0.0,
            modification_type=ModificationType.FLAT,
            scaling_stat="max_capacity",
            scaling_factor=0.10,
        )
    """

    stat: str
    value: float
    modification_type: ModificationType
    scaling_stat: str | None = None
    scaling_factor: float = 1.0


@dataclass(frozen=True)
class Modifier:
    """Immutable modifier for stat changes.

    Represents a pending modification to an entity's stat.

    Attributes:
        entity_id: Target entity
        stat: Name of stat to modify
        modification_type: How to apply value
        value: Modification value
        priority: Application priority
        source: System that created modifier
        duration_ticks: Auto-remove after N ticks (None = permanent)
        stacks: Number of stacks for this modifier
        max_stacks: Maximum stacks allowed from same source
        source_id: Entity that applied modifier (None if system-applied)
        modifier_id: Unique identifier for tracking
        tags: Semantic tags for filtering and bulk operations
        categories: Categories for grouping and stacking rules (can belong to multiple)
        display_group: UI/visual grouping identifier
        metadata: Additional key-value data for game-specific use
        activation_condition: Optional condition for modifier activation
        deactivation_condition: Optional condition for modifier deactivation
        secondary_effects: Additional stats affected by this modifier
        cascade_modifiers: Modifiers spawned when this modifier is applied
        value_calculator: Optional function to calculate dynamic value
        curve_function: Optional non-linear transformation of value
        time_interpolation: Optional time-based interpolation method
        relationships: Modifier relationships (requires, blocks, etc.)

    Usage:
        modifier = Modifier(
            entity_id="player_1",
            stat="health",
            modification_type=ModificationType.FLAT,
            value=10.0,
            priority=ModifierPriority.NORMAL,
            source="healing_system",
            duration_ticks=50,
            modifier_id="heal_buff_1",
            tags=frozenset({"buff", "temporary"}),
            categories=("healing",),
        )
    """

    entity_id: EntityID
    stat: str
    modification_type: ModificationType
    value: float
    priority: ModifierPriority
    source: str
    duration_ticks: int | None = None
    stacks: int = 1
    max_stacks: int | None = None
    source_id: EntityID | None = None
    modifier_id: str | None = None
    tags: frozenset[str] = frozenset()
    categories: tuple[str, ...] = ()
    display_group: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    activation_condition: Callable[[ModifierContext], bool] | None = None
    deactivation_condition: Callable[[ModifierContext], bool] | None = None
    secondary_effects: tuple[StatEffect, ...] = ()
    cascade_modifiers: tuple[Modifier, ...] = ()
    value_calculator: Callable[[float, ModifierContext], float] | None = None
    curve_function: Callable[[float], float] | None = None
    time_interpolation: str | None = None
    relationships: tuple[ModifierRelationship, ...] = ()

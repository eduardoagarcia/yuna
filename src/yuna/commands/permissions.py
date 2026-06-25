"""Action permission types for multi-dimensional resource requirements."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto

from yuna.modifiers.types import ModificationType


class ResourceModificationType(Enum):
    """How resource effect modifies resource value.

    Values:
        SET: Replace resource with value
        FLAT: Add/subtract value (positive = gain, negative = cost)
        PERCENTAGE: Modify by percentage of current value
        MULTIPLIER: Multiply current value
    """

    SET = auto()
    FLAT = auto()
    PERCENTAGE = auto()
    MULTIPLIER = auto()


RESOURCE_TO_MODIFIER_TYPE_MAP: dict[ResourceModificationType, ModificationType] = {
    ResourceModificationType.SET: ModificationType.SET,
    ResourceModificationType.FLAT: ModificationType.FLAT,
    ResourceModificationType.PERCENTAGE: ModificationType.PERCENTAGE,
    ResourceModificationType.MULTIPLIER: ModificationType.MULTIPLIER,
}


@dataclass(frozen=True)
class ResourceEffect:
    """Effect on a single resource.

    Can represent costs (negative), gains (positive), or other operations.
    Validation only checks negative effects (costs). Positive effects (gains)
    always succeed and may exceed resource maximums - game systems handle overflow.

    Attributes:
        resource_type: Identifier for resource (e.g., "energy", "heat")
        modification_type: How to apply the effect
        amount: Effect magnitude (negative = cost, positive = gain)
        condition_modifier: Optional function to modify amount based on context
        tags: Semantic tags for this effect
        categories: Optional categories for modifier stacking rules
            (can belong to multiple)

    Usage:
        # Cost 10 energy
        energy_cost = ResourceEffect(
            resource_type="energy",
            modification_type=ResourceModificationType.FLAT,
            amount=-10.0,
        )

        # Generate 5 heat (side effect)
        heat_gain = ResourceEffect(
            resource_type="heat",
            modification_type=ResourceModificationType.FLAT,
            amount=5.0,
        )

        # Consume 50% of current stamina
        stamina_cost = ResourceEffect(
            resource_type="stamina",
            modification_type=ResourceModificationType.PERCENTAGE,
            amount=-0.50,
        )

        # Conditional cost (half cost if condition met)
        conditional_cost = ResourceEffect(
            resource_type="energy",
            modification_type=ResourceModificationType.FLAT,
            amount=-20.0,
            condition_modifier=lambda amt: amt * 0.5 if condition else amt,
        )

        # With categories for stacking
        categorized_cost = ResourceEffect(
            resource_type="energy",
            modification_type=ResourceModificationType.FLAT,
            amount=-15.0,
            tags=frozenset({"combat"}),
            categories=("energy.drain.combat",),
        )
    """

    resource_type: str
    modification_type: ResourceModificationType
    amount: float
    condition_modifier: Callable[[float], float] | None = None
    tags: frozenset[str] = frozenset()
    categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActionPermission:
    """Permission requirements for action execution.

    Defines all requirements an entity must meet to execute an action,
    including resource effects (costs and gains), stat requirements, and
    tag constraints.

    Attributes:
        resource_effects: Tuple of resource modifications (costs and gains)
        required_stats: Minimum stat values required
        forbidden_tags: Entity cannot have these tags
        required_tags: Entity must have these tags
        cooldown_ticks: Minimum ticks between executions
        max_uses_per_tick: Maximum uses in single tick

    Usage:
        simple_permission = ActionPermission(
            resource_effects=(
                ResourceEffect(
                    resource_type="energy",
                    modification_type=ResourceModificationType.FLAT,
                    amount=-10.0,
                ),
            ),
        )

        complex_permission = ActionPermission(
            resource_effects=(
                ResourceEffect(
                    resource_type="energy",
                    modification_type=ResourceModificationType.FLAT,
                    amount=-25.0,
                ),
                ResourceEffect(
                    resource_type="heat",
                    modification_type=ResourceModificationType.FLAT,
                    amount=5.0,
                ),
                ResourceEffect(
                    resource_type="action_points",
                    modification_type=ResourceModificationType.FLAT,
                    amount=-1.0,
                ),
            ),
            required_stats={"strength": 10.0, "intelligence": 5.0},
            forbidden_tags=frozenset({"stunned", "disabled"}),
            required_tags=frozenset({"alive"}),
            cooldown_ticks=100,
            max_uses_per_tick=1,
        )
    """

    resource_effects: tuple[ResourceEffect, ...] = ()
    required_stats: dict[str, float] = field(default_factory=dict)
    forbidden_tags: frozenset[str] = frozenset()
    required_tags: frozenset[str] = frozenset()
    cooldown_ticks: int = 0
    max_uses_per_tick: int | None = None

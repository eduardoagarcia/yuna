"""Modifier types and enums."""

from enum import Enum, StrEnum, auto


class ModificationType(Enum):
    """Type of stat modification.

    Determines how modifier value is applied to stat.

    Values:
        SET: Replace stat with value
        FLAT: Add value to stat
        PERCENTAGE: Add percentage of base value
        MULTIPLIER: Multiply final value
    """

    SET = auto()
    FLAT = auto()
    PERCENTAGE = auto()
    MULTIPLIER = auto()


class ModifierPriority(Enum):
    """Priority for modifier application.

    Higher priority modifiers process first.

    Values:
        CRITICAL: Highest priority (0)
        HIGH: High priority (100)
        NORMAL: Normal priority (200)
        LOW: Lowest priority (300)
    """

    CRITICAL = 0
    HIGH = 100
    NORMAL = 200
    LOW = 300


class ModifierStage(StrEnum):
    """Standard modifier pipeline stage names.

    String enum matching actual stage.name values.
    Defined in execution order for clarity.

    Pipeline Flow:
        1. COLLECT: Gather queued modifiers
        2. FILTER: Validate stats exist
        3. CONDITION: Check activation/deactivation conditions
        4. EXPANSION: Inject secondary effects and cascades
        5. SCALING: Apply value transformations and calculations
        6. RELATIONSHIP: Resolve modifier dependencies
        7. SORT: Order by priority
        8. GROUP: Organize by entity and stat
        9. STACK: Apply stacking rules (FLAT, MULTIPLIER, etc.)
        10. INTERCEPT: Intercept and reroute final stat values
        11. CLAMP: Enforce min/max bounds
        12. APPLY: Write final values to world components

    Usage:
        pipeline.insert_stage_after(
            after=ModifierStage.STACK,
            stage=CustomStage()
        )
    """

    COLLECT = "collect"
    FILTER = "filter"
    CONDITION = "condition"
    EXPANSION = "expansion"
    SCALING = "scaling"
    RELATIONSHIP = "relationship"
    SORT = "sort"
    GROUP = "group"
    STACK = "stack"
    INTERCEPT = "intercept"
    CLAMP = "clamp"
    APPLY = "apply"

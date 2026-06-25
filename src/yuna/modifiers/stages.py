"""Modifier pipeline stages."""

from dataclasses import replace

from yuna.config.component import ConfigNamespaceComponent
from yuna.modifiers.config import (
    CategoryStackingConfig,
    StackingRule,
    StatConfig,
)
from yuna.modifiers.context import ModifierContext
from yuna.modifiers.modifier import Modifier, StatEffect
from yuna.modifiers.relationships import RelationshipType
from yuna.modifiers.scaling import TimeInterpolation
from yuna.modifiers.types import ModificationType
from yuna.pipeline.context import PipelineContext
from yuna.pipeline.stage import PipelineStage
from yuna.profiling.monitor import get_performance_monitor
from yuna.types.identifiers import EntityID


def modifier_sort_key(modifier: Modifier) -> tuple[int, EntityID, str, str, int, str]:
    """Deterministic cross-thread ordering key for modifiers.

    Excludes ``value`` (a float) so ordering stays stable no matter
    which concurrent producer threads queued the modifiers; see the
    engine determinism rules.
    """
    return (
        modifier.priority.value,
        modifier.entity_id,
        modifier.stat,
        modifier.source,
        modifier.modification_type.value,
        modifier.source_id or "",
    )


class CollectStage(PipelineStage[ModifierContext, ModifierContext, PipelineContext]):
    """Collect queued modifiers (pass-through stage)."""

    def __init__(self, profiling_enabled: bool = False) -> None:
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    @property
    def name(self) -> str:
        return "collect"

    def process(
        self,
        value: ModifierContext,
        context: PipelineContext,
    ) -> ModifierContext:
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="modifier_stage", name="collect"):
                return value
        return value


class FilterStage(PipelineStage[ModifierContext, ModifierContext, PipelineContext]):
    """Filter out invalid modifiers."""

    def __init__(self, profiling_enabled: bool = False) -> None:
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    @property
    def name(self) -> str:
        return "filter"

    def process(
        self,
        value: ModifierContext,
        context: PipelineContext,
    ) -> ModifierContext:
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="modifier_stage", name="filter"):
                return self._execute_filter(modifier_context=value)
        return self._execute_filter(modifier_context=value)

    @staticmethod
    def _execute_filter(modifier_context: ModifierContext) -> ModifierContext:
        valid_modifiers = [
            m
            for m in modifier_context.modifiers
            if modifier_context.config.has_stat(name=m.stat)
        ]
        modifier_context.modifiers = valid_modifiers
        return modifier_context


class ConditionStage(PipelineStage[ModifierContext, ModifierContext, PipelineContext]):
    """Evaluate modifier activation conditions.

    Filters out modifiers whose activation conditions fail or
    deactivation conditions succeed.

    Stage Position: After Filter, before Sort
    """

    def __init__(self, profiling_enabled: bool = False) -> None:
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    @property
    def name(self) -> str:
        return "condition"

    def process(
        self,
        value: ModifierContext,
        context: PipelineContext,
    ) -> ModifierContext:
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="modifier_stage", name="condition"):
                return self._execute_condition(modifier_context=value)
        return self._execute_condition(modifier_context=value)

    @staticmethod
    def _execute_condition(modifier_context: ModifierContext) -> ModifierContext:
        active_modifiers = []

        for modifier in modifier_context.modifiers:
            should_activate = True

            modifier_context.entity_id = modifier.entity_id

            if modifier.activation_condition is not None:
                should_activate = modifier.activation_condition(modifier_context)

            if should_activate and modifier.deactivation_condition is not None:
                should_activate = not modifier.deactivation_condition(modifier_context)

            if should_activate:
                active_modifiers.append(modifier)

        modifier_context.modifiers = active_modifiers
        modifier_context.entity_id = None
        return modifier_context


class SortStage(PipelineStage[ModifierContext, ModifierContext, PipelineContext]):
    """Sort modifiers by priority."""

    def __init__(self, profiling_enabled: bool = False) -> None:
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    @property
    def name(self) -> str:
        return "sort"

    def process(
        self,
        value: ModifierContext,
        context: PipelineContext,
    ) -> ModifierContext:
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="modifier_stage", name="sort"):
                return self._execute_sort(modifier_context=value)
        return self._execute_sort(modifier_context=value)

    @staticmethod
    def _execute_sort(modifier_context: ModifierContext) -> ModifierContext:
        modifier_context.modifiers = sorted(
            modifier_context.modifiers, key=modifier_sort_key
        )
        return modifier_context


class GroupStage(PipelineStage[ModifierContext, ModifierContext, PipelineContext]):
    """Group modifiers by entity and stat."""

    def __init__(self, profiling_enabled: bool = False) -> None:
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    @property
    def name(self) -> str:
        return "group"

    def process(
        self,
        value: ModifierContext,
        context: PipelineContext,
    ) -> ModifierContext:
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="modifier_stage", name="group"):
                return self._execute_group(modifier_context=value)
        return self._execute_group(modifier_context=value)

    @staticmethod
    def _execute_group(modifier_context: ModifierContext) -> ModifierContext:
        grouped: dict[tuple[EntityID, str], list[Modifier]] = {}
        for modifier in modifier_context.modifiers:
            key = (modifier.entity_id, modifier.stat)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(modifier)
        modifier_context.grouped = grouped
        return modifier_context


class StackStage(PipelineStage[ModifierContext, ModifierContext, PipelineContext]):
    """Apply stacking rules to compute final values."""

    def __init__(self, profiling_enabled: bool = False) -> None:
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    @property
    def name(self) -> str:
        return "stack"

    def process(
        self,
        value: ModifierContext,
        context: PipelineContext,
    ) -> ModifierContext:
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="modifier_stage", name="stack"):
                return self._execute_stack(modifier_context=value)
        return self._execute_stack(modifier_context=value)

    @staticmethod
    def _compute_multiplier(
        modifiers: list[Modifier], stacking_rule: StackingRule
    ) -> float:
        if stacking_rule == StackingRule.ADD:
            return sum(m.value for m in modifiers)
        if stacking_rule == StackingRule.MULTIPLY:
            result = 1.0
            for m in modifiers:
                result *= m.value
            return result
        return 1.0

    @staticmethod
    def _group_by_category(
        modifiers: list[Modifier],
    ) -> dict[str | None, list[Modifier]]:
        by_category: dict[str | None, list[Modifier]] = {}
        for modifier in modifiers:
            if not modifier.categories:
                if None not in by_category:
                    by_category[None] = []
                by_category[None].append(modifier)
            else:
                for category in modifier.categories:
                    if category not in by_category:
                        by_category[category] = []
                    by_category[category].append(modifier)
        return by_category

    @staticmethod
    def _process_category_modifiers(
        category_mods: list[Modifier],
        category_config: CategoryStackingConfig | None,
        stat_config: StatConfig,
    ) -> tuple[float | None, list[Modifier], bool]:
        """Resolve stacked modifiers for a single category.

        SET modifiers override all other types. The winning SET is the
        last one in sort order (lowest priority applies last), matching
        the pre-existing precedence. When several SET modifiers share an
        identical cross-thread sort key (priority, entity, stat, source,
        type, source_id) and differ only in value, sort order alone
        cannot break the tie, so the highest value among that tied group
        wins. This keeps resolution deterministic regardless of the
        order in which concurrent producer threads queued the modifiers.
        """
        flat_mods = [
            m for m in category_mods if m.modification_type == ModificationType.FLAT
        ]
        percentage_mods = [
            m
            for m in category_mods
            if m.modification_type == ModificationType.PERCENTAGE
        ]
        multiplier_mods = [
            m
            for m in category_mods
            if m.modification_type == ModificationType.MULTIPLIER
        ]
        set_mods = [
            m for m in category_mods if m.modification_type == ModificationType.SET
        ]

        if set_mods:
            keyed_values = [(modifier_sort_key(modifier=m), m.value) for m in set_mods]
            winning_key = max(key for key, _ in keyed_values)
            return (
                max(value for key, value in keyed_values if key == winning_key),
                [],
                True,
            )

        has_additive_mods = bool(flat_mods or percentage_mods)
        if multiplier_mods and not has_additive_mods:
            return None, multiplier_mods, False

        category_value = sum(m.value for m in flat_mods)
        if percentage_mods:
            percentage_sum = sum(m.value for m in percentage_mods)
            category_value += category_value * percentage_sum

        if multiplier_mods:
            stacking_rule = (
                category_config.stacking_rule
                if category_config
                else stat_config.stacking_rule
            )
            category_value *= StackStage._compute_multiplier(
                modifiers=multiplier_mods, stacking_rule=stacking_rule
            )

        return category_value, [], False

    @staticmethod
    def _compute_base_value(
        entity_id: EntityID, stat: str, modifier_context: ModifierContext
    ) -> float:
        reader = modifier_context.config.get_value_reader(stat=stat)
        if reader and modifier_context.world:
            return reader(entity_id=entity_id, stat=stat, world=modifier_context.world)
        return 0.0

    @staticmethod
    def _execute_stack(modifier_context: ModifierContext) -> ModifierContext:
        final_values: dict[tuple[EntityID, str], float] = {}
        for key, modifiers in sorted(modifier_context.grouped.items()):
            entity_id, stat = key
            stat_config = modifier_context.config.get_stat_config(name=stat)
            base_value = StackStage._compute_base_value(
                entity_id=entity_id, stat=stat, modifier_context=modifier_context
            )

            category_results: list[float] = []
            stat_multipliers: list[Modifier] = []
            has_set_modifier = False
            set_value = 0.0

            for category, category_mods in sorted(
                StackStage._group_by_category(modifiers=modifiers).items(),
                key=lambda item: item[0] or "",
            ):
                category_config = (
                    modifier_context.config.get_category_stacking(category=category)
                    if category
                    else None
                )
                result, multipliers, is_set = StackStage._process_category_modifiers(
                    category_mods=category_mods,
                    category_config=category_config,
                    stat_config=stat_config,
                )
                if is_set:
                    has_set_modifier = True
                    set_value = result if result is not None else 0.0
                elif result is not None:
                    category_results.append(result)
                stat_multipliers.extend(multipliers)

            if has_set_modifier:
                final_values[key] = set_value
            else:
                base_value += sum(category_results)
                if stat_multipliers:
                    base_value *= StackStage._compute_multiplier(
                        modifiers=stat_multipliers,
                        stacking_rule=stat_config.stacking_rule,
                    )
                final_values[key] = base_value
        modifier_context.final_values = final_values
        return modifier_context


class InterceptStage(PipelineStage[ModifierContext, ModifierContext, PipelineContext]):
    """Intercept final stat values before clamping/application.

    Allows games to intercept calculated stat values and reroute them
    to alternative destinations. Common use cases:
    - Damage routing (shield → armor → health)
    - Resource pooling (auxiliary battery → primary battery)
    - Stat stealing (drain enemy, heal self)
    - Overflow handling (excess healing → shield)

    Pipeline Position:
        After STACK (sees final stacked values)
        Before CLAMP (can produce out-of-bounds values that get clamped)

    Performance:
        O(1) interceptor lookup per stat
        Only processes stats with registered interceptors
    """

    def __init__(self, profiling_enabled: bool = False) -> None:
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    @property
    def name(self) -> str:
        return "intercept"

    def process(
        self,
        value: ModifierContext,
        context: PipelineContext,
    ) -> ModifierContext:
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="modifier_stage", name="intercept"):
                return self._execute_intercept(modifier_context=value)
        return self._execute_intercept(modifier_context=value)

    @staticmethod
    def _execute_intercept(modifier_context: ModifierContext) -> ModifierContext:
        if modifier_context.world is None:
            return modifier_context

        for (entity_id, stat), final_value in sorted(
            modifier_context.final_values.items()
        ):
            interceptors = modifier_context.config.get_interceptors(stat=stat)

            value = final_value
            for interceptor in interceptors:
                value = interceptor(
                    entity_id=entity_id,
                    stat=stat,
                    value=value,
                    context=modifier_context,
                )

            modifier_context.final_values[(entity_id, stat)] = value

        return modifier_context


class ClampStage(PipelineStage[ModifierContext, ModifierContext, PipelineContext]):
    """Clamp values to min/max bounds."""

    def __init__(self, profiling_enabled: bool = False) -> None:
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    @property
    def name(self) -> str:
        return "clamp"

    def process(
        self,
        value: ModifierContext,
        context: PipelineContext,
    ) -> ModifierContext:
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="modifier_stage", name="clamp"):
                return self._execute_clamp(modifier_context=value)
        return self._execute_clamp(modifier_context=value)

    @staticmethod
    def _execute_clamp(modifier_context: ModifierContext) -> ModifierContext:
        clamped_values: dict[tuple[EntityID, str], float] = {}
        for key, value in sorted(modifier_context.final_values.items()):
            entity_id, stat = key
            min_value, max_value = ClampStage._get_clamp_bounds(
                modifier_context=modifier_context,
                entity_id=entity_id,
                stat=stat,
            )
            clamped = max(min_value, min(max_value, value))
            stat_config = modifier_context.config.get_stat_config(name=stat)
            if stat_config.precision is not None:
                clamped = round(clamped, stat_config.precision)
            clamped_values[key] = clamped
        modifier_context.final_values = clamped_values
        return modifier_context

    @staticmethod
    def _get_clamp_bounds(
        modifier_context: ModifierContext,
        entity_id: EntityID,
        stat: str,
    ) -> tuple[float, float]:
        """Get entity-specific clamp bounds from config namespace or fall back.

        Returns:
            Tuple of (min_value, max_value) for clamping
        """
        if modifier_context.world:
            try:
                namespace_component = modifier_context.world.get_component(
                    entity_id=entity_id,
                    component_type=ConfigNamespaceComponent,
                )
                if namespace_component:
                    config_key = f"{namespace_component.namespace}.{stat}"
                    min_value = modifier_context.world.config.get_min(key=config_key)
                    max_value = modifier_context.world.config.get_max(key=config_key)
                    if min_value is not None and max_value is not None:
                        return float(min_value), float(max_value)
            except Exception:
                pass

        stat_config = modifier_context.config.get_stat_config(name=stat)
        return stat_config.min_value, stat_config.max_value


class ExpansionStage(PipelineStage[ModifierContext, ModifierContext, PipelineContext]):
    """Expand modifiers with secondary effects and cascades.

    Handles:
    - Secondary stat effects expansion
    - Scaling calculations based on current stat values
    - Cascade modifier injection
    - Recursion depth limiting

    Stage Position: After Condition, before Sort
    """

    def __init__(
        self, profiling_enabled: bool = False, max_cascade_depth: int = 5
    ) -> None:
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None
        self._max_cascade_depth = max_cascade_depth

    @property
    def name(self) -> str:
        return "expansion"

    def process(
        self,
        value: ModifierContext,
        context: PipelineContext,
    ) -> ModifierContext:
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="modifier_stage", name="expansion"):
                return self._execute_expansion(modifier_context=value)
        return self._execute_expansion(modifier_context=value)

    @staticmethod
    def _execute_expansion(modifier_context: ModifierContext) -> ModifierContext:
        expanded_modifiers = []
        cascade_depth = 0

        for modifier in modifier_context.modifiers:
            expanded_modifiers.append(modifier)

            for effect in modifier.secondary_effects:
                secondary = ExpansionStage._create_secondary_modifier(
                    primary=modifier,
                    effect=effect,
                    context=modifier_context,
                )
                expanded_modifiers.append(secondary)

            for cascade in modifier.cascade_modifiers:
                if cascade_depth < 5:
                    expanded_modifiers.append(cascade)
                    cascade_depth += 1

        modifier_context.modifiers = expanded_modifiers
        return modifier_context

    @staticmethod
    def _create_secondary_modifier(
        primary: Modifier,
        effect: StatEffect,
        context: ModifierContext,
    ) -> Modifier:
        """Create modifier from secondary effect with scaling."""
        final_value = effect.value

        if effect.scaling_stat and context.world:
            scaling_value = context.world.get_stat(
                entity_id=primary.entity_id, stat=effect.scaling_stat
            )
            final_value += scaling_value * effect.scaling_factor

        return Modifier(
            entity_id=primary.entity_id,
            stat=effect.stat,
            modification_type=effect.modification_type,
            value=final_value,
            priority=primary.priority,
            source=f"{primary.source}:secondary",
            duration_ticks=primary.duration_ticks,
            source_id=primary.source_id,
            tags=primary.tags,
            categories=primary.categories,
            display_group=primary.display_group,
        )


class ScalingStage(PipelineStage[ModifierContext, ModifierContext, PipelineContext]):
    """Apply scaling functions and value interpolation.

    Processes modifiers with:
    - value_calculator: Custom value calculation
    - curve_function: Non-linear value transformation
    - time_interpolation: Time-based value ramping

    Stage Position: After Expansion, before Sort
    """

    def __init__(self, profiling_enabled: bool = False) -> None:
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    @property
    def name(self) -> str:
        return "scaling"

    def process(
        self,
        value: ModifierContext,
        context: PipelineContext,
    ) -> ModifierContext:
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="modifier_stage", name="scaling"):
                return self._execute_scaling(modifier_context=value)
        return self._execute_scaling(modifier_context=value)

    @staticmethod
    def _execute_scaling(modifier_context: ModifierContext) -> ModifierContext:
        scaled_modifiers = []

        for modifier in modifier_context.modifiers:
            scaled_value = modifier.value

            modifier_context.entity_id = modifier.entity_id

            if modifier.value_calculator is not None:
                scaled_value = modifier.value_calculator(scaled_value, modifier_context)

            if modifier.curve_function is not None:
                scaled_value = modifier.curve_function(scaled_value)

            if modifier.time_interpolation is not None:
                progress = ScalingStage._calculate_time_progress(
                    modifier=modifier, context=modifier_context
                )
                scaled_value = TimeInterpolation.interpolate(
                    start_value=0.0,
                    end_value=modifier.value,
                    progress=progress,
                    method=modifier.time_interpolation,
                )

            if scaled_value != modifier.value:
                scaled_modifier = replace(modifier, value=scaled_value)
                scaled_modifiers.append(scaled_modifier)
            else:
                scaled_modifiers.append(modifier)

        modifier_context.entity_id = None
        modifier_context.modifiers = scaled_modifiers
        return modifier_context

    @staticmethod
    def _calculate_time_progress(modifier: Modifier, context: ModifierContext) -> float:
        """Calculate time progress [0, 1] for time interpolation."""
        if modifier.duration_ticks is None or modifier.duration_ticks == 0:
            return 1.0

        elapsed = context.current_tick
        progress = elapsed / modifier.duration_ticks
        return max(0.0, min(1.0, progress))


class RelationshipStage(
    PipelineStage[ModifierContext, ModifierContext, PipelineContext]
):
    """Resolve modifier relationships and dependencies.

    Handles:
    - REQUIRES: Remove modifiers missing prerequisites
    - BLOCKS: Remove modifiers blocked by active modifiers
    - REPLACES: Remove older modifiers being replaced
    - TRIGGERS: Inject triggered modifiers
    - EXCLUSIVE_WITH: Resolve mutual exclusivity

    Stage Position: After Scaling, before Sort
    """

    def __init__(self, profiling_enabled: bool = False) -> None:
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    @property
    def name(self) -> str:
        return "relationship"

    def process(
        self,
        value: ModifierContext,
        context: PipelineContext,
    ) -> ModifierContext:
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="modifier_stage", name="relationship"):
                return self._execute_relationship(modifier_context=value)
        return self._execute_relationship(modifier_context=value)

    @staticmethod
    def _execute_relationship(modifier_context: ModifierContext) -> ModifierContext:
        entity_groups: dict[EntityID, list[Modifier]] = {}
        for modifier in modifier_context.modifiers:
            if modifier.entity_id not in entity_groups:
                entity_groups[modifier.entity_id] = []
            entity_groups[modifier.entity_id].append(modifier)

        final_modifiers: list[Modifier] = []
        for _entity_id, entity_modifiers in sorted(entity_groups.items()):
            valid_modifiers = RelationshipStage._resolve_requirements(
                modifiers=entity_modifiers,
            )

            valid_modifiers = RelationshipStage._resolve_blocks(
                modifiers=valid_modifiers,
            )

            valid_modifiers = RelationshipStage._resolve_replacements(
                modifiers=valid_modifiers,
            )

            all_modifiers = RelationshipStage._inject_triggered(
                modifiers=valid_modifiers,
            )

            entity_final = RelationshipStage._resolve_exclusivity(
                modifiers=all_modifiers,
            )

            final_modifiers.extend(entity_final)

        modifier_context.modifiers = final_modifiers
        return modifier_context

    @staticmethod
    def _resolve_requirements(modifiers: list[Modifier]) -> list[Modifier]:
        valid_modifiers = []

        for modifier in modifiers:
            has_all_requirements = True

            for relationship in modifier.relationships:
                if relationship.relationship_type != RelationshipType.REQUIRES:
                    continue

                requirement_met = RelationshipStage._check_requirement(
                    relationship=relationship,
                    modifiers=modifiers,
                )

                if not requirement_met:
                    has_all_requirements = False
                    break

            if has_all_requirements:
                valid_modifiers.append(modifier)

        return valid_modifiers

    @staticmethod
    def _check_requirement(relationship, modifiers: list[Modifier]) -> bool:
        for other in modifiers:
            if (
                relationship.target_modifier_id
                and other.modifier_id == relationship.target_modifier_id
            ):
                return True

            if relationship.target_tags and relationship.target_tags & other.tags:
                return True

            if (
                relationship.target_category
                and relationship.target_category in other.categories
            ):
                return True

        return False

    @staticmethod
    def _resolve_blocks(modifiers: list[Modifier]) -> list[Modifier]:
        blocked_modifiers = set()

        for modifier in modifiers:
            for relationship in modifier.relationships:
                if relationship.relationship_type != RelationshipType.BLOCKS:
                    continue

                for other in modifiers:
                    if other is modifier:
                        continue

                    if RelationshipStage._matches_target(
                        relationship=relationship, modifier=other
                    ):
                        blocked_modifiers.add(id(other))

        return [m for m in modifiers if id(m) not in blocked_modifiers]

    @staticmethod
    def _matches_target(relationship, modifier: Modifier) -> bool:
        if (
            relationship.target_modifier_id
            and modifier.modifier_id == relationship.target_modifier_id
        ):
            return True

        if relationship.target_tags and relationship.target_tags & modifier.tags:
            return True

        if (
            relationship.target_category
            and relationship.target_category in modifier.categories
        ):
            return True

        return False

    @staticmethod
    def _resolve_replacements(modifiers: list[Modifier]) -> list[Modifier]:
        replaced_modifiers = set()

        for modifier in modifiers:
            for relationship in modifier.relationships:
                if relationship.relationship_type != RelationshipType.REPLACES:
                    continue

                for other in modifiers:
                    if other is modifier:
                        continue

                    if RelationshipStage._matches_target(
                        relationship=relationship, modifier=other
                    ):
                        replaced_modifiers.add(id(other))

        return [m for m in modifiers if id(m) not in replaced_modifiers]

    @staticmethod
    def _inject_triggered(modifiers: list[Modifier]) -> list[Modifier]:
        return modifiers

    @staticmethod
    def _resolve_exclusivity(modifiers: list[Modifier]) -> list[Modifier]:
        excluded_modifiers: set[int] = set()
        processed_groups: dict[str, Modifier] = {}

        for modifier in modifiers:
            for relationship in modifier.relationships:
                if relationship.relationship_type != RelationshipType.EXCLUSIVE_WITH:
                    continue

                RelationshipStage._process_exclusive_relationship(
                    modifier=modifier,
                    relationship=relationship,
                    modifiers=modifiers,
                    excluded_modifiers=excluded_modifiers,
                    processed_groups=processed_groups,
                )

        return [m for m in modifiers if id(m) not in excluded_modifiers]

    @staticmethod
    def _process_exclusive_relationship(
        modifier: Modifier,
        relationship,
        modifiers: list[Modifier],
        excluded_modifiers: set[int],
        processed_groups: dict[str, Modifier],
    ) -> None:
        if relationship.target_modifier_id:
            RelationshipStage._resolve_exclusive_modifier(
                modifier=modifier,
                relationship=relationship,
                modifiers=modifiers,
                excluded_modifiers=excluded_modifiers,
            )
        elif relationship.target_tags:
            RelationshipStage._resolve_exclusive_tags(
                modifier=modifier,
                relationship=relationship,
                modifiers=modifiers,
                excluded_modifiers=excluded_modifiers,
            )
        elif relationship.target_category:
            RelationshipStage._resolve_exclusive_category(
                modifier=modifier,
                relationship=relationship,
                excluded_modifiers=excluded_modifiers,
                processed_groups=processed_groups,
            )

    @staticmethod
    def _resolve_exclusive_modifier(
        modifier: Modifier,
        relationship,
        modifiers: list[Modifier],
        excluded_modifiers: set[int],
    ) -> None:
        for other in modifiers:
            if (
                other.modifier_id == relationship.target_modifier_id
                and id(other) not in excluded_modifiers
            ):
                other_strength = (
                    RelationshipStage._get_exclusivity_strength_for_modifier(
                        modifier=other, target_id=modifier.modifier_id
                    )
                )
                current_strength = relationship.strength

                if current_strength > other_strength:
                    excluded_modifiers.add(id(other))
                else:
                    excluded_modifiers.add(id(modifier))

    @staticmethod
    def _resolve_exclusive_tags(
        modifier: Modifier,
        relationship,
        modifiers: list[Modifier],
        excluded_modifiers: set[int],
    ) -> None:
        for other in modifiers:
            if (
                relationship.target_tags & other.tags
                and id(other) not in excluded_modifiers
                and other is not modifier
            ):
                other_strength = RelationshipStage._get_exclusivity_strength_for_tags(
                    modifier=other, target_tags=modifier.tags
                )
                current_strength = relationship.strength

                if current_strength > other_strength:
                    excluded_modifiers.add(id(other))
                else:
                    excluded_modifiers.add(id(modifier))

    @staticmethod
    def _resolve_exclusive_category(
        modifier: Modifier,
        relationship,
        excluded_modifiers: set[int],
        processed_groups: dict[str, Modifier],
    ) -> None:
        existing = processed_groups.get(relationship.target_category)
        if existing is None:
            processed_groups[relationship.target_category] = modifier
        else:
            existing_strength = RelationshipStage._get_exclusivity_strength(
                modifier=existing,
                category=relationship.target_category,
            )
            current_strength = relationship.strength

            if current_strength > existing_strength:
                excluded_modifiers.add(id(existing))
                processed_groups[relationship.target_category] = modifier
            else:
                excluded_modifiers.add(id(modifier))

    @staticmethod
    def _get_exclusivity_strength(modifier: Modifier, category: str) -> float:
        for relationship in modifier.relationships:
            if relationship.relationship_type == RelationshipType.EXCLUSIVE_WITH:
                if relationship.target_category == category:
                    return relationship.strength

        return 1.0

    @staticmethod
    def _get_exclusivity_strength_for_modifier(
        modifier: Modifier, target_id: str | None
    ) -> float:
        for relationship in modifier.relationships:
            if relationship.relationship_type == RelationshipType.EXCLUSIVE_WITH:
                if relationship.target_modifier_id == target_id:
                    return relationship.strength

        return 1.0

    @staticmethod
    def _get_exclusivity_strength_for_tags(
        modifier: Modifier, target_tags: frozenset[str]
    ) -> float:
        for relationship in modifier.relationships:
            if relationship.relationship_type == RelationshipType.EXCLUSIVE_WITH:
                if relationship.target_tags and relationship.target_tags & target_tags:
                    return relationship.strength

        return 1.0


class ApplyStage(PipelineStage[ModifierContext, ModifierContext, PipelineContext]):
    """Apply final values to world components.

    Uses optional StatApplicators registered in ModifierConfig.
    If applicator registered for stat → invoke it to write value
    If no applicator → skip (game reads final_values dict manually)

    Design allows hybrid approach: some stats auto-applied, others manual.
    """

    def __init__(self, profiling_enabled: bool = False) -> None:
        self._profiling_enabled = profiling_enabled
        self._monitor = get_performance_monitor() if profiling_enabled else None

    @property
    def name(self) -> str:
        return "apply"

    def process(
        self,
        value: ModifierContext,
        context: PipelineContext,
    ) -> ModifierContext:
        if self._profiling_enabled and self._monitor:
            with self._monitor.sample(category="modifier_stage", name="apply"):
                return self._execute_apply(modifier_context=value)
        return self._execute_apply(modifier_context=value)

    @staticmethod
    def _execute_apply(modifier_context: ModifierContext) -> ModifierContext:
        """Invoke applicators for stats with registered handlers."""
        if modifier_context.world is None:
            return modifier_context

        for (entity_id, stat), final_value in sorted(
            modifier_context.final_values.items()
        ):
            applicator = modifier_context.config.get_applicator(stat=stat)
            if applicator is not None:
                applicator(
                    entity_id=entity_id,
                    stat=stat,
                    value=final_value,
                    world=modifier_context.world,
                )

        return modifier_context

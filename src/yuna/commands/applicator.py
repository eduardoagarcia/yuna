"""Resource effect application for ECS contexts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from yuna.commands.permissions import RESOURCE_TO_MODIFIER_TYPE_MAP
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.types import ModifierPriority

if TYPE_CHECKING:
    from yuna.commands.permissions import (
        ActionPermission,
        ResourceModificationType,
    )
    from yuna.ecs.world import ECSWorld
    from yuna.types.identifiers import EntityID


class ResourceEffectApplicator:
    """Applies resource effects from action permissions to ECS world modifiers.

    Converts declarative permission resource effects into concrete modifier
    pipeline operations. This ensures commands use permission() as single
    source of truth for resource costs/gains.

    Usage:
        # In command execute():
        permission = self.permission(context=context)
        ResourceEffectApplicator.apply_effects(
            entity_id=self._bot_id,
            permission=permission,
            context=context,
        )

    Design:
        - Reads effects from permission (single source of truth)
        - Converts ResourceEffects to Modifiers using RESOURCE_TO_MODIFIER_TYPE_MAP
        - Queues modifiers in world modifier pipeline
        - Maps resource_type to stat names (override via stat_map)
        - Applies all effects from permission in single call
    """

    @staticmethod
    def apply_effects(
        entity_id: EntityID,
        permission: ActionPermission,
        context: ECSWorld,
        source: str = "command",
        stat_map: dict[str, str] | None = None,
    ) -> None:
        """Apply all resource effects from permission to world modifiers.

        Args:
            entity_id: Entity executing the action
            permission: Action permission with resource effects
            context: ECS world with modifier pipeline
            source: Source identifier for modifiers (default: "command")
            stat_map: Optional mapping from resource_type to stat name
                     (default: identity mapping, e.g., "battery" -> "battery")

        Example:
            permission = ActionPermission(
                resource_effects=(
                    ResourceEffect(
                        resource_type="battery",
                        modification_type=ResourceModificationType.FLAT,
                        amount=-0.5,
                    ),
                    ResourceEffect(
                        resource_type="temperature",
                        modification_type=ResourceModificationType.FLAT,
                        amount=0.2,
                    ),
                ),
            )

            ResourceEffectApplicator.apply_effects(
                entity_id=bot_id,
                permission=permission,
                context=world,
                source="navigation_command",
            )
        """
        if not permission.resource_effects:
            return

        default_stat_map = stat_map or {}

        for effect in permission.resource_effects:
            stat = default_stat_map.get(effect.resource_type, effect.resource_type)

            context.modifiers.queue_modifier(
                modifier=Modifier(
                    entity_id=entity_id,
                    stat=stat,
                    modification_type=RESOURCE_TO_MODIFIER_TYPE_MAP[
                        effect.modification_type
                    ],
                    value=effect.amount,
                    priority=ModifierPriority.NORMAL,
                    source=source,
                    categories=effect.categories,
                    tags=effect.tags,
                )
            )

    @staticmethod
    def apply_single_effect(
        entity_id: EntityID,
        resource_type: str,
        modification_type: ResourceModificationType,
        amount: float,
        context: ECSWorld,
        source: str = "command",
        stat_name: str | None = None,
    ) -> None:
        """Apply a single resource effect to world modifiers.

        Convenience method for applying individual effects without creating
        a full ActionPermission.

        Args:
            entity_id: Entity executing the action
            resource_type: Resource identifier (e.g., "battery", "temperature")
            modification_type: How to apply the effect
            amount: Effect magnitude (negative = cost, positive = gain)
            context: ECS world with modifier pipeline
            source: Source identifier for modifier (default: "command")
            stat_name: Optional stat name (default: resource_type)

        Example:
            ResourceEffectApplicator.apply_single_effect(
                entity_id=bot_id,
                resource_type="battery",
                modification_type=ResourceModificationType.FLAT,
                amount=-0.5,
                context=world,
                source="movement_cost",
            )
        """
        stat = stat_name or resource_type

        context.modifiers.queue_modifier(
            modifier=Modifier(
                entity_id=entity_id,
                stat=stat,
                modification_type=RESOURCE_TO_MODIFIER_TYPE_MAP[modification_type],
                value=amount,
                priority=ModifierPriority.NORMAL,
                source=source,
            )
        )

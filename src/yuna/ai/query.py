"""Query and filter AI entities by behavior and state."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from yuna.ai.behavior_tree.component import BehaviorTreeComponent
from yuna.ai.behavior_tree.types import NodeStatus
from yuna.ai.blackboard import Blackboard
from yuna.ai.perception import PerceivedEntities

if TYPE_CHECKING:
    from yuna.ecs.world import ECSWorld
    from yuna.types.identifiers import EntityID


class AIQuery:
    """Query and filter AI entities by behavior and state.

    Enables bulk operations on AI agents matching criteria.
    Similar to Modifier Pipeline's tag-based queries.

    Usage:
        query = AIQuery()

        aggressive_npcs = query.find_by_blackboard_value(
            world=world,
            key="state",
            value="aggressive",
        )

        entities_seeing_player = query.find_perceiving_entity(
            world=world,
            target_entity=player_id,
        )

        query.bulk_update_blackboard(
            world=world,
            entity_ids=aggressive_npcs,
            key="alert_level",
            value=10,
        )
    """

    @staticmethod
    def find_by_blackboard_value(
        world: ECSWorld,
        key: str,
        value: Any,
    ) -> list[EntityID]:
        """Find all AI entities with specific Blackboard value.

        Args:
            world: ECS world reference
            key: Blackboard key to check
            value: Value to match

        Returns:
            List of entity IDs matching criteria
        """
        matching_entities: list[EntityID] = []

        query = world.query().with_components(Blackboard)

        for entity_id, (blackboard_raw,) in query.iterator():
            blackboard = cast(Blackboard, blackboard_raw)

            if blackboard.has_key(key=key):
                stored_value = blackboard.get_value(key=key)
                if stored_value == value:
                    matching_entities.append(entity_id)

        return matching_entities

    @staticmethod
    def find_by_behavior_tree_status(
        world: ECSWorld,
        status: NodeStatus,
    ) -> list[EntityID]:
        """Find AI entities with specific behavior tree status.

        Args:
            world: ECS world reference
            status: NodeStatus to match (SUCCESS, FAILURE, RUNNING)

        Returns:
            List of entity IDs with matching tree status
        """
        matching_entities: list[EntityID] = []

        query = world.query().with_components(BehaviorTreeComponent)

        for entity_id, (tree_raw,) in query.iterator():
            tree = cast(BehaviorTreeComponent, tree_raw)

            if tree.root is None or not tree.enabled:
                continue

            if hasattr(tree.root, "_last_status"):
                if tree.root._last_status == status:
                    matching_entities.append(entity_id)

        return matching_entities

    @staticmethod
    def find_perceiving_entity(
        world: ECSWorld,
        target_entity: EntityID,
    ) -> list[EntityID]:
        """Find all AI entities currently perceiving target.

        Args:
            world: ECS world reference
            target_entity: Entity to check perception of

        Returns:
            List of entity IDs perceiving the target
        """
        perceiving_entities: list[EntityID] = []

        query = world.query().with_components(PerceivedEntities)

        for entity_id, (perceived_raw,) in query.iterator():
            perceived = cast(PerceivedEntities, perceived_raw)

            if target_entity in perceived.visible or target_entity in perceived.audible:
                perceiving_entities.append(entity_id)

        return perceiving_entities

    @staticmethod
    def bulk_update_blackboard(
        world: ECSWorld,
        entity_ids: list[EntityID],
        key: str,
        value: Any,
    ) -> None:
        """Bulk update Blackboard value for multiple entities.

        Args:
            world: ECS world reference
            entity_ids: List of entities to update
            key: Blackboard key to set
            value: Value to set
        """
        for entity_id in entity_ids:
            blackboard_raw = world.get_component(
                entity_id=entity_id,
                component_type=Blackboard,
            )

            if blackboard_raw is not None:
                blackboard = cast(Blackboard, blackboard_raw)
                blackboard.set_value(
                    key=key,
                    value=value,
                    entity_id=entity_id,
                    event_bus=None,
                )

    @staticmethod
    def bulk_interrupt_behavior_trees(
        world: ECSWorld,
        entity_ids: list[EntityID],
    ) -> None:
        """Interrupt behavior trees for all specified entities.

        Disables and re-enables trees to reset execution state.

        Args:
            world: ECS world reference
            entity_ids: List of entities to interrupt
        """
        for entity_id in entity_ids:
            tree_raw = world.get_component(
                entity_id=entity_id,
                component_type=BehaviorTreeComponent,
            )

            if tree_raw is not None:
                tree = cast(BehaviorTreeComponent, tree_raw)
                tree.enabled = False
                tree._ticks_since_update = 0
                tree.enabled = True

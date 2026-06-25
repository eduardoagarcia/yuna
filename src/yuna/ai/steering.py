"""Steering behaviors for AI movement."""

from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from yuna.ecs.component import Component
from yuna.ecs.system import System
from yuna.types.vector import Vector2

if TYPE_CHECKING:
    from yuna.ecs.world import ECSWorld
    from yuna.types.identifiers import EntityID


@dataclass
class SteeringContext:
    """Context for steering calculations.

    Attributes:
        position: Current position
        velocity: Current velocity
        max_speed: Maximum speed
        max_force: Maximum steering force
        target: Target position (for seek/flee)
        entities_nearby: Nearby entities (for avoidance/flocking)
        seed: World seed for deterministic random
        entity_id: Entity ID for per-entity random differentiation
        tick: Current world tick for per-tick random differentiation
    """

    position: Vector2
    velocity: Vector2
    max_speed: float
    max_force: float
    target: Vector2 | None = None
    entities_nearby: list[tuple[EntityID, Vector2]] = field(default_factory=list)
    seed: int = 0
    entity_id: str = ""
    tick: int = 0


class SteeringBehavior(ABC):
    """Base class for steering behaviors.

    Returns desired velocity vector.
    Multiple behaviors can be combined with weights.
    """

    @abstractmethod
    def calculate(self, context: SteeringContext) -> Vector2:
        """Calculate desired velocity.

        Args:
            context: Entity state and environment

        Returns:
            Desired velocity vector (steering force)
        """
        ...  # pragma: no cover


class SeekBehavior(SteeringBehavior):
    """Move toward target.

    Use case: Chase player, move to waypoint
    """

    def calculate(self, context: SteeringContext) -> Vector2:  # noqa: PLR6301
        """Calculate seek force.

        Args:
            context: Steering context

        Returns:
            Steering force toward target
        """
        if context.target is None:
            return Vector2(x=0.0, y=0.0)

        to_target = context.target.subtract(other=context.position)
        distance = to_target.magnitude()

        if distance == 0.0:
            return Vector2(x=0.0, y=0.0)

        desired = to_target.normalize().multiply(scalar=context.max_speed)
        steer = desired.subtract(other=context.velocity)

        if steer.magnitude() > context.max_force:
            steer = steer.normalize().multiply(scalar=context.max_force)

        return steer


class FleeBehavior(SteeringBehavior):
    """Move away from target.

    Use case: Run from player, avoid danger
    """

    def calculate(self, context: SteeringContext) -> Vector2:  # noqa: PLR6301
        """Calculate flee force.

        Args:
            context: Steering context

        Returns:
            Steering force away from target
        """
        if context.target is None:
            return Vector2(x=0.0, y=0.0)

        away_from_target = context.position.subtract(other=context.target)
        distance = away_from_target.magnitude()

        if distance == 0.0:
            return Vector2(x=0.0, y=0.0)

        desired = away_from_target.normalize().multiply(scalar=context.max_speed)
        steer = desired.subtract(other=context.velocity)

        if steer.magnitude() > context.max_force:
            steer = steer.normalize().multiply(scalar=context.max_force)

        return steer


class WanderBehavior(SteeringBehavior):
    """Random wandering movement.

    Use case: Idle movement, patrol variation

    Attributes:
        wander_radius: Radius of wander circle
        wander_distance: Distance ahead for wander circle
        wander_angle: Current wander angle
        angle_change: Max angle change per frame
    """

    def __init__(
        self,
        wander_radius: float = 5.0,
        wander_distance: float = 10.0,
        angle_change: float = 0.3,
    ) -> None:
        """Initialize wander behavior.

        Args:
            wander_radius: Radius of wander circle
            wander_distance: Distance ahead for wander circle
            angle_change: Max angle change per frame
        """
        self._wander_radius = wander_radius
        self._wander_distance = wander_distance
        self._wander_angle = 0.0
        self._angle_change = angle_change

    def calculate(self, context: SteeringContext) -> Vector2:
        """Calculate wander force.

        Args:
            context: Steering context

        Returns:
            Steering force for wandering
        """
        velocity_magnitude = context.velocity.magnitude()

        if velocity_magnitude == 0.0:
            circle_center = context.position.add(
                other=Vector2(x=self._wander_distance, y=0.0)
            )
        else:
            forward = context.velocity.normalize()
            circle_center = context.position.add(
                other=forward.multiply(scalar=self._wander_distance)
            )

        wander_random = random.Random(
            f"{context.seed}:{context.entity_id}:{context.tick}_wander"
        )
        self._wander_angle += wander_random.uniform(
            -self._angle_change, self._angle_change
        )

        displacement = Vector2(
            x=self._wander_radius * math.cos(self._wander_angle),
            y=self._wander_radius * math.sin(self._wander_angle),
        )

        wander_target = circle_center.add(other=displacement)
        desired = wander_target.subtract(other=context.position)

        if desired.magnitude() > 0.0:
            desired = desired.normalize().multiply(scalar=context.max_speed)

        steer = desired.subtract(other=context.velocity)

        if steer.magnitude() > context.max_force:
            steer = steer.normalize().multiply(scalar=context.max_force)

        return steer


class AvoidanceBehavior(SteeringBehavior):
    """Avoid nearby entities.

    Use case: Don't bump into other NPCs, avoid obstacles

    Attributes:
        avoidance_radius: Distance to start avoiding
    """

    def __init__(self, avoidance_radius: float = 3.0) -> None:
        """Initialize avoidance behavior.

        Args:
            avoidance_radius: Distance to start avoiding
        """
        self._avoidance_radius = avoidance_radius

    def calculate(self, context: SteeringContext) -> Vector2:
        """Calculate avoidance force.

        Args:
            context: Steering context

        Returns:
            Steering force to avoid nearby entities
        """
        avoidance_force = Vector2(x=0.0, y=0.0)

        for _entity_id, entity_position in context.entities_nearby:
            to_entity = entity_position.subtract(other=context.position)
            distance = to_entity.magnitude()

            if 0.0 < distance < self._avoidance_radius:
                away = context.position.subtract(other=entity_position)
                away = away.normalize()
                strength = (self._avoidance_radius - distance) / self._avoidance_radius
                away = away.multiply(scalar=strength)
                avoidance_force = avoidance_force.add(other=away)

        if avoidance_force.magnitude() > 0.0:
            avoidance_force = avoidance_force.normalize().multiply(
                scalar=context.max_speed
            )
            avoidance_force = avoidance_force.subtract(other=context.velocity)

            if avoidance_force.magnitude() > context.max_force:
                avoidance_force = avoidance_force.normalize().multiply(
                    scalar=context.max_force
                )

        return avoidance_force


class FlockingBehavior(SteeringBehavior):
    """Flock with nearby entities (separation, alignment, cohesion).

    Use case: Birds, fish, herd animals

    Attributes:
        separation_weight: Weight for separation (avoid crowding)
        alignment_weight: Weight for alignment (match direction)
        cohesion_weight: Weight for cohesion (move toward center)
        neighbor_radius: Radius to consider neighbors
    """

    def __init__(
        self,
        separation_weight: float = 1.5,
        alignment_weight: float = 1.0,
        cohesion_weight: float = 1.0,
        neighbor_radius: float = 10.0,
    ) -> None:
        """Initialize flocking behavior.

        Args:
            separation_weight: Weight for separation
            alignment_weight: Weight for alignment
            cohesion_weight: Weight for cohesion
            neighbor_radius: Radius to consider neighbors
        """
        self._separation_weight = separation_weight
        self._alignment_weight = alignment_weight
        self._cohesion_weight = cohesion_weight
        self._neighbor_radius = neighbor_radius

    def calculate(self, context: SteeringContext) -> Vector2:
        """Calculate flocking force.

        Args:
            context: Steering context

        Returns:
            Combined flocking force
        """
        neighbors = [
            (entity_id, pos)
            for entity_id, pos in context.entities_nearby
            if context.position.distance(other=pos) <= self._neighbor_radius
        ]

        if not neighbors:
            return Vector2(x=0.0, y=0.0)

        separation = self._calculate_separation(
            position=context.position, neighbors=neighbors
        )
        alignment = self._calculate_alignment(
            velocity=context.velocity, neighbors=neighbors
        )
        cohesion = self._calculate_cohesion(
            position=context.position, neighbors=neighbors
        )

        separation = separation.multiply(scalar=self._separation_weight)
        alignment = alignment.multiply(scalar=self._alignment_weight)
        cohesion = cohesion.multiply(scalar=self._cohesion_weight)

        combined = separation.add(other=alignment).add(other=cohesion)

        if combined.magnitude() > context.max_force:
            combined = combined.normalize().multiply(scalar=context.max_force)

        return combined

    @staticmethod
    def _calculate_separation(
        position: Vector2, neighbors: list[tuple[EntityID, Vector2]]
    ) -> Vector2:
        """Calculate separation force.

        Args:
            position: Current position
            neighbors: Nearby entities

        Returns:
            Separation force
        """
        separation = Vector2(x=0.0, y=0.0)

        for _, neighbor_pos in neighbors:
            diff = position.subtract(other=neighbor_pos)
            distance = diff.magnitude()
            if distance > 0.0:
                diff = diff.normalize().multiply(scalar=1.0 / distance)
                separation = separation.add(other=diff)

        if len(neighbors) > 0:
            separation = separation.multiply(scalar=1.0 / len(neighbors))

        if separation.magnitude() > 0.0:
            separation = separation.normalize()

        return separation

    @staticmethod
    def _calculate_alignment(
        velocity: Vector2, neighbors: list[tuple[EntityID, Vector2]]
    ) -> Vector2:
        """Calculate alignment force.

        Args:
            velocity: Current velocity
            neighbors: Nearby entities

        Returns:
            Alignment force
        """
        return Vector2(x=0.0, y=0.0)

    @staticmethod
    def _calculate_cohesion(
        position: Vector2, neighbors: list[tuple[EntityID, Vector2]]
    ) -> Vector2:
        """Calculate cohesion force.

        Args:
            position: Current position
            neighbors: Nearby entities

        Returns:
            Cohesion force
        """
        if not neighbors:
            return Vector2(x=0.0, y=0.0)

        center = Vector2(x=0.0, y=0.0)
        for _, neighbor_pos in neighbors:
            center = center.add(other=neighbor_pos)

        center = center.multiply(scalar=1.0 / len(neighbors))
        cohesion = center.subtract(other=position)

        if cohesion.magnitude() > 0.0:
            cohesion = cohesion.normalize()

        return cohesion


@dataclass
class SteeringComponent(Component):
    """Steering behavior for entity.

    Combines multiple behaviors with weights.

    Attributes:
        behaviors: List of steering behaviors
        weights: Weight for each behavior
        max_speed: Maximum movement speed
        max_force: Maximum steering force
    """

    behaviors: list[SteeringBehavior] = field(default_factory=list)
    weights: list[float] = field(default_factory=list)
    max_speed: float = 10.0
    max_force: float = 5.0

    def add_behavior(self, behavior: SteeringBehavior, weight: float = 1.0) -> None:
        """Add steering behavior.

        Args:
            behavior: Steering behavior to add
            weight: Weight for this behavior
        """
        self.behaviors.append(behavior)
        self.weights.append(weight)

    def remove_behavior(self, behavior: SteeringBehavior) -> None:
        """Remove steering behavior.

        Args:
            behavior: Behavior to remove
        """
        if behavior in self.behaviors:
            index = self.behaviors.index(behavior)
            del self.behaviors[index]
            del self.weights[index]


class SteeringSystem(System):
    """Applies steering behaviors to entities.

    Calculates steering forces and applies to velocity/physics.

    Priority: 300 (After AI decisions, applies movement)
    """

    def __init__(self, spatial_grid: Any | None = None) -> None:
        """Initialize steering system.

        Args:
            spatial_grid: Optional spatial grid for neighbor queries
        """
        self._spatial_grid = spatial_grid

    @property
    def priority(self) -> int:
        """Get system execution priority.

        Returns:
            Priority value (lower executes first)
        """
        return 300

    def update(self, world: ECSWorld, delta_time: float) -> None:
        """Apply steering behaviors.

        Args:
            world: ECS world
            delta_time: Time since last update
        """
        pass

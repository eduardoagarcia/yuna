"""Physics engine for deterministic simulation."""

from dataclasses import dataclass

from yuna.events.event import Event
from yuna.physics.body import PhysicsBody
from yuna.physics.shapes import CircleShape
from yuna.types.vector import Vector2


@dataclass(frozen=True)
class CollisionEvent(Event):
    """Event emitted when two bodies collide.

    Attributes:
        entity_a: First entity ID
        entity_b: Second entity ID
        contact_point: Point of collision
        normal: Collision normal (from A to B)
    """

    entity_a: str
    entity_b: str
    contact_point: Vector2
    normal: Vector2


class PhysicsEngine:
    """Deterministic physics engine.

    Simulates physics for registered bodies, handles collisions,
    and provides spatial queries.

    Usage:
        engine = PhysicsEngine(gravity=Vector2(x=0.0, y=-9.8))
        engine.add_body(entity_id="player", body=player_body, position=position)
        engine.step(delta_time=0.016)
    """

    def __init__(self, gravity: Vector2 | None = None) -> None:
        """Initialize physics engine.

        Args:
            gravity: Global gravity vector
        """
        self.gravity = gravity if gravity is not None else Vector2(x=0.0, y=0.0)
        self._bodies: dict[str, PhysicsBody] = {}
        self._positions: dict[str, Vector2] = {}
        self._collision_events: list[CollisionEvent] = []
        self._current_timestamp: float = 0.0
        self._current_tick: int = 0

    def add_body(self, entity_id: str, body: PhysicsBody, position: Vector2) -> None:
        """Register physics body.

        Args:
            entity_id: Entity identifier
            body: Physics body component
            position: Initial position
        """
        self._bodies[entity_id] = body
        self._positions[entity_id] = position

    def remove_body(self, entity_id: str) -> None:
        """Unregister physics body.

        Args:
            entity_id: Entity identifier
        """
        self._bodies.pop(entity_id, None)
        self._positions.pop(entity_id, None)

    def get_position(self, entity_id: str) -> Vector2 | None:
        """Get body position.

        Args:
            entity_id: Entity identifier

        Returns:
            Body position or None if not found
        """
        return self._positions.get(entity_id)

    def set_position(self, entity_id: str, position: Vector2) -> None:
        """Set body position.

        Args:
            entity_id: Entity identifier
            position: New position
        """
        if entity_id in self._positions:
            self._positions[entity_id] = position

    def step(
        self,
        delta_time: float,
        timestamp: float = 0.0,
        tick: int = 0,
    ) -> list[CollisionEvent]:
        """Advance physics simulation.

        Args:
            delta_time: Time step in seconds
            timestamp: Current simulation timestamp
            tick: Current simulation tick

        Returns:
            List of collision events that occurred
        """
        self._current_timestamp = timestamp
        self._current_tick = tick
        self._collision_events.clear()

        self._apply_gravity(delta_time=delta_time)
        self._integrate_velocities(delta_time=delta_time)
        self._detect_collisions()

        return self._collision_events.copy()

    def query_point(self, position: Vector2) -> list[str]:
        """Find all bodies containing point.

        Args:
            position: Query position

        Returns:
            List of entity IDs at position
        """
        result: list[str] = []

        for entity_id, body_position in self._positions.items():
            body = self._bodies[entity_id]
            if body.shape.contains_point(point=position, position=body_position):
                result.append(entity_id)

        return result

    def query_circle(self, position: Vector2, radius: float) -> list[str]:
        """Find all bodies intersecting circle.

        Args:
            position: Circle center
            radius: Circle radius

        Returns:
            List of entity IDs intersecting circle
        """
        result: list[str] = []

        for entity_id, body_position in self._positions.items():
            body = self._bodies[entity_id]
            if body.shape.intersects_circle(
                circle_position=position,
                circle_radius=radius,
                position=body_position,
            ):
                result.append(entity_id)

        return result

    def raycast(
        self,
        origin: Vector2,
        direction: Vector2,
        max_distance: float = 100.0,
        resolution: int = 10,
    ) -> tuple[str, Vector2] | None:
        """Cast ray and return first hit.

        Args:
            origin: Ray origin
            direction: Ray direction (will be normalized)
            max_distance: Maximum ray distance
            resolution: Number of samples along ray

        Returns:
            Tuple of (entity_id, hit_point) or None if no hit
        """
        direction_normalized = direction.normalize()
        step = max_distance / resolution

        for i in range(resolution):
            t = i * step
            point = Vector2(
                x=origin.x + direction_normalized.x * t,
                y=origin.y + direction_normalized.y * t,
            )

            hits = self.query_point(position=point)
            if hits:
                return hits[0], point

        return None

    def _apply_gravity(self, delta_time: float) -> None:
        """Apply gravity to all dynamic bodies."""
        for _entity_id, body in self._bodies.items():
            if body.is_static or body.is_kinematic:
                continue

            gravity_force = Vector2(
                x=self.gravity.x * body.mass * body.gravity_scale,
                y=self.gravity.y * body.mass * body.gravity_scale,
            )

            body.apply_force(force=gravity_force, delta_time=delta_time)

    def _integrate_velocities(self, delta_time: float) -> None:
        """Update positions based on velocities."""
        for entity_id, body in self._bodies.items():
            if body.is_static:
                continue

            position = self._positions[entity_id]
            new_position = Vector2(
                x=position.x + body.velocity.x * delta_time,
                y=position.y + body.velocity.y * delta_time,
            )
            self._positions[entity_id] = new_position

    def _detect_collisions(self) -> None:
        """Detect and resolve collisions between bodies."""
        entity_ids = list(self._bodies.keys())

        for i, entity_a in enumerate(entity_ids):
            for entity_b in entity_ids[i + 1 :]:
                if self._check_collision(entity_a=entity_a, entity_b=entity_b):
                    self._resolve_collision(entity_a=entity_a, entity_b=entity_b)

    def _check_collision(self, entity_a: str, entity_b: str) -> bool:
        """Check if two bodies are colliding.

        Args:
            entity_a: First entity ID
            entity_b: Second entity ID

        Returns:
            True if bodies are colliding
        """
        body_a = self._bodies[entity_a]
        body_b = self._bodies[entity_b]

        if not body_a.shape.can_collide_with(other=body_b.shape):
            return False

        pos_a = self._positions[entity_a]
        pos_b = self._positions[entity_b]

        if isinstance(body_a.shape, CircleShape) and isinstance(
            body_b.shape, CircleShape
        ):
            center_a = Vector2(
                x=pos_a.x + body_a.shape.offset.x,
                y=pos_a.y + body_a.shape.offset.y,
            )
            center_b = Vector2(
                x=pos_b.x + body_b.shape.offset.x,
                y=pos_b.y + body_b.shape.offset.y,
            )
            distance = center_a.distance(other=center_b)
            return distance <= (body_a.shape.radius + body_b.shape.radius)

        if isinstance(body_b.shape, CircleShape):
            return body_a.shape.intersects_circle(
                circle_position=Vector2(
                    x=pos_b.x + body_b.shape.offset.x,
                    y=pos_b.y + body_b.shape.offset.y,
                ),
                circle_radius=body_b.shape.radius,
                position=pos_a,
            )

        if isinstance(body_a.shape, CircleShape):
            return body_b.shape.intersects_circle(
                circle_position=Vector2(
                    x=pos_a.x + body_a.shape.offset.x,
                    y=pos_a.y + body_a.shape.offset.y,
                ),
                circle_radius=body_a.shape.radius,
                position=pos_b,
            )

        return False

    def _resolve_collision(self, entity_a: str, entity_b: str) -> None:
        """Resolve collision between two bodies.

        Args:
            entity_a: First entity ID
            entity_b: Second entity ID
        """
        body_a = self._bodies[entity_a]
        body_b = self._bodies[entity_b]
        pos_a = self._positions[entity_a]
        pos_b = self._positions[entity_b]

        if body_a.is_static and body_b.is_static:
            return

        collision_normal = Vector2(
            x=pos_b.x - pos_a.x,
            y=pos_b.y - pos_a.y,
        )
        distance = collision_normal.magnitude()

        if distance == 0:
            collision_normal = Vector2(x=1.0, y=0.0)
        else:
            collision_normal = collision_normal.normalize()

        relative_velocity = Vector2(
            x=body_b.velocity.x - body_a.velocity.x,
            y=body_b.velocity.y - body_a.velocity.y,
        )

        velocity_along_normal = (
            relative_velocity.x * collision_normal.x
            + relative_velocity.y * collision_normal.y
        )

        if velocity_along_normal > 0:
            return

        restitution = min(body_a.restitution, body_b.restitution)

        impulse_magnitude = -(1.0 + restitution) * velocity_along_normal
        impulse_magnitude /= body_a.inverse_mass + body_b.inverse_mass

        impulse = Vector2(
            x=collision_normal.x * impulse_magnitude,
            y=collision_normal.y * impulse_magnitude,
        )

        if not body_a.is_static:
            body_a.apply_impulse(
                impulse=Vector2(x=-impulse.x, y=-impulse.y),
            )

        if not body_b.is_static:
            body_b.apply_impulse(impulse=impulse)

        contact_point = Vector2(
            x=(pos_a.x + pos_b.x) / 2.0,
            y=(pos_a.y + pos_b.y) / 2.0,
        )

        self._collision_events.append(
            CollisionEvent(
                timestamp=self._current_timestamp,
                tick=self._current_tick,
                entity_a=entity_a,
                entity_b=entity_b,
                contact_point=contact_point,
                normal=collision_normal,
            ),
        )

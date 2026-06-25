"""Physics body component for ECS integration."""

from dataclasses import dataclass, field

from yuna.physics.shapes import CollisionShape
from yuna.types.vector import Vector2


@dataclass
class PhysicsBody:
    """Physics body component.

    Stores physics properties for an entity. The physics system uses this
    component to simulate motion, collisions, and forces.

    Attributes:
        mass: Body mass (kg). Zero mass = kinematic (not affected by forces)
        velocity: Current velocity (units/second)
        angular_velocity: Angular velocity (radians/second)
        friction: Friction coefficient (0-1, higher = more friction)
        restitution: Bounciness (0-1, 0 = no bounce, 1 = perfect bounce)
        shape: Collision shape
        is_static: If True, body never moves (infinite mass)
        gravity_scale: Multiplier for gravity (0 = no gravity, 1 = normal)
    """

    mass: float
    shape: CollisionShape
    velocity: Vector2 = field(default_factory=lambda: Vector2(x=0.0, y=0.0))
    angular_velocity: float = 0.0
    friction: float = 0.3
    restitution: float = 0.2
    is_static: bool = False
    gravity_scale: float = 1.0

    @property
    def is_kinematic(self) -> bool:
        """Check if body is kinematic (zero mass).

        Returns:
            True if body has zero mass
        """
        return self.mass == 0.0

    @property
    def inverse_mass(self) -> float:
        """Get inverse mass for force calculations.

        Returns:
            Inverse mass (0 for static/kinematic bodies)
        """
        if self.is_static or self.is_kinematic:
            return 0.0
        return 1.0 / self.mass

    def apply_force(self, force: Vector2, delta_time: float) -> None:
        """Apply force to body (F = ma).

        Args:
            force: Force vector
            delta_time: Time step
        """
        if self.is_static:
            return

        acceleration = Vector2(
            x=force.x * self.inverse_mass,
            y=force.y * self.inverse_mass,
        )

        self.velocity = Vector2(
            x=self.velocity.x + acceleration.x * delta_time,
            y=self.velocity.y + acceleration.y * delta_time,
        )

    def apply_impulse(self, impulse: Vector2) -> None:
        """Apply impulse to body (instant velocity change).

        Args:
            impulse: Impulse vector
        """
        if self.is_static:
            return

        delta_velocity = Vector2(
            x=impulse.x * self.inverse_mass,
            y=impulse.y * self.inverse_mass,
        )

        self.velocity = Vector2(
            x=self.velocity.x + delta_velocity.x,
            y=self.velocity.y + delta_velocity.y,
        )

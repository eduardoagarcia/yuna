"""World-level particle field state: short-lived points on a singleton.

The field component is a world singleton holding every live particle.
Exactly ONE game system per world owns particle upkeep: it advances
the whole field each tick and applies per-kind rules to the results,
so mixed-kind fields never race between owners. Particles are plain
data points with velocity, a lifetime, and a game-defined kind: they
are not ECS entities, never enter the spatial grid, and cost the
recorder one component write per changed tick instead of per-particle
entity churn. Games that record the component get real particle
positions in every frame; games that do not simply exclude it from
their recording config.
"""

from dataclasses import dataclass, field

from yuna.ecs.component import Component
from yuna.state.serializer import bump_serialization_version
from yuna.types.identifiers import EntityID

PARTICLE_FIELD_ENTITY_ID = EntityID("particle_field")


@dataclass(frozen=True)
class Particle:
    """A single short-lived particle in flight.

    Attributes:
        kind: Game-defined particle type tag, the discriminator for
            rendering and for game rules applied on contact
        x: Current x position in world coordinates
        y: Current y position in world coordinates
        vx: X velocity in cells per tick, damped every tick
        vy: Y velocity in cells per tick, damped every tick
        intensity: Remaining payload budget (0.0-1.0), meaning is
            game-defined and drained by the game as the particle acts
        origin_x: X position of the emission origin (range cap anchor)
        origin_y: Y position of the emission origin (range cap anchor)
        owner_id: Entity credited with this particle's effects
        expires_at_tick: First tick the particle no longer exists
    """

    kind: str
    x: float
    y: float
    vx: float
    vy: float
    intensity: float
    origin_x: float
    origin_y: float
    owner_id: EntityID
    expires_at_tick: int


@dataclass
class ParticleFieldComponent(Component):
    """Singleton ledger of live particles of every kind.

    Lives on PARTICLE_FIELD_ENTITY_ID, created lazily on the first
    emission so worlds without particles never carry the entity.
    Written only through replace_particles so the recorder always sees
    a fresh version.

    Attributes:
        particles: Live particles (pruned once expired or culled)
        serialization_version: Recorder cache key, bumped on every write
    """

    particles: list[Particle] = field(default_factory=list)
    serialization_version: int = field(default=0, compare=False)

    def replace_particles(self, particles: list[Particle]) -> None:
        """Replace the particle list and mark the component dirty.

        Args:
            particles: New complete particle list
        """
        self.particles = particles
        bump_serialization_version(component=self)

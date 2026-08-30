"""Pure particle simulation.

Every function takes plain numbers and returns plain data: no world, no
config, no game concepts. Games resolve their own tuning values and
apply their own rules on contact; this module only moves particles.
Angles are math-convention radians. Deterministic given identical
inputs, including the caller-provided seeded RNG.
"""

import math
from dataclasses import replace
from random import Random

from yuna.particles.field import Particle
from yuna.types.identifiers import EntityID

HALF_SPREAD = 0.5


def particle_cell(x: float, y: float) -> tuple[int, int]:
    """Snap a fractional particle position to its containing cell.

    Floors like the unit-cell spatial grid: a particle at 4.6 is in
    cell 4, the same cell an entity positioned at 4 occupies, and a
    particle just below a boundary belongs to the lower cell for
    negative coordinates too.

    Args:
        x: Fractional x position
        y: Fractional y position

    Returns:
        Cell coordinates as an int pair
    """
    return math.floor(x), math.floor(y)


def emit_particles(  # noqa: PLR0917
    origin_x: float,
    origin_y: float,
    direction_radians: float,
    spread_radians: float,
    count: int,
    speed: float,
    lifetime_ticks: int,
    intensity: float,
    kind: str,
    tick: int,
    owner_id: EntityID,
    rng: Random,
    speed_jitter: float = 0.0,
    spawn_spread: float = 0.0,
) -> list[Particle]:
    """Create one tick's worth of particles fanned across a cone.

    Args:
        origin_x: Emission origin x in world coordinates
        origin_y: Emission origin y in world coordinates
        direction_radians: Cone center direction in math radians
        spread_radians: Total cone width in radians
        count: Particles to emit
        speed: Maximum initial speed in cells per tick
        lifetime_ticks: Ticks each particle survives
        intensity: Starting payload budget for each particle
        kind: Game-defined particle type tag
        tick: Current tick (expiry anchor)
        owner_id: Entity credited with the particles' effects
        rng: Seeded RNG (draw order is the determinism contract: one
            cone draw, one jitter draw, then one spawn offset draw per
            particle, regardless of the jitter and spread values)
        speed_jitter: Fraction of speed randomly shaved off each
            particle, so a burst staggers instead of flying as a rigid
            arc (0.0 keeps every particle at full speed)
        spawn_spread: Fraction of each particle's first move over which
            spawn points are distributed along its own direction, so
            consecutive bursts tile into a continuous stream instead of
            pulsing (0.0 spawns every particle exactly at the origin)

    Returns:
        Newly created particles at or ahead of the emission origin
    """
    particles = []
    for _ in range(count):
        angle = direction_radians + rng.uniform(
            -spread_radians * HALF_SPREAD,
            spread_radians * HALF_SPREAD,
        )
        particle_speed = speed * (1.0 - rng.uniform(0.0, speed_jitter))
        vx = math.cos(angle) * particle_speed
        vy = math.sin(angle) * particle_speed
        spawn_offset = rng.uniform(0.0, spawn_spread)
        particles.append(
            Particle(
                kind=kind,
                x=origin_x + vx * spawn_offset,
                y=origin_y + vy * spawn_offset,
                vx=vx,
                vy=vy,
                intensity=intensity,
                origin_x=origin_x,
                origin_y=origin_y,
                owner_id=owner_id,
                expires_at_tick=tick + lifetime_ticks,
            )
        )
    return particles


def _axis_crossing(origin: float, delta: float, cell: int) -> float:
    if delta == 0.0:
        return math.inf
    boundary = float(cell + 1) if delta > 0.0 else float(cell)
    return (boundary - origin) / delta


def traversed_cells(
    from_x: float,
    from_y: float,
    to_x: float,
    to_y: float,
) -> tuple[tuple[int, int], ...]:
    """List every cell a one-tick move occupies after leaving the start.

    Exact for any segment length: the walk steps cell by cell in ray
    order, so nothing between the endpoints is skipped. Always includes
    the end cell, which is the start cell again when no boundary is
    crossed, so a particle inside a freshly blocked cell still reports
    it. A crossing that lands exactly on a shared corner touches both
    corner-adjacent cells and reports both.

    Args:
        from_x: Starting x position
        from_y: Starting y position
        to_x: Ending x position
        to_y: Ending y position

    Returns:
        Cells the move passes through or ends in, in traversal order
    """
    start = particle_cell(x=from_x, y=from_y)
    end = particle_cell(x=to_x, y=to_y)
    if start == end:
        return (end,)
    delta_x = to_x - from_x
    delta_y = to_y - from_y
    step_x = 1 if delta_x > 0.0 else -1
    step_y = 1 if delta_y > 0.0 else -1
    cells: list[tuple[int, int]] = []
    current = start
    while current != end:
        crossing_x = _axis_crossing(origin=from_x, delta=delta_x, cell=current[0])
        crossing_y = _axis_crossing(origin=from_y, delta=delta_y, cell=current[1])
        if crossing_x < crossing_y:
            current = (current[0] + step_x, current[1])
        elif crossing_y < crossing_x:
            current = (current[0], current[1] + step_y)
        else:
            cells.append((current[0] + step_x, current[1]))
            cells.append((current[0], current[1] + step_y))
            current = (current[0] + step_x, current[1] + step_y)
        cells.append(current)
    return tuple(cells)


def advance_particles(  # noqa: PLR0917
    particles: list[Particle],
    damping: float,
    range_cells: float,
    blocked_cells: frozenset[tuple[int, int]],
    tick: int,
    turbulence_radians: float = 0.0,
    rng: Random | None = None,
) -> list[Particle]:
    """Age, move, damp, and cull particles for one tick.

    A particle dies when its expiry tick arrives, when the cell it
    stands in is blocked (covering spawns into blocked cells and cells
    blocked after the fact), when it strays beyond range_cells from its
    emission origin, or when any cell its move traverses is blocked, so
    diagonal moves cannot thread a sealed corner between two blocked
    cells. Turbulence rotates each unexpired particle's velocity by a
    uniform angle before it moves; rotation preserves speed, so
    bounded-speed contracts survive. Draw order is the determinism
    contract: one draw per unexpired particle in an unblocked cell, in
    list order, when turbulence is positive; zero draws when it is 0.0.

    Args:
        particles: Current live particles in list order
        damping: Velocity multiplier applied after each move
        range_cells: Maximum distance from the emission origin
        blocked_cells: Cells that extinguish particles on contact
        tick: Current tick
        turbulence_radians: Maximum per-tick velocity rotation, 0.0
            skips turbulence entirely
        rng: Seeded RNG for turbulence draws, required only when
            turbulence_radians is positive

    Returns:
        Surviving particles, moved and damped, in input order
    """
    survivors = []
    for particle in particles:
        if tick >= particle.expires_at_tick:
            continue
        if particle_cell(x=particle.x, y=particle.y) in blocked_cells:
            continue
        vx = particle.vx
        vy = particle.vy
        if turbulence_radians > 0.0 and rng is not None:
            wobble = rng.uniform(-turbulence_radians, turbulence_radians)
            vx = particle.vx * math.cos(wobble) - particle.vy * math.sin(wobble)
            vy = particle.vx * math.sin(wobble) + particle.vy * math.cos(wobble)
        moved_x = particle.x + vx
        moved_y = particle.y + vy
        range_dx = moved_x - particle.origin_x
        range_dy = moved_y - particle.origin_y
        if math.sqrt(range_dx * range_dx + range_dy * range_dy) > range_cells:
            continue
        if any(
            cell in blocked_cells
            for cell in traversed_cells(
                from_x=particle.x,
                from_y=particle.y,
                to_x=moved_x,
                to_y=moved_y,
            )
        ):
            continue
        survivors.append(
            replace(
                particle,
                x=moved_x,
                y=moved_y,
                vx=vx * damping,
                vy=vy * damping,
            )
        )
    return survivors


def contact_cells(
    particles: list[Particle],
    radius: float = 0.0,
) -> dict[tuple[int, int], list[int]]:
    """Group particles by every cell their effect square touches.

    A particle's effect square extends radius on each side of its
    position, so a particle near a shared edge touches both cells and
    one near a corner touches up to four; radius 0.0 keeps point
    particles that touch only the cell they stand in. An edge exactly
    on a cell boundary does not reach into the next cell. Contact
    policy beyond this geometry (which particles may affect which
    occupants) is the caller's rule to apply per index.

    Args:
        particles: Current live particles in list order
        radius: Half width of each particle's square of effect

    Returns:
        Cell -> indices into particles, insertion-ordered by particle
    """
    cells: dict[tuple[int, int], list[int]] = {}
    for index, particle in enumerate(particles):
        low_x = math.floor(particle.x - radius)
        high_x = max(low_x, math.ceil(particle.x + radius) - 1)
        low_y = math.floor(particle.y - radius)
        high_y = max(low_y, math.ceil(particle.y + radius) - 1)
        for cell_x in range(low_x, high_x + 1):
            for cell_y in range(low_y, high_y + 1):
                cells.setdefault((cell_x, cell_y), []).append(index)
    return cells

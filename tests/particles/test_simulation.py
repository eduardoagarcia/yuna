"""Tests for the pure particle simulation."""

import math
import uuid
from dataclasses import replace
from random import Random

import pytest
from faker import Faker

from yuna.particles.field import Particle
from yuna.particles.simulation import (
    advance_particles,
    contact_cells,
    emit_particles,
    particle_cell,
    traversed_cells,
)
from yuna.types.identifiers import EntityID

fake = Faker()

ORIGIN_X = 4.0
ORIGIN_Y = 4.0
SPEED = 0.9
SPEED_JITTER = 0.25
FULL_SPAWN_SPREAD = 1.0
EFFECT_RADIUS = 0.5
TURBULENCE_RADIANS = math.radians(8.0)
NO_TURBULENCE = 0.0
LIFETIME_TICKS = 8
PARTICLE_COUNT = 6
INTENSITY = 1.0
SPREAD_RADIANS = math.radians(45.0)
ALONG_X_RADIANS = 0.0
ALONG_Y_RADIANS = math.pi / 2
NO_SPREAD = 0.0
SINGLE_PARTICLE = 1
ANGLE_EPSILON = 1e-6
AXIS_EPSILON = 1e-9
DAMPING = 0.75
EXPIRY_TICK = 12
RANGE_LIMIT = 5.0
WIDE_RANGE = 100.0
FAR_FUTURE_TICK = 10_000
NO_BLOCKS: frozenset[tuple[int, int]] = frozenset()
ENTERED_BLOCKED_CELL = (5, 0)
CORNER_SEAM_START = (0.7, 0.6)
CORNER_SEAM_VELOCITY = (0.45, 0.78)
CORNER_SEAM_TRAVERSED_CELL = (0, 1)
CORNER_SEAM_UNTOUCHED_CELL = (1, 0)


def _owner() -> EntityID:
    return EntityID(str(uuid.uuid4()))


def _emit(
    rng: Random,
    direction_radians: float = ALONG_X_RADIANS,
    spread_radians: float = SPREAD_RADIANS,
    count: int = PARTICLE_COUNT,
    tick: int = 0,
    owner_id: EntityID | None = None,
) -> list[Particle]:
    return emit_particles(
        origin_x=ORIGIN_X,
        origin_y=ORIGIN_Y,
        direction_radians=direction_radians,
        spread_radians=spread_radians,
        count=count,
        speed=SPEED,
        lifetime_ticks=LIFETIME_TICKS,
        intensity=INTENSITY,
        kind=fake.word(),
        tick=tick,
        owner_id=owner_id or _owner(),
        rng=rng,
    )


def _particle(
    x: float,
    y: float,
    vx: float = 0.0,
    vy: float = 0.0,
    origin_x: float = ORIGIN_X,
    origin_y: float = ORIGIN_Y,
    expires_at_tick: int = FAR_FUTURE_TICK,
) -> Particle:
    return Particle(
        kind=fake.word(),
        x=x,
        y=y,
        vx=vx,
        vy=vy,
        intensity=INTENSITY,
        origin_x=origin_x,
        origin_y=origin_y,
        owner_id=_owner(),
        expires_at_tick=expires_at_tick,
    )


def test_particle_cell_snaps_fractional_position_to_containing_cell() -> None:
    assert particle_cell(x=4.6, y=7.2) == (4, 7)


def test_particle_cell_keeps_whole_cell_coordinates() -> None:
    assert particle_cell(x=4.0, y=4.0) == (4, 4)


def test_particle_cell_floors_negative_coordinates() -> None:
    assert particle_cell(x=-0.4, y=-1.6) == (-1, -2)


def test_emit_particles_creates_requested_count_at_origin() -> None:
    particles = _emit(rng=Random(x=fake.uuid4()))

    assert len(particles) == PARTICLE_COUNT
    for particle in particles:
        assert particle.x == ORIGIN_X
        assert particle.y == ORIGIN_Y
        assert particle.origin_x == ORIGIN_X
        assert particle.origin_y == ORIGIN_Y


def test_emit_particles_sets_kind_intensity_expiry_and_owner() -> None:
    owner_id = _owner()
    kind = fake.word()
    tick = fake.random_int(min=0, max=500)

    particles = emit_particles(
        origin_x=ORIGIN_X,
        origin_y=ORIGIN_Y,
        direction_radians=ALONG_X_RADIANS,
        spread_radians=SPREAD_RADIANS,
        count=PARTICLE_COUNT,
        speed=SPEED,
        lifetime_ticks=LIFETIME_TICKS,
        intensity=INTENSITY,
        kind=kind,
        tick=tick,
        owner_id=owner_id,
        rng=Random(x=fake.uuid4()),
    )

    for particle in particles:
        assert particle.kind == kind
        assert particle.intensity == INTENSITY
        assert particle.expires_at_tick == tick + LIFETIME_TICKS
        assert particle.owner_id == owner_id


def test_emit_particles_speed_matches_request() -> None:
    for particle in _emit(rng=Random(x=fake.uuid4())):
        assert math.hypot(particle.vx, particle.vy) == pytest.approx(expected=SPEED)


def test_emit_particles_cone_spread_stays_within_half_width() -> None:
    for particle in _emit(rng=Random(x=fake.uuid4())):
        angle = math.atan2(particle.vy, particle.vx)

        assert angle >= ALONG_X_RADIANS - SPREAD_RADIANS / 2 - ANGLE_EPSILON
        assert angle <= ALONG_X_RADIANS + SPREAD_RADIANS / 2 + ANGLE_EPSILON


def test_emit_particles_deterministic_for_identical_seeds() -> None:
    seed = fake.uuid4()
    owner_id = _owner()
    kind = fake.word()

    def emit_with_seed() -> list[Particle]:
        return emit_particles(
            origin_x=ORIGIN_X,
            origin_y=ORIGIN_Y,
            direction_radians=ALONG_X_RADIANS,
            spread_radians=SPREAD_RADIANS,
            count=PARTICLE_COUNT,
            speed=SPEED,
            lifetime_ticks=LIFETIME_TICKS,
            intensity=INTENSITY,
            kind=kind,
            tick=0,
            owner_id=owner_id,
            rng=Random(x=seed),
        )

    assert emit_with_seed() == emit_with_seed()


def test_emit_particles_differ_across_seeds() -> None:
    owner_id = _owner()

    assert _emit(rng=Random(x=fake.unique.uuid4()), owner_id=owner_id) != _emit(
        rng=Random(x=fake.unique.uuid4()), owner_id=owner_id
    )


def test_emit_particles_along_y_launches_toward_positive_y() -> None:
    particles = _emit(
        rng=Random(x=fake.uuid4()),
        direction_radians=ALONG_Y_RADIANS,
        spread_radians=NO_SPREAD,
        count=SINGLE_PARTICLE,
    )

    assert particles[0].vx == pytest.approx(expected=0.0, abs=AXIS_EPSILON)
    assert particles[0].vy == pytest.approx(expected=SPEED)


def test_emit_particles_speed_jitter_stays_within_band() -> None:
    particles = emit_particles(
        origin_x=ORIGIN_X,
        origin_y=ORIGIN_Y,
        direction_radians=ALONG_X_RADIANS,
        spread_radians=SPREAD_RADIANS,
        count=PARTICLE_COUNT,
        speed=SPEED,
        lifetime_ticks=LIFETIME_TICKS,
        intensity=INTENSITY,
        kind=fake.word(),
        tick=0,
        owner_id=_owner(),
        rng=Random(x=fake.uuid4()),
        speed_jitter=SPEED_JITTER,
    )

    speeds = [math.hypot(particle.vx, particle.vy) for particle in particles]
    assert all(
        SPEED * (1.0 - SPEED_JITTER) - ANGLE_EPSILON <= value <= SPEED + ANGLE_EPSILON
        for value in speeds
    )
    assert len(set(speeds)) > 1


def test_emit_particles_speed_jitter_is_deterministic_per_seed() -> None:
    seed = fake.uuid4()
    owner_id = _owner()
    kind = fake.word()

    def emit_jittered() -> list[Particle]:
        return emit_particles(
            origin_x=ORIGIN_X,
            origin_y=ORIGIN_Y,
            direction_radians=ALONG_X_RADIANS,
            spread_radians=SPREAD_RADIANS,
            count=PARTICLE_COUNT,
            speed=SPEED,
            lifetime_ticks=LIFETIME_TICKS,
            intensity=INTENSITY,
            kind=kind,
            tick=0,
            owner_id=owner_id,
            rng=Random(x=seed),
            speed_jitter=SPEED_JITTER,
        )

    assert emit_jittered() == emit_jittered()


def test_emit_particles_spawn_spread_distributes_along_each_direction() -> None:
    particles = emit_particles(
        origin_x=ORIGIN_X,
        origin_y=ORIGIN_Y,
        direction_radians=ALONG_X_RADIANS,
        spread_radians=NO_SPREAD,
        count=PARTICLE_COUNT,
        speed=SPEED,
        lifetime_ticks=LIFETIME_TICKS,
        intensity=INTENSITY,
        kind=fake.word(),
        tick=0,
        owner_id=_owner(),
        rng=Random(x=fake.uuid4()),
        spawn_spread=FULL_SPAWN_SPREAD,
    )

    offsets = [particle.x - ORIGIN_X for particle in particles]
    assert all(0.0 <= offset <= SPEED for offset in offsets)
    assert len(set(offsets)) > 1
    for particle in particles:
        assert particle.y == pytest.approx(expected=ORIGIN_Y, abs=AXIS_EPSILON)
        assert particle.origin_x == ORIGIN_X
        assert particle.origin_y == ORIGIN_Y


def test_emit_particles_along_x_launches_toward_positive_x() -> None:
    particles = _emit(
        rng=Random(x=fake.uuid4()),
        direction_radians=ALONG_X_RADIANS,
        spread_radians=NO_SPREAD,
        count=SINGLE_PARTICLE,
    )

    assert particles[0].vx == pytest.approx(expected=SPEED)
    assert particles[0].vy == pytest.approx(expected=0.0, abs=AXIS_EPSILON)


def test_traversed_cells_returns_end_cell_for_moves_within_one_cell() -> None:
    assert traversed_cells(from_x=4.2, from_y=4.2, to_x=4.8, to_y=4.8) == ((4, 4),)


def test_traversed_cells_reports_intermediate_cell_for_diagonal_moves() -> None:
    assert traversed_cells(from_x=12.7, from_y=10.6, to_x=13.48, to_y=11.05) == (
        (13, 10),
        (13, 11),
    )


def test_traversed_cells_reports_both_sides_for_exact_corner_crossings() -> None:
    assert traversed_cells(from_x=0.5, from_y=0.5, to_x=1.0, to_y=1.0) == (
        (1, 0),
        (0, 1),
        (1, 1),
    )


def test_traversed_cells_reports_intermediate_cell_for_negative_diagonals() -> None:
    assert traversed_cells(from_x=13.3, from_y=11.4, to_x=12.52, to_y=10.95) == (
        (12, 11),
        (12, 10),
    )


def test_traversed_cells_walks_every_cell_of_a_multi_cell_straight_move() -> None:
    assert traversed_cells(from_x=4.6, from_y=0.2, to_x=6.6, to_y=0.2) == (
        (5, 0),
        (6, 0),
    )


def test_traversed_cells_walks_every_cell_of_a_multi_cell_diagonal_move() -> None:
    assert traversed_cells(from_x=0.2, from_y=0.9, to_x=2.0, to_y=2.4) == (
        (0, 1),
        (1, 1),
        (1, 2),
        (2, 2),
    )


def test_traversed_cells_walks_multi_cell_negative_moves() -> None:
    assert traversed_cells(from_x=5.4, from_y=3.5, to_x=3.2, to_y=3.5) == (
        (4, 3),
        (3, 3),
    )


def test_advance_particles_moves_damps_and_preserves_other_fields() -> None:
    particle = _particle(x=1.25, y=2.5, vx=0.5, vy=-0.25)

    survivors = advance_particles(
        particles=[particle],
        damping=DAMPING,
        range_cells=WIDE_RANGE,
        blocked_cells=NO_BLOCKS,
        tick=0,
    )

    assert survivors == [
        replace(
            particle,
            x=particle.x + particle.vx,
            y=particle.y + particle.vy,
            vx=particle.vx * DAMPING,
            vy=particle.vy * DAMPING,
        )
    ]


def test_advance_particles_culls_particles_at_their_expiry_tick() -> None:
    particle = _particle(x=ORIGIN_X, y=ORIGIN_Y, expires_at_tick=EXPIRY_TICK)

    assert (
        advance_particles(
            particles=[particle],
            damping=DAMPING,
            range_cells=WIDE_RANGE,
            blocked_cells=NO_BLOCKS,
            tick=EXPIRY_TICK,
        )
        == []
    )


def test_advance_particles_keeps_particles_one_tick_before_expiry() -> None:
    particle = _particle(x=ORIGIN_X, y=ORIGIN_Y, expires_at_tick=EXPIRY_TICK)

    survivors = advance_particles(
        particles=[particle],
        damping=DAMPING,
        range_cells=WIDE_RANGE,
        blocked_cells=NO_BLOCKS,
        tick=EXPIRY_TICK - 1,
    )

    assert len(survivors) == 1


def test_advance_particles_culls_beyond_range_from_origin() -> None:
    runaway = _particle(x=ORIGIN_X + 4.5, y=ORIGIN_Y, vx=1.0)

    assert (
        advance_particles(
            particles=[runaway],
            damping=DAMPING,
            range_cells=RANGE_LIMIT,
            blocked_cells=NO_BLOCKS,
            tick=0,
        )
        == []
    )


def test_advance_particles_culls_particles_standing_in_a_blocked_cell() -> None:
    stuck = _particle(x=5.4, y=0.2, vx=0.9)

    assert (
        advance_particles(
            particles=[stuck],
            damping=DAMPING,
            range_cells=WIDE_RANGE,
            blocked_cells=frozenset({(5, 0)}),
            tick=0,
        )
        == []
    )


def test_advance_particles_culls_on_blocked_entered_cell() -> None:
    streaker = _particle(x=4.6, y=0.2, vx=0.9)

    assert (
        advance_particles(
            particles=[streaker],
            damping=DAMPING,
            range_cells=WIDE_RANGE,
            blocked_cells=frozenset({ENTERED_BLOCKED_CELL}),
            tick=0,
        )
        == []
    )


def test_advance_particles_culls_on_diagonal_corner_seam_block() -> None:
    diagonal = _particle(
        x=CORNER_SEAM_START[0],
        y=CORNER_SEAM_START[1],
        vx=CORNER_SEAM_VELOCITY[0],
        vy=CORNER_SEAM_VELOCITY[1],
    )

    assert (
        advance_particles(
            particles=[diagonal],
            damping=DAMPING,
            range_cells=WIDE_RANGE,
            blocked_cells=frozenset({CORNER_SEAM_TRAVERSED_CELL}),
            tick=0,
        )
        == []
    )


def test_advance_particles_survives_block_on_untraversed_diagonal_side() -> None:
    diagonal = _particle(
        x=CORNER_SEAM_START[0],
        y=CORNER_SEAM_START[1],
        vx=CORNER_SEAM_VELOCITY[0],
        vy=CORNER_SEAM_VELOCITY[1],
    )

    survivors = advance_particles(
        particles=[diagonal],
        damping=DAMPING,
        range_cells=WIDE_RANGE,
        blocked_cells=frozenset({CORNER_SEAM_UNTOUCHED_CELL}),
        tick=0,
    )

    assert len(survivors) == 1


def test_advance_particles_exact_corner_crossing_culls_on_either_side() -> None:
    corner_runner = _particle(x=0.5, y=0.5, vx=0.5, vy=0.5)

    for blocked_cell in [(1, 0), (0, 1)]:
        assert (
            advance_particles(
                particles=[corner_runner],
                damping=DAMPING,
                range_cells=WIDE_RANGE,
                blocked_cells=frozenset({blocked_cell}),
                tick=0,
            )
            == []
        )


def test_advance_particles_turbulence_rotates_but_preserves_speed() -> None:
    particle = _particle(x=10.0, y=10.0, vx=0.5, vy=0.25)
    seed = fake.uuid4()

    def advance_turbulent() -> list[Particle]:
        return advance_particles(
            particles=[particle],
            damping=DAMPING,
            range_cells=WIDE_RANGE,
            blocked_cells=NO_BLOCKS,
            tick=0,
            turbulence_radians=TURBULENCE_RADIANS,
            rng=Random(x=seed),
        )

    survivors = advance_turbulent()

    assert len(survivors) == 1
    moved = survivors[0]
    assert (moved.vx, moved.vy) != (particle.vx * DAMPING, particle.vy * DAMPING)
    assert math.hypot(moved.vx, moved.vy) == pytest.approx(
        expected=math.hypot(particle.vx, particle.vy) * DAMPING
    )
    assert advance_turbulent() == survivors


def test_advance_particles_zero_turbulence_never_touches_the_rng() -> None:
    particle = _particle(x=10.0, y=10.0, vx=0.5, vy=0.25)
    rng = Random(x=fake.uuid4())
    state_before = rng.getstate()

    advance_particles(
        particles=[particle],
        damping=DAMPING,
        range_cells=WIDE_RANGE,
        blocked_cells=NO_BLOCKS,
        tick=0,
        turbulence_radians=NO_TURBULENCE,
        rng=rng,
    )

    assert rng.getstate() == state_before


def test_advance_particles_moves_survivors_and_preserves_input_order() -> None:
    leader = _particle(x=1.0, y=1.0, vx=0.1)
    expired = _particle(x=1.0, y=1.0, expires_at_tick=0)
    trailer = _particle(x=2.0, y=2.0, vy=0.1)

    survivors = advance_particles(
        particles=[leader, expired, trailer],
        damping=DAMPING,
        range_cells=WIDE_RANGE,
        blocked_cells=NO_BLOCKS,
        tick=0,
    )

    assert survivors == [
        replace(
            leader,
            x=leader.x + leader.vx,
            y=leader.y + leader.vy,
            vx=leader.vx * DAMPING,
            vy=leader.vy * DAMPING,
        ),
        replace(
            trailer,
            x=trailer.x + trailer.vx,
            y=trailer.y + trailer.vy,
            vx=trailer.vx * DAMPING,
            vy=trailer.vy * DAMPING,
        ),
    ]


def test_contact_cells_groups_particles_still_in_their_emission_cell() -> None:
    emitter_bound = _particle(x=4.2, y=4.9, origin_x=4.6, origin_y=4.1)

    assert contact_cells(particles=[emitter_bound]) == {(4, 4): [0]}


def test_contact_cells_groups_by_current_cell_in_insertion_order() -> None:
    first = _particle(x=2.2, y=3.9)
    second = _particle(x=5.5, y=5.5)
    third = _particle(x=2.8, y=3.1)

    assert contact_cells(particles=[first, second, third]) == {
        (2, 3): [0, 2],
        (5, 5): [1],
    }


def test_contact_cells_radius_reaches_across_a_shared_edge() -> None:
    edge_rider = _particle(x=6.0, y=5.5)

    assert contact_cells(particles=[edge_rider], radius=EFFECT_RADIUS) == {
        (5, 5): [0],
        (6, 5): [0],
    }


def test_contact_cells_radius_touches_four_cells_at_a_corner() -> None:
    corner_rider = _particle(x=6.0, y=5.0)

    assert contact_cells(particles=[corner_rider], radius=EFFECT_RADIUS) == {
        (5, 4): [0],
        (5, 5): [0],
        (6, 4): [0],
        (6, 5): [0],
    }


def test_contact_cells_radius_edge_on_a_boundary_does_not_reach_over() -> None:
    centered = _particle(x=6.5, y=5.5)

    assert contact_cells(particles=[centered], radius=EFFECT_RADIUS) == {
        (6, 5): [0],
    }

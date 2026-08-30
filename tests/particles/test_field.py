"""Tests for the world-level particle field state."""

import dataclasses
import uuid

import pytest
from faker import Faker

from yuna.particles.field import (
    PARTICLE_FIELD_ENTITY_ID,
    Particle,
    ParticleFieldComponent,
)
from yuna.types.identifiers import EntityID

fake = Faker()

FIXED_FIELD_ENTITY_NAME = "particle_field"


def _particle() -> Particle:
    origin_x = fake.pyfloat(min_value=0.0, max_value=30.0)
    origin_y = fake.pyfloat(min_value=0.0, max_value=30.0)
    return Particle(
        kind=fake.word(),
        x=origin_x,
        y=origin_y,
        vx=fake.pyfloat(min_value=-1.0, max_value=1.0),
        vy=fake.pyfloat(min_value=-1.0, max_value=1.0),
        intensity=fake.pyfloat(min_value=0.0, max_value=1.0),
        origin_x=origin_x,
        origin_y=origin_y,
        owner_id=EntityID(str(uuid.uuid4())),
        expires_at_tick=fake.random_int(min=1, max=1000),
    )


def test_particle_field_entity_id_is_fixed_and_deterministic() -> None:
    assert PARTICLE_FIELD_ENTITY_ID == EntityID(FIXED_FIELD_ENTITY_NAME)


def test_particle_stores_all_fields() -> None:
    kind = fake.word()
    x = fake.pyfloat(min_value=0.0, max_value=30.0)
    y = fake.pyfloat(min_value=0.0, max_value=30.0)
    vx = fake.pyfloat(min_value=-1.0, max_value=1.0)
    vy = fake.pyfloat(min_value=-1.0, max_value=1.0)
    intensity = fake.pyfloat(min_value=0.0, max_value=1.0)
    origin_x = fake.pyfloat(min_value=0.0, max_value=30.0)
    origin_y = fake.pyfloat(min_value=0.0, max_value=30.0)
    owner_id = EntityID(str(uuid.uuid4()))
    expires_at_tick = fake.random_int(min=1, max=1000)

    particle = Particle(
        kind=kind,
        x=x,
        y=y,
        vx=vx,
        vy=vy,
        intensity=intensity,
        origin_x=origin_x,
        origin_y=origin_y,
        owner_id=owner_id,
        expires_at_tick=expires_at_tick,
    )

    assert particle.kind == kind
    assert particle.x == x
    assert particle.y == y
    assert particle.vx == vx
    assert particle.vy == vy
    assert particle.intensity == intensity
    assert particle.origin_x == origin_x
    assert particle.origin_y == origin_y
    assert particle.owner_id == owner_id
    assert particle.expires_at_tick == expires_at_tick


def test_particle_is_frozen() -> None:
    particle = _particle()

    with pytest.raises(expected_exception=dataclasses.FrozenInstanceError):
        particle.intensity = 0.0  # type: ignore[misc]


def test_component_defaults_to_empty_particles_and_version_zero() -> None:
    component = ParticleFieldComponent()

    assert component.particles == []
    assert component.serialization_version == 0


def test_replace_particles_assigns_list_and_bumps_version() -> None:
    component = ParticleFieldComponent()
    particles = [_particle(), _particle()]

    component.replace_particles(particles=particles)

    assert component.particles is particles
    assert component.serialization_version == 1

    component.replace_particles(particles=[])

    assert component.particles == []
    assert component.serialization_version == 2


def test_serialization_version_is_excluded_from_equality() -> None:
    shared = [_particle()]

    assert ParticleFieldComponent(particles=list(shared)) == ParticleFieldComponent(
        particles=list(shared),
        serialization_version=fake.random_int(min=1, max=1000),
    )

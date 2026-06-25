"""Tests for modifier expiration tracking."""

from faker import Faker

from yuna.modifiers.expiration import TrackedModifier
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.types import (
    ModificationType,
    ModifierPriority,
)
from yuna.types.identifiers import EntityID

fake = Faker()


def test_tracked_modifier_initialization() -> None:
    """Test TrackedModifier initialization."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    applied_tick = fake.pyint()
    expires_tick = applied_tick + fake.pyint(min_value=1, max_value=100)

    tracked = TrackedModifier(
        modifier=modifier,
        applied_tick=applied_tick,
        expires_tick=expires_tick,
    )

    assert tracked.modifier == modifier
    assert tracked.applied_tick == applied_tick
    assert tracked.expires_tick == expires_tick


def test_tracked_modifier_permanent() -> None:
    """Test TrackedModifier with no expiration."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    tracked = TrackedModifier(
        modifier=modifier,
        applied_tick=fake.pyint(),
        expires_tick=None,
    )

    assert tracked.expires_tick is None


def test_is_expired_before_expiration() -> None:
    """Test is_expired returns False before expiration."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    applied_tick = 100
    expires_tick = 150

    tracked = TrackedModifier(
        modifier=modifier,
        applied_tick=applied_tick,
        expires_tick=expires_tick,
    )

    assert not tracked.is_expired(current_tick=149)
    assert not tracked.is_expired(current_tick=100)
    assert not tracked.is_expired(current_tick=125)


def test_is_expired_at_expiration() -> None:
    """Test is_expired returns True at expiration tick."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    applied_tick = 100
    expires_tick = 150

    tracked = TrackedModifier(
        modifier=modifier,
        applied_tick=applied_tick,
        expires_tick=expires_tick,
    )

    assert tracked.is_expired(current_tick=150)


def test_is_expired_after_expiration() -> None:
    """Test is_expired returns True after expiration."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )
    applied_tick = 100
    expires_tick = 150

    tracked = TrackedModifier(
        modifier=modifier,
        applied_tick=applied_tick,
        expires_tick=expires_tick,
    )

    assert tracked.is_expired(current_tick=151)
    assert tracked.is_expired(current_tick=200)


def test_is_expired_permanent_never_expires() -> None:
    """Test is_expired returns False for permanent modifiers."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    tracked = TrackedModifier(
        modifier=modifier,
        applied_tick=100,
        expires_tick=None,
    )

    assert not tracked.is_expired(current_tick=100)
    assert not tracked.is_expired(current_tick=1000)
    assert not tracked.is_expired(current_tick=999999)


def test_ticks_remaining_before_expiration() -> None:
    """Test ticks_remaining returns correct value before expiration."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    tracked = TrackedModifier(
        modifier=modifier,
        applied_tick=100,
        expires_tick=150,
    )

    assert tracked.ticks_remaining(current_tick=100) == 50
    assert tracked.ticks_remaining(current_tick=125) == 25
    assert tracked.ticks_remaining(current_tick=149) == 1


def test_ticks_remaining_at_expiration() -> None:
    """Test ticks_remaining returns 0 at expiration."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    tracked = TrackedModifier(
        modifier=modifier,
        applied_tick=100,
        expires_tick=150,
    )

    assert tracked.ticks_remaining(current_tick=150) == 0


def test_ticks_remaining_after_expiration() -> None:
    """Test ticks_remaining returns 0 after expiration."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    tracked = TrackedModifier(
        modifier=modifier,
        applied_tick=100,
        expires_tick=150,
    )

    assert tracked.ticks_remaining(current_tick=151) == 0
    assert tracked.ticks_remaining(current_tick=200) == 0


def test_ticks_remaining_permanent_returns_none() -> None:
    """Test ticks_remaining returns None for permanent modifiers."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    tracked = TrackedModifier(
        modifier=modifier,
        applied_tick=100,
        expires_tick=None,
    )

    assert tracked.ticks_remaining(current_tick=100) is None
    assert tracked.ticks_remaining(current_tick=1000) is None

"""Tests for StatConversions helper class."""

import pytest
from faker import Faker

from yuna.modifiers.conversions import StatConversions
from yuna.modifiers.modifier import StatEffect
from yuna.modifiers.types import ModificationType

fake = Faker()


def test_convert_stat_to_stat_creates_effect_with_scaling() -> None:
    """Test convert_stat_to_stat creates StatEffect with scaling configuration."""
    source = fake.word()
    target = fake.word()
    rate = fake.pyfloat(min_value=0.01, max_value=1.0)

    effect = StatConversions.convert_stat_to_stat(
        source_stat=source,
        target_stat=target,
        conversion_rate=rate,
    )

    assert effect.stat == target
    assert effect.value == 0.0
    assert effect.modification_type == ModificationType.FLAT
    assert effect.scaling_stat == source
    assert effect.scaling_factor == rate


def test_convert_stat_to_stat_with_custom_modification_type() -> None:
    """Test convert_stat_to_stat uses custom modification type."""
    effect = StatConversions.convert_stat_to_stat(
        source_stat=fake.word(),
        target_stat=fake.word(),
        conversion_rate=0.5,
        modification_type=ModificationType.PERCENTAGE,
    )

    assert effect.modification_type == ModificationType.PERCENTAGE


def test_convert_stat_to_stat_with_zero_conversion_rate() -> None:
    """Test convert_stat_to_stat handles zero conversion rate."""
    effect = StatConversions.convert_stat_to_stat(
        source_stat=fake.word(),
        target_stat=fake.word(),
        conversion_rate=0.0,
    )

    assert effect.scaling_factor == 0.0


def test_mirror_stat_creates_1_to_1_mapping() -> None:
    """Test mirror_stat creates 1:1 stat mapping."""
    source = fake.word()
    target = fake.word()

    effect = StatConversions.mirror_stat(source_stat=source, target_stat=target)

    assert effect.stat == target
    assert effect.value == 0.0
    assert effect.modification_type == ModificationType.FLAT
    assert effect.scaling_stat == source
    assert effect.scaling_factor == 1.0


def test_mirror_stat_with_custom_multiplier() -> None:
    """Test mirror_stat applies custom multiplier."""
    multiplier = fake.pyfloat(min_value=0.1, max_value=2.0)

    effect = StatConversions.mirror_stat(
        source_stat=fake.word(),
        target_stat=fake.word(),
        multiplier=multiplier,
    )

    assert effect.scaling_factor == multiplier


def test_distribute_value_splits_equally_by_default() -> None:
    """Test distribute_value splits value equally across stats."""
    stats = [fake.word() for _ in range(3)]
    total = 90.0

    effects = StatConversions.distribute_value(stats=stats, total_value=total)

    assert len(effects) == 3
    for effect in effects:
        assert effect.value == 30.0
        assert effect.modification_type == ModificationType.FLAT


def test_distribute_value_with_custom_distribution() -> None:
    """Test distribute_value uses custom distribution weights."""
    stats = [fake.word() for _ in range(3)]
    total = 100.0
    distribution = [0.5, 0.3, 0.2]

    effects = StatConversions.distribute_value(
        stats=stats,
        total_value=total,
        distribution=distribution,
    )

    assert len(effects) == 3
    assert effects[0].value == 50.0
    assert effects[1].value == 30.0
    assert effects[2].value == 20.0


def test_distribute_value_normalizes_weights() -> None:
    """Test distribute_value normalizes distribution weights."""
    stats = [fake.word() for _ in range(2)]
    total = 100.0
    distribution = [2.0, 3.0]

    effects = StatConversions.distribute_value(
        stats=stats,
        total_value=total,
        distribution=distribution,
    )

    assert effects[0].value == 40.0
    assert effects[1].value == 60.0


def test_distribute_value_assigns_correct_stats() -> None:
    """Test distribute_value assigns values to correct stats."""
    stat1 = fake.word()
    stat2 = fake.word()
    stats = [stat1, stat2]

    effects = StatConversions.distribute_value(stats=stats, total_value=100.0)

    assert effects[0].stat == stat1
    assert effects[1].stat == stat2


def test_distribute_value_raises_on_mismatched_lengths() -> None:
    """Test distribute_value raises error when distribution length mismatches."""
    stats = [fake.word(), fake.word()]
    distribution = [0.5, 0.3, 0.2]

    with pytest.raises(ValueError, match="Distribution length .* must match"):
        StatConversions.distribute_value(
            stats=stats,
            total_value=100.0,
            distribution=distribution,
        )


def test_distribute_value_raises_on_zero_weight_sum() -> None:
    """Test distribute_value raises error when weights sum to zero."""
    stats = [fake.word(), fake.word()]
    distribution = [0.0, 0.0]

    with pytest.raises(ValueError, match="Distribution weights sum to zero"):
        StatConversions.distribute_value(
            stats=stats,
            total_value=100.0,
            distribution=distribution,
        )


def test_distribute_value_handles_single_stat() -> None:
    """Test distribute_value handles single stat distribution."""
    stat = fake.word()
    total = fake.pyfloat(min_value=1.0, max_value=100.0)

    effects = StatConversions.distribute_value(stats=[stat], total_value=total)

    assert len(effects) == 1
    assert effects[0].stat == stat
    assert effects[0].value == total


def test_distribute_value_with_negative_total() -> None:
    """Test distribute_value handles negative total value."""
    stats = [fake.word(), fake.word()]
    total = -50.0

    effects = StatConversions.distribute_value(stats=stats, total_value=total)

    assert effects[0].value == -25.0
    assert effects[1].value == -25.0


def test_percentage_of_stat_is_convenience_wrapper() -> None:
    """Test percentage_of_stat is equivalent to convert_stat_to_stat."""
    source = fake.word()
    target = fake.word()
    percentage = 0.25

    effect = StatConversions.percentage_of_stat(
        source_stat=source,
        target_stat=target,
        percentage=percentage,
    )

    expected = StatConversions.convert_stat_to_stat(
        source_stat=source,
        target_stat=target,
        conversion_rate=percentage,
        modification_type=ModificationType.FLAT,
    )

    assert effect.stat == expected.stat
    assert effect.value == expected.value
    assert effect.modification_type == expected.modification_type
    assert effect.scaling_stat == expected.scaling_stat
    assert effect.scaling_factor == expected.scaling_factor


def test_percentage_of_stat_uses_flat_modification_type() -> None:
    """Test percentage_of_stat always uses FLAT modification type."""
    effect = StatConversions.percentage_of_stat(
        source_stat=fake.word(),
        target_stat=fake.word(),
        percentage=0.5,
    )

    assert effect.modification_type == ModificationType.FLAT


def test_stat_effect_returned_types_are_correct() -> None:
    """Test all conversion methods return StatEffect instances."""
    source = fake.word()
    target = fake.word()

    convert_effect = StatConversions.convert_stat_to_stat(
        source_stat=source,
        target_stat=target,
        conversion_rate=0.1,
    )
    mirror_effect = StatConversions.mirror_stat(source_stat=source, target_stat=target)
    percentage_effect = StatConversions.percentage_of_stat(
        source_stat=source,
        target_stat=target,
        percentage=0.25,
    )

    assert isinstance(convert_effect, StatEffect)
    assert isinstance(mirror_effect, StatEffect)
    assert isinstance(percentage_effect, StatEffect)


def test_distribute_value_returns_tuple() -> None:
    """Test distribute_value returns tuple of StatEffects."""
    effects = StatConversions.distribute_value(
        stats=[fake.word(), fake.word()],
        total_value=100.0,
    )

    assert isinstance(effects, tuple)
    assert all(isinstance(e, StatEffect) for e in effects)

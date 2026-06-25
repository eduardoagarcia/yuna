"""Tests for scaling functions and value calculators."""

import math
from unittest.mock import Mock

from faker import Faker

from yuna.modifiers.context import ModifierContext
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.scaling import (
    CurveFunctions,
    TimeInterpolation,
    ValueCalculators,
)
from yuna.modifiers.types import ModificationType, ModifierPriority
from yuna.types.identifiers import EntityID

fake = Faker()


def test_scale_by_stat_additive() -> None:
    """Test scale_by_stat with additive mode."""
    entity_id = EntityID(fake.uuid4())
    base_value = fake.pyfloat(min_value=1.0, max_value=100.0)
    stat_value = fake.pyfloat(min_value=1.0, max_value=100.0)
    multiplier = fake.pyfloat(min_value=0.1, max_value=2.0)

    calculator = ValueCalculators.scale_by_stat(
        stat_name="test_stat",
        multiplier=multiplier,
        additive=True,
    )

    world = Mock()
    world.get_stat.return_value = stat_value

    context = ModifierContext(
        modifiers=[],
        config=Mock(),
        world=world,
    )
    context.entity_id = entity_id

    result = calculator(base_value, context)

    assert result == base_value + (stat_value * multiplier)
    world.get_stat.assert_called_once_with(entity_id=entity_id, stat="test_stat")


def test_scale_by_stat_multiplicative() -> None:
    """Test scale_by_stat with multiplicative mode."""
    entity_id = EntityID(fake.uuid4())
    base_value = fake.pyfloat(min_value=1.0, max_value=100.0)
    stat_value = fake.pyfloat(min_value=1.0, max_value=100.0)
    multiplier = fake.pyfloat(min_value=0.1, max_value=2.0)

    calculator = ValueCalculators.scale_by_stat(
        stat_name="test_stat",
        multiplier=multiplier,
        additive=False,
    )

    world = Mock()
    world.get_stat.return_value = stat_value

    context = ModifierContext(
        modifiers=[],
        config=Mock(),
        world=world,
    )
    context.entity_id = entity_id

    result = calculator(base_value, context)

    assert result == base_value * (stat_value * multiplier)


def test_scale_by_stat_returns_base_when_no_world() -> None:
    """Test scale_by_stat returns base value when world is None."""
    base_value = fake.pyfloat(min_value=1.0, max_value=100.0)

    calculator = ValueCalculators.scale_by_stat(
        stat_name="test_stat",
        multiplier=0.5,
        additive=True,
    )

    context = ModifierContext(
        modifiers=[],
        config=Mock(),
        world=None,
    )

    result = calculator(base_value, context)

    assert result == base_value


def test_scale_by_stat_returns_base_when_no_entity_id() -> None:
    """Test scale_by_stat returns base value when entity_id is None."""
    base_value = fake.pyfloat(min_value=1.0, max_value=100.0)

    calculator = ValueCalculators.scale_by_stat(
        stat_name="test_stat",
        multiplier=0.5,
        additive=True,
    )

    context = ModifierContext(
        modifiers=[],
        config=Mock(),
        world=Mock(),
    )
    context.entity_id = None

    result = calculator(base_value, context)

    assert result == base_value


def test_scale_by_percentage() -> None:
    """Test scale_by_percentage returns percentage of stat."""
    entity_id = EntityID(fake.uuid4())
    base_value = fake.pyfloat(min_value=1.0, max_value=100.0)
    stat_value = fake.pyfloat(min_value=1.0, max_value=1000.0)
    percentage = fake.pyfloat(min_value=0.01, max_value=1.0)

    calculator = ValueCalculators.scale_by_percentage(
        stat_name="max_health",
        percentage=percentage,
    )

    world = Mock()
    world.get_stat.return_value = stat_value

    context = ModifierContext(
        modifiers=[],
        config=Mock(),
        world=world,
    )
    context.entity_id = entity_id

    result = calculator(base_value, context)

    assert result == stat_value * percentage
    world.get_stat.assert_called_once_with(entity_id=entity_id, stat="max_health")


def test_scale_by_percentage_returns_base_when_no_world() -> None:
    """Test scale_by_percentage returns base value when world is None."""
    base_value = fake.pyfloat(min_value=1.0, max_value=100.0)

    calculator = ValueCalculators.scale_by_percentage(
        stat_name="max_health",
        percentage=0.10,
    )

    context = ModifierContext(
        modifiers=[],
        config=Mock(),
        world=None,
    )

    result = calculator(base_value, context)

    assert result == base_value


def test_diminishing_returns_single_modifier() -> None:
    """Test diminishing_returns with single modifier."""
    base_value = 10.0
    diminishing_factor = 0.6

    calculator = ValueCalculators.diminishing_returns(
        base_value=base_value,
        diminishing_factor=diminishing_factor,
    )

    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat="test_stat",
        modification_type=ModificationType.FLAT,
        value=5.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    context = ModifierContext(
        modifiers=[modifier],
        config=Mock(),
    )

    result = calculator(5.0, context)

    assert result == base_value


def test_diminishing_returns_multiple_modifiers() -> None:
    """Test diminishing_returns with multiple modifiers."""
    base_value = 10.0
    diminishing_factor = 0.6

    calculator = ValueCalculators.diminishing_returns(
        base_value=base_value,
        diminishing_factor=diminishing_factor,
    )

    modifiers = [
        Modifier(
            entity_id=EntityID(fake.uuid4()),
            stat="test_stat",
            modification_type=ModificationType.FLAT,
            value=5.0,
            priority=ModifierPriority.NORMAL,
            source=fake.word(),
        )
        for _ in range(3)
    ]

    context = ModifierContext(
        modifiers=modifiers,
        config=Mock(),
    )

    result = calculator(5.0, context)

    expected = base_value * (1.0 - ((1.0 - diminishing_factor) ** 3))
    assert result == expected


def test_linear_curve() -> None:
    """Test linear curve is identity function."""
    value = fake.pyfloat(min_value=-100.0, max_value=100.0)

    result = CurveFunctions.linear(value)

    assert result == value


def test_quadratic_curve() -> None:
    """Test quadratic curve squares value."""
    value = fake.pyfloat(min_value=-10.0, max_value=10.0)

    result = CurveFunctions.quadratic(value)

    assert result == value * value


def test_cubic_curve() -> None:
    """Test cubic curve cubes value."""
    value = fake.pyfloat(min_value=-5.0, max_value=5.0)

    result = CurveFunctions.cubic(value)

    assert result == value * value * value


def test_square_root_curve_positive() -> None:
    """Test square_root curve with positive value."""
    value = fake.pyfloat(min_value=0.0, max_value=100.0)

    result = CurveFunctions.square_root(value)

    assert result == math.sqrt(value)


def test_square_root_curve_negative() -> None:
    """Test square_root curve with negative value."""
    value = fake.pyfloat(min_value=-100.0, max_value=-0.1)

    result = CurveFunctions.square_root(value)

    assert result == -math.sqrt(abs(value))


def test_exponential_curve() -> None:
    """Test exponential curve."""
    base = fake.pyfloat(min_value=1.5, max_value=3.0)
    value = fake.pyfloat(min_value=0.0, max_value=5.0)

    curve = CurveFunctions.exponential(base=base)
    result = curve(value)

    assert result == base**value


def test_logarithmic_curve_positive() -> None:
    """Test logarithmic curve with positive value."""
    base = fake.pyfloat(min_value=1.5, max_value=3.0)
    value = fake.pyfloat(min_value=1.0, max_value=100.0)

    curve = CurveFunctions.logarithmic(base=base)
    result = curve(value)

    assert result == math.log(value, base)


def test_logarithmic_curve_zero() -> None:
    """Test logarithmic curve with zero returns zero."""
    curve = CurveFunctions.logarithmic(base=2.0)
    result = curve(0.0)

    assert result == 0.0


def test_logarithmic_curve_negative() -> None:
    """Test logarithmic curve with negative returns zero."""
    curve = CurveFunctions.logarithmic(base=2.0)
    result = curve(-5.0)

    assert result == 0.0


def test_sigmoid_curve() -> None:
    """Test sigmoid curve."""
    steepness = fake.pyfloat(min_value=0.5, max_value=2.0)
    value = fake.pyfloat(min_value=-5.0, max_value=5.0)

    curve = CurveFunctions.sigmoid(steepness=steepness)
    result = curve(value)

    expected = 1.0 / (1.0 + math.exp(-steepness * value))
    assert abs(result - expected) < 0.0001


def test_inverse_curve_positive() -> None:
    """Test inverse curve with positive value."""
    value = fake.pyfloat(min_value=0.1, max_value=100.0)

    result = CurveFunctions.inverse(value)

    assert result == 1.0 / value


def test_inverse_curve_zero() -> None:
    """Test inverse curve with zero returns zero."""
    result = CurveFunctions.inverse(0.0)

    assert result == 0.0


def test_time_interpolation_linear() -> None:
    """Test linear interpolation."""
    start = fake.pyfloat(min_value=0.0, max_value=50.0)
    end = fake.pyfloat(min_value=50.0, max_value=100.0)
    progress = fake.pyfloat(min_value=0.0, max_value=1.0)

    result = TimeInterpolation.interpolate(
        start_value=start,
        end_value=end,
        progress=progress,
        method=TimeInterpolation.LINEAR,
    )

    expected = start + (end - start) * progress
    assert result == expected


def test_time_interpolation_ease_in() -> None:
    """Test ease-in interpolation."""
    start = 0.0
    end = 100.0
    progress = 0.5

    result = TimeInterpolation.interpolate(
        start_value=start,
        end_value=end,
        progress=progress,
        method=TimeInterpolation.EASE_IN,
    )

    t = progress * progress
    expected = start + (end - start) * t
    assert result == expected


def test_time_interpolation_ease_out() -> None:
    """Test ease-out interpolation."""
    start = 0.0
    end = 100.0
    progress = 0.5

    result = TimeInterpolation.interpolate(
        start_value=start,
        end_value=end,
        progress=progress,
        method=TimeInterpolation.EASE_OUT,
    )

    t = 1.0 - (1.0 - progress) * (1.0 - progress)
    expected = start + (end - start) * t
    assert result == expected


def test_time_interpolation_ease_in_out() -> None:
    """Test ease-in-out interpolation."""
    start = 0.0
    end = 100.0
    progress = 0.3

    result = TimeInterpolation.interpolate(
        start_value=start,
        end_value=end,
        progress=progress,
        method=TimeInterpolation.EASE_IN_OUT,
    )

    t = 2.0 * progress * progress
    expected = start + (end - start) * t
    assert result == expected


def test_time_interpolation_spike() -> None:
    """Test spike interpolation."""
    start = 0.0
    end = 100.0
    progress = 0.5

    result = TimeInterpolation.interpolate(
        start_value=start,
        end_value=end,
        progress=progress,
        method=TimeInterpolation.SPIKE,
    )

    t = 1.0 - abs(2.0 * progress - 1.0)
    expected = start + (end - start) * t
    assert result == expected


def test_time_interpolation_clamps_progress() -> None:
    """Test interpolation clamps progress to [0, 1]."""
    start = 0.0
    end = 100.0

    result_below = TimeInterpolation.interpolate(
        start_value=start,
        end_value=end,
        progress=-0.5,
        method=TimeInterpolation.LINEAR,
    )

    result_above = TimeInterpolation.interpolate(
        start_value=start,
        end_value=end,
        progress=1.5,
        method=TimeInterpolation.LINEAR,
    )

    assert result_below == start
    assert result_above == end


def test_time_interpolation_unknown_method_defaults_to_linear() -> None:
    """Test unknown interpolation method defaults to linear."""
    start = 0.0
    end = 100.0
    progress = 0.5

    result = TimeInterpolation.interpolate(
        start_value=start,
        end_value=end,
        progress=progress,
        method="unknown_method",
    )

    expected = start + (end - start) * progress
    assert result == expected

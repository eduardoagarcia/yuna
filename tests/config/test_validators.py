"""Tests for config validators."""

from faker import Faker

from yuna.config.validators import (
    must_be_in_range,
    must_be_positive,
    must_be_power_of_two,
)

fake = Faker()


def test_must_be_positive_with_positive_int():
    """Test must_be_positive with positive integer."""
    value = fake.random_int(min=1, max=1000)
    valid, reason = must_be_positive(value)
    assert valid is True
    assert not reason


def test_must_be_positive_with_positive_float():
    """Test must_be_positive with positive float."""
    value = fake.pyfloat(min_value=0.1, max_value=1000.0)
    valid, reason = must_be_positive(value)
    assert valid is True
    assert not reason


def test_must_be_positive_with_zero():
    """Test must_be_positive with zero."""
    valid, reason = must_be_positive(0)
    assert valid is False
    assert reason == "Must be positive"


def test_must_be_positive_with_negative():
    """Test must_be_positive with negative value."""
    value = fake.random_int(min=-1000, max=-1)
    valid, reason = must_be_positive(value)
    assert valid is False
    assert reason == "Must be positive"


def test_must_be_power_of_two_with_valid_power():
    """Test must_be_power_of_two with valid power of 2."""
    power = fake.random_int(min=1, max=10)
    value = 2**power
    valid, reason = must_be_power_of_two(value)
    assert valid is True
    assert not reason


def test_must_be_power_of_two_with_invalid_value():
    """Test must_be_power_of_two with non-power of 2."""
    value = fake.random_int(min=1, max=100)
    while value & (value - 1) == 0:
        value = fake.random_int(min=1, max=100)

    valid, reason = must_be_power_of_two(value)
    assert valid is False
    assert reason == "Must be power of 2"


def test_must_be_power_of_two_with_zero():
    """Test must_be_power_of_two with zero."""
    valid, reason = must_be_power_of_two(0)
    assert valid is False
    assert reason == "Must be power of 2"


def test_must_be_power_of_two_with_negative():
    """Test must_be_power_of_two with negative value."""
    value = fake.random_int(min=-100, max=-1)
    valid, reason = must_be_power_of_two(value)
    assert valid is False
    assert reason == "Must be power of 2"


def test_must_be_in_range_with_valid_value():
    """Test must_be_in_range with value in range."""
    min_val = fake.pyfloat(min_value=0.0, max_value=50.0)
    max_val = fake.pyfloat(min_value=min_val + 10.0, max_value=100.0)
    value = fake.pyfloat(min_value=min_val, max_value=max_val)

    validator = must_be_in_range(min_val=min_val, max_val=max_val)
    valid, reason = validator(value)

    assert valid is True
    assert not reason


def test_must_be_in_range_with_min_boundary():
    """Test must_be_in_range with minimum boundary value."""
    min_val = fake.pyfloat(min_value=0.0, max_value=50.0)
    max_val = fake.pyfloat(min_value=min_val + 10.0, max_value=100.0)

    validator = must_be_in_range(min_val=min_val, max_val=max_val)
    valid, reason = validator(min_val)

    assert valid is True
    assert not reason


def test_must_be_in_range_with_max_boundary():
    """Test must_be_in_range with maximum boundary value."""
    min_val = fake.pyfloat(min_value=0.0, max_value=50.0)
    max_val = fake.pyfloat(min_value=min_val + 10.0, max_value=100.0)

    validator = must_be_in_range(min_val=min_val, max_val=max_val)
    valid, reason = validator(max_val)

    assert valid is True
    assert not reason


def test_must_be_in_range_with_value_below_min():
    """Test must_be_in_range with value below minimum."""
    min_val = fake.pyfloat(min_value=10.0, max_value=50.0)
    max_val = fake.pyfloat(min_value=min_val + 10.0, max_value=100.0)
    value = fake.pyfloat(min_value=0.0, max_value=min_val - 0.1)

    validator = must_be_in_range(min_val=min_val, max_val=max_val)
    valid, reason = validator(value)

    assert valid is False
    assert f"Must be in range [{min_val}, {max_val}]" in reason


def test_must_be_in_range_with_value_above_max():
    """Test must_be_in_range with value above maximum."""
    min_val = fake.pyfloat(min_value=0.0, max_value=50.0)
    max_val = fake.pyfloat(min_value=min_val + 10.0, max_value=100.0)
    value = fake.pyfloat(min_value=max_val + 0.1, max_value=max_val + 100.0)

    validator = must_be_in_range(min_val=min_val, max_val=max_val)
    valid, reason = validator(value)

    assert valid is False
    assert f"Must be in range [{min_val}, {max_val}]" in reason

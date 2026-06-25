"""Configuration validators."""

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

Validator = Callable[[T], tuple[bool, str]]


def must_be_positive(value: int | float) -> tuple[bool, str]:
    """Validate value is positive."""
    if value <= 0:
        return False, "Must be positive"
    return True, ""


def must_be_power_of_two(value: int) -> tuple[bool, str]:
    """Validate value is power of 2."""
    if value <= 0 or (value & (value - 1)) != 0:
        return False, "Must be power of 2"
    return True, ""


def must_be_in_range(min_val: float, max_val: float) -> Validator[float]:
    """Create validator for range."""

    def validator(value: float) -> tuple[bool, str]:
        if not (min_val <= value <= max_val):
            return False, f"Must be in range [{min_val}, {max_val}]"
        return True, ""

    return validator

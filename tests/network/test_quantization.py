"""Tests for position quantization."""

import pytest
from faker import Faker

from yuna.exceptions import ValidationError
from yuna.network.quantization import (
    QuantizedPosition,
    calculate_bandwidth_savings,
    dequantize_position,
    dequantize_vector,
    get_quantization_range,
    quantize_position,
    quantize_vector,
)
from yuna.types.vector import Vector2

fake = Faker()


def test_quantized_position_dataclass() -> None:
    """Test QuantizedPosition dataclass."""
    x = fake.pyint(min_value=-32768, max_value=32767)
    y = fake.pyint(min_value=-32768, max_value=32767)
    quantized = QuantizedPosition(x=x, y=y)
    assert quantized.x == x
    assert quantized.y == y


def test_quantize_position_default_precision() -> None:
    """Test quantize_position with default precision (0.1)."""
    position = Vector2(x=123.456, y=78.901)
    quantized = quantize_position(position)

    assert quantized.x == 1235
    assert quantized.y == 789


def test_quantize_position_precision_01() -> None:
    """Test quantize_position with 0.1 precision."""
    position = Vector2(x=50.25, y=-30.75)
    quantized = quantize_position(position, precision=0.1)

    assert quantized.x == 502
    assert quantized.y == -308


def test_quantize_position_precision_001() -> None:
    """Test quantize_position with 0.01 precision."""
    position = Vector2(x=12.345, y=67.891)
    quantized = quantize_position(position, precision=0.01)

    assert quantized.x == 1234
    assert quantized.y == 6789


def test_quantize_position_precision_1() -> None:
    """Test quantize_position with 1.0 precision."""
    position = Vector2(x=123.456, y=78.901)
    quantized = quantize_position(position, precision=1.0)

    assert quantized.x == 123
    assert quantized.y == 79


def test_quantize_position_zero() -> None:
    """Test quantize_position with zero coordinates."""
    position = Vector2(x=0.0, y=0.0)
    quantized = quantize_position(position, precision=0.1)

    assert quantized.x == 0
    assert quantized.y == 0


def test_quantize_position_negative() -> None:
    """Test quantize_position with negative coordinates."""
    position = Vector2(x=-123.456, y=-78.901)
    quantized = quantize_position(position, precision=0.1)

    assert quantized.x == -1235
    assert quantized.y == -789


def test_quantize_position_large_values() -> None:
    """Test quantize_position with large values within range."""
    position = Vector2(x=3276.7, y=-3276.8)
    quantized = quantize_position(position, precision=0.1)

    assert quantized.x == 32767
    assert quantized.y == -32768


def test_quantize_position_exceeds_range_positive() -> None:
    """Test quantize_position raises error for values exceeding positive range."""
    position = Vector2(x=3277.0, y=0.0)

    with pytest.raises(ValidationError, match="exceeds 16-bit range"):
        quantize_position(position, precision=0.1)


def test_quantize_position_exceeds_range_negative() -> None:
    """Test quantize_position raises error for values exceeding negative range."""
    position = Vector2(x=0.0, y=-3277.0)

    with pytest.raises(ValidationError, match="exceeds 16-bit range"):
        quantize_position(position, precision=0.1)


def test_quantize_position_rounding() -> None:
    """Test quantize_position rounds to nearest integer."""
    position = Vector2(x=12.34, y=12.36)
    quantized = quantize_position(position, precision=0.1)

    assert quantized.x == 123
    assert quantized.y == 124


def test_dequantize_position_default_precision() -> None:
    """Test dequantize_position with default precision (0.1)."""
    quantized = QuantizedPosition(x=1234, y=789)
    position = dequantize_position(quantized)

    assert position.x == pytest.approx(123.4)
    assert position.y == pytest.approx(78.9)


def test_dequantize_position_precision_01() -> None:
    """Test dequantize_position with 0.1 precision."""
    quantized = QuantizedPosition(x=502, y=-308)
    position = dequantize_position(quantized, precision=0.1)

    assert position.x == pytest.approx(50.2)
    assert position.y == pytest.approx(-30.8)


def test_dequantize_position_precision_001() -> None:
    """Test dequantize_position with 0.01 precision."""
    quantized = QuantizedPosition(x=1234, y=6789)
    position = dequantize_position(quantized, precision=0.01)

    assert position.x == pytest.approx(12.34)
    assert position.y == pytest.approx(67.89)


def test_dequantize_position_precision_1() -> None:
    """Test dequantize_position with 1.0 precision."""
    quantized = QuantizedPosition(x=123, y=79)
    position = dequantize_position(quantized, precision=1.0)

    assert position.x == pytest.approx(123.0)
    assert position.y == pytest.approx(79.0)


def test_dequantize_position_zero() -> None:
    """Test dequantize_position with zero coordinates."""
    quantized = QuantizedPosition(x=0, y=0)
    position = dequantize_position(quantized, precision=0.1)

    assert position.x == pytest.approx(0.0)
    assert position.y == pytest.approx(0.0)


def test_dequantize_position_negative() -> None:
    """Test dequantize_position with negative coordinates."""
    quantized = QuantizedPosition(x=-1234, y=-789)
    position = dequantize_position(quantized, precision=0.1)

    assert position.x == pytest.approx(-123.4)
    assert position.y == pytest.approx(-78.9)


def test_round_trip_precision_01() -> None:
    """Test quantize → dequantize round trip with 0.1 precision."""
    original = Vector2(x=123.456, y=78.901)
    quantized = quantize_position(original, precision=0.1)
    recovered = dequantize_position(quantized, precision=0.1)

    assert recovered.x == pytest.approx(123.5, abs=0.1)
    assert recovered.y == pytest.approx(78.9, abs=0.1)


def test_round_trip_precision_001() -> None:
    """Test quantize → dequantize round trip with 0.01 precision."""
    original = Vector2(x=12.3456, y=6.7891)
    quantized = quantize_position(original, precision=0.01)
    recovered = dequantize_position(quantized, precision=0.01)

    assert recovered.x == pytest.approx(12.35, abs=0.01)
    assert recovered.y == pytest.approx(6.79, abs=0.01)


def test_round_trip_precision_1() -> None:
    """Test quantize → dequantize round trip with 1.0 precision."""
    original = Vector2(x=123.456, y=78.901)
    quantized = quantize_position(original, precision=1.0)
    recovered = dequantize_position(quantized, precision=1.0)

    assert recovered.x == pytest.approx(123.0, abs=1.0)
    assert recovered.y == pytest.approx(79.0, abs=1.0)


def test_round_trip_negative_values() -> None:
    """Test quantize → dequantize round trip with negative values."""
    original = Vector2(x=-123.456, y=-78.901)
    quantized = quantize_position(original, precision=0.1)
    recovered = dequantize_position(quantized, precision=0.1)

    assert recovered.x == pytest.approx(-123.5, abs=0.1)
    assert recovered.y == pytest.approx(-78.9, abs=0.1)


def test_round_trip_zero() -> None:
    """Test quantize → dequantize round trip with zero."""
    original = Vector2(x=0.0, y=0.0)
    quantized = quantize_position(original, precision=0.1)
    recovered = dequantize_position(quantized, precision=0.1)

    assert recovered.x == pytest.approx(0.0)
    assert recovered.y == pytest.approx(0.0)


def test_quantize_vector_alias() -> None:
    """Test quantize_vector is alias for quantize_position."""
    vector = Vector2(x=50.25, y=-30.75)
    quantized = quantize_vector(vector, precision=0.1)

    assert quantized.x == 502
    assert quantized.y == -308


def test_dequantize_vector_alias() -> None:
    """Test dequantize_vector is alias for dequantize_position."""
    quantized = QuantizedPosition(x=502, y=-308)
    vector = dequantize_vector(quantized, precision=0.1)

    assert vector.x == pytest.approx(50.2)
    assert vector.y == pytest.approx(-30.8)


def test_get_quantization_range_precision_01() -> None:
    """Test get_quantization_range with 0.1 precision."""
    min_val, max_val = get_quantization_range(precision=0.1)

    assert min_val == pytest.approx(-3276.8)
    assert max_val == pytest.approx(3276.7)


def test_get_quantization_range_precision_001() -> None:
    """Test get_quantization_range with 0.01 precision."""
    min_val, max_val = get_quantization_range(precision=0.01)

    assert min_val == pytest.approx(-327.68)
    assert max_val == pytest.approx(327.67)


def test_get_quantization_range_precision_1() -> None:
    """Test get_quantization_range with 1.0 precision."""
    min_val, max_val = get_quantization_range(precision=1.0)

    assert min_val == pytest.approx(-32768.0)
    assert max_val == pytest.approx(32767.0)


def test_calculate_bandwidth_savings_quantized() -> None:
    """Test calculate_bandwidth_savings with quantization enabled."""
    stats = calculate_bandwidth_savings(num_positions=100, use_quantization=True)

    assert stats["bytes_unquantized"] == 800
    assert stats["bytes_quantized"] == 400
    assert stats["bytes_used"] == 400
    assert stats["savings_percent"] == 50


def test_calculate_bandwidth_savings_unquantized() -> None:
    """Test calculate_bandwidth_savings with quantization disabled."""
    stats = calculate_bandwidth_savings(num_positions=100, use_quantization=False)

    assert stats["bytes_unquantized"] == 800
    assert stats["bytes_quantized"] == 400
    assert stats["bytes_used"] == 800
    assert stats["savings_percent"] == 50


def test_calculate_bandwidth_savings_zero_positions() -> None:
    """Test calculate_bandwidth_savings with zero positions."""
    stats = calculate_bandwidth_savings(num_positions=0, use_quantization=True)

    assert stats["bytes_unquantized"] == 0
    assert stats["bytes_quantized"] == 0
    assert stats["bytes_used"] == 0
    assert stats["savings_percent"] == 0


def test_calculate_bandwidth_savings_large_count() -> None:
    """Test calculate_bandwidth_savings with large position count."""
    stats = calculate_bandwidth_savings(num_positions=10000, use_quantization=True)

    assert stats["bytes_unquantized"] == 80000
    assert stats["bytes_quantized"] == 40000
    assert stats["bytes_used"] == 40000
    assert stats["savings_percent"] == 50


def test_bandwidth_reduction_measurement() -> None:
    """Test actual bandwidth reduction is 50% as specified."""
    num_positions = 1000

    stats = calculate_bandwidth_savings(num_positions=num_positions)

    reduction_percent = stats["savings_percent"]
    assert reduction_percent == 50


def test_precision_sufficient_for_gameplay() -> None:
    """Test 0.1 precision is sufficient for typical game coordinates."""
    test_positions = [
        Vector2(x=0.0, y=0.0),
        Vector2(x=100.5, y=200.3),
        Vector2(x=-50.7, y=-100.2),
        Vector2(x=1000.0, y=1000.0),
    ]

    for original in test_positions:
        quantized = quantize_position(original, precision=0.1)
        recovered = dequantize_position(quantized, precision=0.1)

        assert abs(recovered.x - original.x) <= 0.1
        assert abs(recovered.y - original.y) <= 0.1

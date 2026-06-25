"""Position quantization for network bandwidth reduction."""

from __future__ import annotations

from dataclasses import dataclass

from yuna.exceptions import ValidationError
from yuna.types.vector import Vector2


@dataclass
class QuantizedPosition:
    """16-bit quantized position for network transmission.

    Reduces position bandwidth by ~50% compared to 32-bit floats.
    Uses fixed-point encoding with configurable precision.

    Attributes:
        x: Quantized x coordinate (16-bit signed integer)
        y: Quantized y coordinate (16-bit signed integer)
    """

    x: int
    y: int


def quantize_position(position: Vector2, precision: float = 0.1) -> QuantizedPosition:
    """Convert floating point position to quantized fixed-point.

    Args:
        position: Position vector with float coordinates
        precision: Quantization precision (e.g., 0.1 = 1 decimal place)

    Returns:
        Quantized position with 16-bit integer coordinates

    Raises:
        ValueError: If quantized value exceeds 16-bit range (-32768 to 32767)

    Example:
        pos = Vector2(x=123.456, y=78.901)
        quantized = quantize_position(pos, precision=0.1)
        quantized.x  # 1234 (123.4 * 10)
        quantized.y  # 789 (78.9 * 10)
    """
    scale = 1.0 / precision
    quantized_x = round(position.x * scale)
    quantized_y = round(position.y * scale)

    if not (-32768 <= quantized_x <= 32767):
        raise ValidationError(
            reason=f"Quantized x value {quantized_x} exceeds 16-bit range",
            field="position.x",
            value=f"{position.x} (precision={precision})",
        )
    if not (-32768 <= quantized_y <= 32767):
        raise ValidationError(
            reason=f"Quantized y value {quantized_y} exceeds 16-bit range",
            field="position.y",
            value=f"{position.y} (precision={precision})",
        )

    return QuantizedPosition(x=quantized_x, y=quantized_y)


def dequantize_position(
    quantized: QuantizedPosition, precision: float = 0.1
) -> Vector2:
    """Convert quantized fixed-point position back to floating point.

    Args:
        quantized: Quantized position with 16-bit integer coordinates
        precision: Quantization precision (must match quantize call)

    Returns:
        Position vector with float coordinates

    Example:
        quantized = QuantizedPosition(x=1234, y=789)
        pos = dequantize_position(quantized, precision=0.1)
        pos.x  # 123.4
        pos.y  # 78.9
    """
    return Vector2(
        x=float(quantized.x) * precision,
        y=float(quantized.y) * precision,
    )


def quantize_vector(vector: Vector2, precision: float = 0.1) -> QuantizedPosition:
    """Alias for quantize_position for velocity/direction vectors.

    Args:
        vector: Vector with float coordinates
        precision: Quantization precision

    Returns:
        Quantized vector with 16-bit integer coordinates
    """
    return quantize_position(position=vector, precision=precision)


def dequantize_vector(quantized: QuantizedPosition, precision: float = 0.1) -> Vector2:
    """Alias for dequantize_position for velocity/direction vectors.

    Args:
        quantized: Quantized vector with 16-bit integer coordinates
        precision: Quantization precision

    Returns:
        Vector with float coordinates
    """
    return dequantize_position(quantized=quantized, precision=precision)


def get_quantization_range(precision: float) -> tuple[float, float]:
    """Get valid range for positions with given precision.

    Args:
        precision: Quantization precision

    Returns:
        Tuple of (min_value, max_value) representable with 16-bit quantization

    Example:
        get_quantization_range(0.1)
        (-3276.8, 3276.7)
        get_quantization_range(0.01)
        (-327.68, 327.67)
    """
    min_quantized = -32768
    max_quantized = 32767
    return (
        float(min_quantized) * precision,
        float(max_quantized) * precision,
    )


def calculate_bandwidth_savings(
    num_positions: int,
    use_quantization: bool = True,
) -> dict[str, int]:
    """Calculate bandwidth usage with and without quantization.

    Args:
        num_positions: Number of positions to transmit
        use_quantization: Whether to use quantization

    Returns:
        Dictionary with bytes_unquantized, bytes_quantized, savings_percent

    Example:
        calculate_bandwidth_savings(100)
        {'bytes_unquantized': 800, 'bytes_quantized': 400, 'savings_percent': 50}
    """
    bytes_per_float = 4
    bytes_per_int16 = 2
    coords_per_position = 2

    bytes_unquantized = num_positions * coords_per_position * bytes_per_float
    bytes_quantized = num_positions * coords_per_position * bytes_per_int16

    if use_quantization:
        bytes_used = bytes_quantized
    else:
        bytes_used = bytes_unquantized

    savings_percent = (
        int(((bytes_unquantized - bytes_quantized) / bytes_unquantized) * 100)
        if bytes_unquantized > 0
        else 0
    )

    return {
        "bytes_unquantized": bytes_unquantized,
        "bytes_quantized": bytes_quantized,
        "bytes_used": bytes_used,
        "savings_percent": savings_percent,
    }

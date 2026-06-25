"""Tests for compression strategies."""

import pytest
from faker import Faker

from yuna.network.compression import (
    LZ4Compression,
    NoCompression,
    ZlibCompression,
)

fake = Faker()


def test_no_compression_creation() -> None:
    """Test NoCompression can be instantiated."""
    strategy = NoCompression()
    assert strategy is not None


def test_no_compression_compress() -> None:
    """Test NoCompression returns data unchanged on compress."""
    strategy = NoCompression()
    data = fake.text().encode(encoding="utf-8")

    compressed = strategy.compress(data=data)

    assert compressed == data


def test_no_compression_decompress() -> None:
    """Test NoCompression returns data unchanged on decompress."""
    strategy = NoCompression()
    data = fake.text().encode(encoding="utf-8")

    decompressed = strategy.decompress(data=data)

    assert decompressed == data


def test_no_compression_round_trip() -> None:
    """Test NoCompression round trip."""
    strategy = NoCompression()
    original = fake.text().encode(encoding="utf-8")

    compressed = strategy.compress(data=original)
    decompressed = strategy.decompress(data=compressed)

    assert decompressed == original


def test_zlib_compression_creation() -> None:
    """Test ZlibCompression can be instantiated."""
    strategy = ZlibCompression()
    assert strategy is not None


def test_zlib_compression_with_custom_level() -> None:
    """Test ZlibCompression with custom compression level."""
    strategy = ZlibCompression(level=9)
    assert strategy.level == 9


def test_zlib_compression_compress() -> None:
    """Test ZlibCompression compresses data."""
    strategy = ZlibCompression()
    original = (fake.text() * 10).encode(encoding="utf-8")

    compressed = strategy.compress(data=original)

    assert len(compressed) < len(original)


def test_zlib_compression_decompress() -> None:
    """Test ZlibCompression decompresses data correctly."""
    strategy = ZlibCompression()
    original = (fake.text() * 10).encode(encoding="utf-8")

    compressed = strategy.compress(data=original)
    decompressed = strategy.decompress(data=compressed)

    assert decompressed == original


def test_zlib_compression_round_trip() -> None:
    """Test ZlibCompression round trip preserves data."""
    strategy = ZlibCompression()
    original = (fake.text() * 100).encode(encoding="utf-8")

    compressed = strategy.compress(data=original)
    decompressed = strategy.decompress(data=compressed)

    assert decompressed == original


def test_zlib_compression_different_levels() -> None:
    """Test ZlibCompression with different compression levels."""
    original = (fake.text() * 100).encode(encoding="utf-8")

    strategy_low = ZlibCompression(level=1)
    strategy_high = ZlibCompression(level=9)

    compressed_low = strategy_low.compress(data=original)
    compressed_high = strategy_high.compress(data=original)

    assert len(compressed_high) <= len(compressed_low)

    assert strategy_low.decompress(data=compressed_low) == original
    assert strategy_high.decompress(data=compressed_high) == original


def test_zlib_compression_empty_data() -> None:
    """Test ZlibCompression with empty data."""
    strategy = ZlibCompression()
    empty = b""

    compressed = strategy.compress(data=empty)
    decompressed = strategy.decompress(data=compressed)

    assert decompressed == empty


def test_zlib_compression_small_data() -> None:
    """Test ZlibCompression with small data."""
    strategy = ZlibCompression()
    small = b"hi"

    compressed = strategy.compress(data=small)
    decompressed = strategy.decompress(data=compressed)

    assert decompressed == small


def test_lz4_compression_creation() -> None:
    """Test LZ4Compression can be instantiated if lz4 is available."""
    try:
        strategy = LZ4Compression()
        assert strategy is not None
    except ImportError:
        pytest.skip(reason="lz4 package not installed")


def test_lz4_compression_compress() -> None:
    """Test LZ4Compression compresses data."""
    try:
        strategy = LZ4Compression()
    except ImportError:
        pytest.skip(reason="lz4 package not installed")

    original = (fake.text() * 10).encode(encoding="utf-8")

    compressed = strategy.compress(data=original)

    assert len(compressed) < len(original)


def test_lz4_compression_decompress() -> None:
    """Test LZ4Compression decompresses data correctly."""
    try:
        strategy = LZ4Compression()
    except ImportError:
        pytest.skip(reason="lz4 package not installed")

    original = (fake.text() * 10).encode(encoding="utf-8")

    compressed = strategy.compress(data=original)
    decompressed = strategy.decompress(data=compressed)

    assert decompressed == original


def test_lz4_compression_round_trip() -> None:
    """Test LZ4Compression round trip preserves data."""
    try:
        strategy = LZ4Compression()
    except ImportError:
        pytest.skip(reason="lz4 package not installed")

    original = (fake.text() * 100).encode(encoding="utf-8")

    compressed = strategy.compress(data=original)
    decompressed = strategy.decompress(data=compressed)

    assert decompressed == original


def test_lz4_compression_empty_data() -> None:
    """Test LZ4Compression with empty data."""
    try:
        strategy = LZ4Compression()
    except ImportError:
        pytest.skip(reason="lz4 package not installed")

    empty = b""

    compressed = strategy.compress(data=empty)
    decompressed = strategy.decompress(data=compressed)

    assert decompressed == empty


def test_lz4_compression_small_data() -> None:
    """Test LZ4Compression with small data."""
    try:
        strategy = LZ4Compression()
    except ImportError:
        pytest.skip(reason="lz4 package not installed")

    small = b"hi"

    compressed = strategy.compress(data=small)
    decompressed = strategy.decompress(data=compressed)

    assert decompressed == small


def test_compression_strategies_compatible() -> None:
    """Test different compression strategies produce same output after decompression."""
    original = (fake.text() * 100).encode(encoding="utf-8")

    no_comp = NoCompression()
    zlib_comp = ZlibCompression()

    no_result = no_comp.decompress(data=no_comp.compress(data=original))
    zlib_result = zlib_comp.decompress(data=zlib_comp.compress(data=original))

    assert no_result == original
    assert zlib_result == original
    assert no_result == zlib_result

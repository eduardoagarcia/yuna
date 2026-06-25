"""Compression strategies for network data."""

from __future__ import annotations

import zlib
from typing import Protocol

import lz4.frame


class CompressionStrategy(Protocol):
    """Protocol for compression strategies.

    Compression strategies reduce the size of byte data for network transmission.
    """

    def compress(self, data: bytes) -> bytes:
        """Compress data.

        Args:
            data: Uncompressed bytes

        Returns:
            Compressed bytes
        """
        ...  # pragma: no cover

    def decompress(self, data: bytes) -> bytes:
        """Decompress data.

        Args:
            data: Compressed bytes

        Returns:
            Decompressed bytes
        """
        ...  # pragma: no cover


class NoCompression:
    """No compression strategy (passthrough).

    Usage:
        strategy = NoCompression()
        compressed = strategy.compress(data=b"hello")
        assert compressed == b"hello"
    """

    @staticmethod
    def compress(data: bytes) -> bytes:
        """Return data unchanged.

        Args:
            data: Input bytes

        Returns:
            Same bytes unchanged
        """
        return data

    @staticmethod
    def decompress(data: bytes) -> bytes:
        """Return data unchanged.

        Args:
            data: Input bytes

        Returns:
            Same bytes unchanged
        """
        return data


class ZlibCompression:
    """Zlib compression strategy.

    Provides good compression ratio with reasonable speed.

    Usage:
        strategy = ZlibCompression(level=6)
        compressed = strategy.compress(data=b"hello world" * 100)
        decompressed = strategy.decompress(data=compressed)
    """

    def __init__(self, level: int = 6) -> None:
        """Initialize zlib compression.

        Args:
            level: Compression level (0-9, default 6)
        """
        self.level = level

    def compress(self, data: bytes) -> bytes:
        """Compress data with zlib.

        Args:
            data: Uncompressed bytes

        Returns:
            Compressed bytes
        """
        return zlib.compress(data, self.level)

    @staticmethod
    def decompress(data: bytes) -> bytes:
        """Decompress data with zlib.

        Args:
            data: Compressed bytes

        Returns:
            Decompressed bytes
        """
        return zlib.decompress(data)


class LZ4Compression:
    """LZ4 compression strategy (fast compression).

    Provides fast compression/decompression with moderate compression ratio.
    Requires lz4 package to be installed.

    Usage:
        strategy = LZ4Compression()
        compressed = strategy.compress(data=b"hello world" * 100)
        decompressed = strategy.decompress(data=compressed)
    """

    def __init__(self) -> None:
        """Initialize LZ4 compression."""
        self._lz4 = lz4.frame

    def compress(self, data: bytes) -> bytes:
        """Compress data with LZ4.

        Args:
            data: Uncompressed bytes

        Returns:
            Compressed bytes
        """
        return self._lz4.compress(data)  # type: ignore[no-any-return]

    def decompress(self, data: bytes) -> bytes:
        """Decompress data with LZ4.

        Args:
            data: Compressed bytes

        Returns:
            Decompressed bytes
        """
        return self._lz4.decompress(data)  # type: ignore[no-any-return]

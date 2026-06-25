"""Network component metadata and tagging."""

from __future__ import annotations

from dataclasses import dataclass

from yuna.network.authority import Authority


@dataclass
class NetworkedComponent:
    """Mixin for components that replicate across network.

    Add network metadata to components for replication control.

    Usage:
        @dataclass
        class Position(NetworkedComponent):
            x: float
            y: float
            replicate: bool = True
            authority: Authority = Authority.SERVER
    """

    replicate: bool = True
    authority: Authority = Authority.SERVER
    owner_only: bool = False
    reliable: bool = True
    update_rate: float = 0.0

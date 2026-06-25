"""Network authority and role definitions."""

from __future__ import annotations

from enum import Enum


class Authority(Enum):
    """Component authority mode for network replication.

    Defines who has permission to modify component data.
    """

    SERVER = "server"
    CLIENT = "client"
    SHARED = "shared"


class NetworkRole(Enum):
    """Network role for participants.

    Defines the role of a network participant in the game session.
    """

    SERVER = "server"
    CLIENT = "client"
    PEER = "peer"

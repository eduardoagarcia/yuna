"""Tests for network authority definitions."""

from yuna.network.authority import Authority, NetworkRole


def test_authority_enum_values() -> None:
    """Test Authority enum has correct values."""
    assert Authority.SERVER.value == "server"
    assert Authority.CLIENT.value == "client"
    assert Authority.SHARED.value == "shared"


def test_authority_enum_members() -> None:
    """Test Authority enum has all expected members."""
    authorities = {a.name for a in Authority}
    assert authorities == {"SERVER", "CLIENT", "SHARED"}


def test_network_role_enum_values() -> None:
    """Test NetworkRole enum has correct values."""
    assert NetworkRole.SERVER.value == "server"
    assert NetworkRole.CLIENT.value == "client"
    assert NetworkRole.PEER.value == "peer"


def test_network_role_enum_members() -> None:
    """Test NetworkRole enum has all expected members."""
    roles = {r.name for r in NetworkRole}
    assert roles == {"SERVER", "CLIENT", "PEER"}


def test_authority_equality() -> None:
    """Test Authority enum equality."""
    assert Authority.SERVER == Authority.SERVER
    assert Authority.SERVER != Authority.CLIENT  # type: ignore[comparison-overlap]
    assert Authority.CLIENT != Authority.SHARED  # type: ignore[comparison-overlap]


def test_network_role_equality() -> None:
    """Test NetworkRole enum equality."""
    assert NetworkRole.SERVER == NetworkRole.SERVER
    assert NetworkRole.SERVER != NetworkRole.CLIENT  # type: ignore[comparison-overlap]
    assert NetworkRole.CLIENT != NetworkRole.PEER  # type: ignore[comparison-overlap]

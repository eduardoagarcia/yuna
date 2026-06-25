"""Tests for component versioning."""

from dataclasses import dataclass
from typing import Any

from faker import Faker

from yuna.state.versioning import (
    VersionedComponent,
    add_version_to_data,
    extract_version_from_data,
    get_component_instance_version,
    get_component_version,
    version,
)

fake = Faker()


def test_versioned_component_default_version() -> None:
    """Test VersionedComponent has default version 1."""

    @dataclass
    class Position(VersionedComponent):
        x: float
        y: float

    assert Position.__version__ == 1


def test_versioned_component_custom_version() -> None:
    """Test VersionedComponent with custom version."""

    @dataclass
    class Position(VersionedComponent):
        x: float = 0.0
        y: float = 0.0
        __version__: int = 2

    assert Position.__version__ == 2


def test_versioned_component_instance_version() -> None:
    """Test VersionedComponent instance has version."""

    @dataclass
    class Position(VersionedComponent):
        x: float
        y: float

    position = Position(x=fake.pyfloat(), y=fake.pyfloat())

    assert hasattr(type(position), "__version__")
    assert type(position).__version__ == 1


def test_version_decorator_sets_version() -> None:
    """Test @version decorator sets component version."""

    @version(version_number=3)
    @dataclass
    class Position:
        x: float
        y: float

    assert Position.__version__ == 3  # type: ignore[attr-defined]


def test_version_decorator_multiple_versions() -> None:
    """Test different components can have different versions."""
    version_1 = fake.random_int(min=1, max=10)
    version_2 = fake.random_int(min=1, max=10)

    @version(version_number=version_1)
    @dataclass
    class ComponentA:
        value: int

    @version(version_number=version_2)
    @dataclass
    class ComponentB:
        value: str

    assert ComponentA.__version__ == version_1  # type: ignore[attr-defined]
    assert ComponentB.__version__ == version_2  # type: ignore[attr-defined]


def test_get_component_version_versioned() -> None:
    """Test get_component_version for versioned component."""
    expected_version = fake.random_int(min=1, max=10)

    @version(version_number=expected_version)
    @dataclass
    class Position:
        x: float
        y: float

    result = get_component_version(component_type=Position)

    assert result == expected_version


def test_get_component_version_unversioned() -> None:
    """Test get_component_version returns 1 for unversioned component."""

    @dataclass
    class Position:
        x: float
        y: float

    result = get_component_version(component_type=Position)

    assert result == 1


def test_get_component_version_inherited() -> None:
    """Test get_component_version with inherited VersionedComponent."""

    @dataclass
    class Position(VersionedComponent):
        x: float
        y: float

    result = get_component_version(component_type=Position)

    assert result == 1


def test_get_component_instance_version_versioned() -> None:
    """Test get_component_instance_version for versioned component."""
    expected_version = fake.random_int(min=1, max=10)

    @version(version_number=expected_version)
    @dataclass
    class Position:
        x: float
        y: float

    position = Position(x=fake.pyfloat(), y=fake.pyfloat())
    result = get_component_instance_version(component=position)

    assert result == expected_version


def test_get_component_instance_version_unversioned() -> None:
    """Test get_component_instance_version returns 1 for unversioned component."""

    @dataclass
    class Position:
        x: float
        y: float

    position = Position(x=fake.pyfloat(), y=fake.pyfloat())
    result = get_component_instance_version(component=position)

    assert result == 1


def test_add_version_to_data_versioned() -> None:
    """Test add_version_to_data with versioned component."""
    expected_version = fake.random_int(min=1, max=10)

    @version(version_number=expected_version)
    @dataclass
    class Position:
        x: float
        y: float

    x = fake.pyfloat()
    y = fake.pyfloat()
    data = {"x": x, "y": y}

    result = add_version_to_data(component_type=Position, data=data)

    assert result == {"__version__": expected_version, "x": x, "y": y}


def test_add_version_to_data_unversioned() -> None:
    """Test add_version_to_data with unversioned component."""

    @dataclass
    class Position:
        x: float
        y: float

    x = fake.pyfloat()
    y = fake.pyfloat()
    data = {"x": x, "y": y}

    result = add_version_to_data(component_type=Position, data=data)

    assert result == {"__version__": 1, "x": x, "y": y}


def test_add_version_to_data_preserves_original() -> None:
    """Test add_version_to_data does not modify original dict."""

    @version(version_number=2)
    @dataclass
    class Position:
        x: float
        y: float

    original_data = {"x": 1.0, "y": 2.0}

    add_version_to_data(component_type=Position, data=original_data)

    assert original_data == {"x": 1.0, "y": 2.0}


def test_extract_version_from_data_with_version() -> None:
    """Test extract_version_from_data with version field."""
    expected_version = fake.random_int(min=1, max=10)
    x = fake.pyfloat()
    y = fake.pyfloat()
    data = {"__version__": expected_version, "x": x, "y": y}

    version_num, clean_data = extract_version_from_data(data=data)

    assert version_num == expected_version
    assert clean_data == {"x": x, "y": y}


def test_extract_version_from_data_without_version() -> None:
    """Test extract_version_from_data without version field."""
    x = fake.pyfloat()
    y = fake.pyfloat()
    data = {"x": x, "y": y}

    version_num, clean_data = extract_version_from_data(data=data)

    assert version_num == 1
    assert clean_data == {"x": x, "y": y}


def test_extract_version_from_data_preserves_original() -> None:
    """Test extract_version_from_data does not modify original dict."""
    original_data = {"__version__": 2, "x": 1.0, "y": 2.0}

    extract_version_from_data(data=original_data)

    assert original_data == {"__version__": 2, "x": 1.0, "y": 2.0}


def test_extract_version_from_data_empty_dict() -> None:
    """Test extract_version_from_data with empty dict."""
    data: dict[str, Any] = {}

    version_num, clean_data = extract_version_from_data(data=data)

    assert version_num == 1
    assert clean_data == {}


def test_version_decorator_preserves_class() -> None:
    """Test @version decorator preserves class functionality."""

    @version(version_number=2)
    @dataclass
    class Position:
        x: float
        y: float

    x = fake.pyfloat()
    y = fake.pyfloat()
    position = Position(x=x, y=y)

    assert position.x == x
    assert position.y == y


def test_versioned_component_field_not_in_init() -> None:
    """Test VersionedComponent version field not in __init__."""

    @dataclass
    class Position(VersionedComponent):
        x: float
        y: float

    x = fake.pyfloat()
    y = fake.pyfloat()
    position = Position(x=x, y=y)

    assert position.x == x
    assert position.y == y


def test_versioned_component_field_not_in_repr() -> None:
    """Test VersionedComponent version field not in __repr__."""

    @dataclass
    class Position(VersionedComponent):
        x: float
        y: float

    position = Position(x=1.0, y=2.0)
    repr_str = repr(position)

    assert "__version__" not in repr_str


def test_versioned_component_field_not_in_compare() -> None:
    """Test VersionedComponent version field not used in comparison."""

    @dataclass
    class Position(VersionedComponent):
        x: float
        y: float

    position1 = Position(x=1.0, y=2.0)
    position2 = Position(x=1.0, y=2.0)

    assert position1 == position2


def test_add_version_to_data_multiple_fields() -> None:
    """Test add_version_to_data with many fields."""

    @version(version_number=3)
    @dataclass
    class ComplexComponent:
        int_field: int
        float_field: float
        str_field: str
        bool_field: bool

    data = {
        "int_field": fake.random_int(),
        "float_field": fake.pyfloat(),
        "str_field": fake.word(),
        "bool_field": fake.pybool(),
    }

    result = add_version_to_data(component_type=ComplexComponent, data=data)

    assert result["__version__"] == 3
    assert result["int_field"] == data["int_field"]
    assert result["float_field"] == data["float_field"]
    assert result["str_field"] == data["str_field"]
    assert result["bool_field"] == data["bool_field"]


def test_extract_version_from_data_multiple_fields() -> None:
    """Test extract_version_from_data with many fields."""
    data = {
        "__version__": 3,
        "int_field": fake.random_int(),
        "float_field": fake.pyfloat(),
        "str_field": fake.word(),
        "bool_field": fake.pybool(),
    }

    version_num, clean_data = extract_version_from_data(data=data)

    assert version_num == 3
    assert "__version__" not in clean_data
    assert "int_field" in clean_data
    assert "float_field" in clean_data
    assert "str_field" in clean_data
    assert "bool_field" in clean_data


def test_version_round_trip() -> None:
    """Test version round trip through add and extract."""
    expected_version = fake.random_int(min=1, max=10)

    @version(version_number=expected_version)
    @dataclass
    class Position:
        x: float
        y: float

    original_data = {"x": fake.pyfloat(), "y": fake.pyfloat()}

    versioned_data = add_version_to_data(component_type=Position, data=original_data)
    extracted_version, clean_data = extract_version_from_data(data=versioned_data)

    assert extracted_version == expected_version
    assert clean_data == original_data

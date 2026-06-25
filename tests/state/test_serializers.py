"""Tests for built-in component serializers."""

from dataclasses import dataclass

import pytest
from faker import Faker

from yuna.exceptions import SerializationError
from yuna.state.serializers import (
    EntityIDSerializer,
    GenericDataclassSerializer,
    Vector2Serializer,
)
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

fake = Faker()


def test_vector2_serializer_to_dict() -> None:
    """Test Vector2 serialization to dict."""
    x = fake.pyfloat()
    y = fake.pyfloat()
    vector = Vector2(x=x, y=y)

    result = Vector2Serializer.to_dict(component=vector)

    assert result == {"x": x, "y": y}


def test_vector2_serializer_from_dict() -> None:
    """Test Vector2 deserialization from dict."""
    x = fake.pyfloat()
    y = fake.pyfloat()
    data = {"x": x, "y": y}

    result = Vector2Serializer.from_dict(data=data)

    assert isinstance(result, Vector2)
    assert result.x == x
    assert result.y == y


def test_vector2_serializer_round_trip() -> None:
    """Test Vector2 serialization round trip."""
    x = fake.pyfloat()
    y = fake.pyfloat()
    original = Vector2(x=x, y=y)

    data = Vector2Serializer.to_dict(component=original)
    result = Vector2Serializer.from_dict(data=data)

    assert result.x == original.x
    assert result.y == original.y


def test_entity_id_serializer_to_dict() -> None:
    """Test EntityID serialization to dict."""
    entity_id = EntityID(fake.uuid4())

    result = EntityIDSerializer.to_dict(component=entity_id)

    assert result == {"id": str(entity_id)}


def test_entity_id_serializer_from_dict() -> None:
    """Test EntityID deserialization from dict."""
    uuid_str = fake.uuid4()
    data = {"id": uuid_str}

    result = EntityIDSerializer.from_dict(data=data)

    assert str(result) == uuid_str


def test_entity_id_serializer_round_trip() -> None:
    """Test EntityID serialization round trip."""
    original = EntityID(fake.uuid4())

    data = EntityIDSerializer.to_dict(component=original)
    result = EntityIDSerializer.from_dict(data=data)

    assert str(result) == str(original)


def test_generic_dataclass_serializer_to_dict() -> None:
    """Test generic dataclass serialization."""

    @dataclass
    class Position:
        x: float
        y: float

    x = fake.pyfloat()
    y = fake.pyfloat()
    position = Position(x=x, y=y)

    result = GenericDataclassSerializer.to_dict(component=position)

    assert result == {"x": x, "y": y}


def test_generic_dataclass_serializer_to_dict_non_dataclass() -> None:
    """Test generic serializer raises error for non-dataclass."""

    class NotADataclass:
        pass

    obj = NotADataclass()

    with pytest.raises(SerializationError, match="must be a dataclass"):
        GenericDataclassSerializer.to_dict(component=obj)


def test_generic_dataclass_serializer_from_dict() -> None:
    """Test generic dataclass deserialization."""

    @dataclass
    class Position:
        x: float
        y: float

    x = fake.pyfloat()
    y = fake.pyfloat()
    data = {"x": x, "y": y}

    result = GenericDataclassSerializer.from_dict(component_type=Position, data=data)

    assert isinstance(result, Position)
    assert result.x == x
    assert result.y == y


def test_generic_dataclass_serializer_from_dict_non_dataclass() -> None:
    """Test generic deserializer raises error for non-dataclass."""

    class NotADataclass:
        pass

    data = {"x": 1, "y": 2}

    with pytest.raises(SerializationError, match="must be a dataclass"):
        GenericDataclassSerializer.from_dict(component_type=NotADataclass, data=data)


def test_generic_dataclass_serializer_from_dict_filters_extra_fields() -> None:
    """Test generic deserializer filters extra fields."""

    @dataclass
    class Position:
        x: float
        y: float

    data = {"x": 1.0, "y": 2.0, "z": 3.0}

    result = GenericDataclassSerializer.from_dict(component_type=Position, data=data)

    assert result.x == 1.0
    assert result.y == 2.0
    assert not hasattr(result, "z")


def test_generic_dataclass_serializer_round_trip() -> None:
    """Test generic dataclass serialization round trip."""

    @dataclass
    class Health:
        value: int
        max_value: int

    value = fake.random_int(min=1, max=100)
    max_value = fake.random_int(min=100, max=200)
    original = Health(value=value, max_value=max_value)

    data = GenericDataclassSerializer.to_dict(component=original)
    result = GenericDataclassSerializer.from_dict(component_type=Health, data=data)

    assert result.value == original.value
    assert result.max_value == original.max_value


def test_generic_dataclass_serializer_nested_dataclass() -> None:
    """Test generic serializer with nested dataclass."""

    @dataclass
    class Inner:
        value: int

    @dataclass
    class Outer:
        inner: Inner
        name: str

    inner = Inner(value=42)
    outer = Outer(inner=inner, name="test")

    data = GenericDataclassSerializer.to_dict(component=outer)

    assert data == {"inner": {"value": 42}, "name": "test"}


def test_generic_dataclass_serializer_multiple_fields() -> None:
    """Test generic serializer with many fields."""

    @dataclass
    class ComplexComponent:
        int_field: int
        float_field: float
        str_field: str
        bool_field: bool

    component = ComplexComponent(
        int_field=fake.random_int(),
        float_field=fake.pyfloat(),
        str_field=fake.word(),
        bool_field=fake.pybool(),
    )

    data = GenericDataclassSerializer.to_dict(component=component)
    result = GenericDataclassSerializer.from_dict(
        component_type=ComplexComponent, data=data
    )

    assert result.int_field == component.int_field
    assert result.float_field == component.float_field
    assert result.str_field == component.str_field
    assert result.bool_field == component.bool_field


def test_vector2_serializer_zero_values() -> None:
    """Test Vector2 serializer with zero values."""
    vector = Vector2(x=0.0, y=0.0)

    data = Vector2Serializer.to_dict(component=vector)
    result = Vector2Serializer.from_dict(data=data)

    assert result.x == 0.0
    assert result.y == 0.0


def test_vector2_serializer_negative_values() -> None:
    """Test Vector2 serializer with negative values."""
    vector = Vector2(x=-10.5, y=-20.3)

    data = Vector2Serializer.to_dict(component=vector)
    result = Vector2Serializer.from_dict(data=data)

    assert result.x == -10.5
    assert result.y == -20.3

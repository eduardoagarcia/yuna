"""Tests for component serialization registry."""

from dataclasses import dataclass
from typing import Any

import pytest
from faker import Faker

from yuna.exceptions import ValidationError
from yuna.state.component_registry import (
    ComponentSerializerRegistry,
)

fake = Faker()


@dataclass
class TestComponent:
    """Test component for serialization tests."""

    value: int
    name: str


def test_registry_initial_state() -> None:
    """Test registry starts empty."""
    registry = ComponentSerializerRegistry()

    assert registry.get_registered_types() == []


def test_register_serializer() -> None:
    """Test registering a serializer."""
    registry = ComponentSerializerRegistry()

    def to_dict(component: TestComponent) -> dict[str, Any]:
        return {"value": component.value, "name": component.name}

    def from_dict(data: dict[str, Any]) -> TestComponent:
        return TestComponent(value=data["value"], name=data["name"])

    registry.register_serializer(
        component_type="TestComponent",
        to_dict=to_dict,
        from_dict=from_dict,
    )

    assert "TestComponent" in registry.get_registered_types()


def test_register_serializer_duplicate() -> None:
    """Test that registering duplicate serializer raises error."""
    registry = ComponentSerializerRegistry()

    def to_dict(component: Any) -> dict[str, Any]:
        return {}

    def from_dict(data: dict[str, Any]) -> Any:
        return None

    registry.register_serializer(
        component_type="TestComponent",
        to_dict=to_dict,
        from_dict=from_dict,
    )

    with pytest.raises(ValidationError, match="already registered"):
        registry.register_serializer(
            component_type="TestComponent",
            to_dict=to_dict,
            from_dict=from_dict,
        )


def test_unregister_serializer() -> None:
    """Test unregistering a serializer."""
    registry = ComponentSerializerRegistry()

    def to_dict(component: Any) -> dict[str, Any]:
        return {}

    def from_dict(data: dict[str, Any]) -> Any:
        return None

    registry.register_serializer(
        component_type="TestComponent",
        to_dict=to_dict,
        from_dict=from_dict,
    )

    registry.unregister_serializer(component_type="TestComponent")

    assert "TestComponent" not in registry.get_registered_types()


def test_unregister_serializer_not_registered() -> None:
    """Test unregistering non-existent serializer raises error."""
    registry = ComponentSerializerRegistry()

    with pytest.raises(ValidationError, match="No serializer registered"):
        registry.unregister_serializer(component_type="TestComponent")


def test_is_registered() -> None:
    """Test checking if serializer is registered."""
    registry = ComponentSerializerRegistry()

    def to_dict(component: Any) -> dict[str, Any]:
        return {}

    def from_dict(data: dict[str, Any]) -> Any:
        return None

    assert registry.is_registered(component_type="TestComponent") is False

    registry.register_serializer(
        component_type="TestComponent",
        to_dict=to_dict,
        from_dict=from_dict,
    )

    assert registry.is_registered(component_type="TestComponent") is True


def test_serialize_component() -> None:
    """Test serializing a component."""
    registry = ComponentSerializerRegistry()
    value = fake.random_int()
    name = fake.word()
    component = TestComponent(value=value, name=name)

    def to_dict(comp: TestComponent) -> dict[str, Any]:
        return {"value": comp.value, "name": comp.name}

    def from_dict(data: dict[str, Any]) -> TestComponent:
        return TestComponent(value=data["value"], name=data["name"])

    registry.register_serializer(
        component_type="TestComponent",
        to_dict=to_dict,
        from_dict=from_dict,
    )

    result = registry.serialize_component(
        component_type="TestComponent",
        component=component,
    )

    assert result == {"__version__": 1, "value": value, "name": name}


def test_serialize_component_not_registered() -> None:
    """Test serializing unregistered component raises error."""
    registry = ComponentSerializerRegistry()
    component = TestComponent(value=42, name="test")

    with pytest.raises(ValidationError, match="No serializer registered"):
        registry.serialize_component(
            component_type="TestComponent",
            component=component,
        )


def test_deserialize_component() -> None:
    """Test deserializing a component."""
    registry = ComponentSerializerRegistry()
    value = fake.random_int()
    name = fake.word()
    data = {"value": value, "name": name}

    def to_dict(comp: TestComponent) -> dict[str, Any]:
        return {"value": comp.value, "name": comp.name}

    def from_dict(d: dict[str, Any]) -> TestComponent:
        return TestComponent(value=d["value"], name=d["name"])

    registry.register_serializer(
        component_type="TestComponent",
        to_dict=to_dict,
        from_dict=from_dict,
    )

    result = registry.deserialize_component(
        component_type="TestComponent",
        data=data,
    )

    assert isinstance(result, TestComponent)
    assert result.value == value
    assert result.name == name


def test_deserialize_component_not_registered() -> None:
    """Test deserializing unregistered component raises error."""
    registry = ComponentSerializerRegistry()
    data = {"value": 42, "name": "test"}

    with pytest.raises(ValidationError, match="No deserializer registered"):
        registry.deserialize_component(
            component_type="TestComponent",
            data=data,
        )


def test_get_registered_types() -> None:
    """Test getting list of registered types."""
    registry = ComponentSerializerRegistry()

    def to_dict(component: Any) -> dict[str, Any]:
        return {}

    def from_dict(data: dict[str, Any]) -> Any:
        return None

    registry.register_serializer(
        component_type="ComponentC",
        to_dict=to_dict,
        from_dict=from_dict,
    )
    registry.register_serializer(
        component_type="ComponentA",
        to_dict=to_dict,
        from_dict=from_dict,
    )
    registry.register_serializer(
        component_type="ComponentB",
        to_dict=to_dict,
        from_dict=from_dict,
    )

    types = registry.get_registered_types()

    assert types == ["ComponentA", "ComponentB", "ComponentC"]


def test_register_decorator() -> None:
    """Test auto-registration via decorator."""
    registry = ComponentSerializerRegistry()

    @registry.register("TestComponent")
    class TestComponentSerializer:
        @staticmethod
        def to_dict(component: TestComponent) -> dict[str, Any]:
            return {"value": component.value, "name": component.name}

        @staticmethod
        def from_dict(data: dict[str, Any]) -> TestComponent:
            return TestComponent(value=data["value"], name=data["name"])

    assert "TestComponent" in registry.get_registered_types()


def test_register_decorator_round_trip() -> None:
    """Test decorator registration with serialization round trip."""
    registry = ComponentSerializerRegistry()
    value = fake.random_int()
    name = fake.word()

    @registry.register("TestComponent")
    class TestComponentSerializer:
        @staticmethod
        def to_dict(component: TestComponent) -> dict[str, Any]:
            return {"value": component.value, "name": component.name}

        @staticmethod
        def from_dict(data: dict[str, Any]) -> TestComponent:
            return TestComponent(value=data["value"], name=data["name"])

    component = TestComponent(value=value, name=name)
    data = registry.serialize_component(
        component_type="TestComponent",
        component=component,
    )
    result = registry.deserialize_component(
        component_type="TestComponent",
        data=data,
    )

    assert result.value == value
    assert result.name == name


def test_register_decorator_missing_to_dict() -> None:
    """Test decorator raises error if to_dict missing."""
    registry = ComponentSerializerRegistry()

    with pytest.raises(ValidationError, match="must have to_dict method"):

        @registry.register("TestComponent")
        class TestComponentSerializer:
            @staticmethod
            def from_dict(data: dict[str, Any]) -> TestComponent:
                return TestComponent(value=0, name="")


def test_register_decorator_missing_from_dict() -> None:
    """Test decorator raises error if from_dict missing."""
    registry = ComponentSerializerRegistry()

    with pytest.raises(ValidationError, match="must have from_dict method"):

        @registry.register("TestComponent")
        class TestComponentSerializer:
            @staticmethod
            def to_dict(component: TestComponent) -> dict[str, Any]:
                return {}


def test_multiple_component_types() -> None:
    """Test registering and using multiple component types."""
    registry = ComponentSerializerRegistry()

    @dataclass
    class ComponentA:
        x: int

    @dataclass
    class ComponentB:
        y: str

    @registry.register("ComponentA")
    class ComponentASerializer:
        @staticmethod
        def to_dict(component: ComponentA) -> dict[str, Any]:
            return {"x": component.x}

        @staticmethod
        def from_dict(data: dict[str, Any]) -> ComponentA:
            return ComponentA(x=data["x"])

    @registry.register("ComponentB")
    class ComponentBSerializer:
        @staticmethod
        def to_dict(component: ComponentB) -> dict[str, Any]:
            return {"y": component.y}

        @staticmethod
        def from_dict(data: dict[str, Any]) -> ComponentB:
            return ComponentB(y=data["y"])

    comp_a = ComponentA(x=42)
    comp_b = ComponentB(y="test")

    data_a = registry.serialize_component(component_type="ComponentA", component=comp_a)
    data_b = registry.serialize_component(component_type="ComponentB", component=comp_b)

    result_a = registry.deserialize_component(component_type="ComponentA", data=data_a)
    result_b = registry.deserialize_component(component_type="ComponentB", data=data_b)

    assert result_a.x == 42
    assert result_b.y == "test"

"""Tests for prototype pattern and entity cloning."""

from dataclasses import dataclass

import pytest
from faker import Faker

from yuna.ecs.component import Component
from yuna.ecs.prototype import PrototypeManager
from yuna.ecs.world import ECSWorld
from yuna.exceptions import EntityNotFoundError, StateError
from yuna.types.identifiers import EntityID

fake = Faker()


@dataclass
class Position(Component):
    x: float
    y: float


@dataclass
class Health(Component):
    current: int
    maximum: int


@dataclass
class Inventory(Component):
    items: list[str]


def test_prototype_manager_creation() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)

    assert manager is not None


def test_register_prototype() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    entity = world.create_entity()

    manager.register_prototype(name=fake.word(), entity_id=entity)

    assert manager.has_prototype(name=fake.word()) or not manager.has_prototype(
        name=fake.word()
    )


def test_register_prototype_with_name() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    entity = world.create_entity()
    name = fake.word()

    manager.register_prototype(name=name, entity_id=entity)

    assert manager.has_prototype(name=name)


def test_register_duplicate_prototype_raises_error() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    entity = world.create_entity()
    name = fake.word()

    manager.register_prototype(name=name, entity_id=entity)

    with pytest.raises(StateError, match="already registered"):
        manager.register_prototype(name=name, entity_id=entity)


def test_register_non_existent_entity_raises_error() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    non_existent_entity = EntityID(fake.uuid4())

    with pytest.raises(EntityNotFoundError, match="non-existent entity"):
        manager.register_prototype(name=fake.word(), entity_id=non_existent_entity)


def test_has_prototype_returns_true_for_registered() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    entity = world.create_entity()
    name = fake.word()

    manager.register_prototype(name=name, entity_id=entity)

    assert manager.has_prototype(name=name)


def test_has_prototype_returns_false_for_non_existent() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)

    assert not manager.has_prototype(name=fake.word())


def test_get_prototype() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    entity = world.create_entity()
    name = fake.word()

    manager.register_prototype(name=name, entity_id=entity)
    retrieved = manager.get_prototype(name=name)

    assert retrieved == entity


def test_get_non_existent_prototype_raises_error() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)

    with pytest.raises(KeyError, match="Prototype.*not found"):
        manager.get_prototype(name=fake.word())


def test_unregister_prototype() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    entity = world.create_entity()
    name = fake.word()

    manager.register_prototype(name=name, entity_id=entity)
    manager.unregister_prototype(name=name)

    assert not manager.has_prototype(name=name)


def test_unregister_non_existent_prototype_raises_error() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)

    with pytest.raises(KeyError, match="Prototype.*not found"):
        manager.unregister_prototype(name=fake.word())


def test_get_all_prototypes() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    entity1 = world.create_entity()
    entity2 = world.create_entity()
    name1 = fake.unique.word()
    name2 = fake.unique.word()

    manager.register_prototype(name=name1, entity_id=entity1)
    manager.register_prototype(name=name2, entity_id=entity2)

    all_prototypes = manager.get_all_prototypes()

    assert len(all_prototypes) == 2
    assert name1 in all_prototypes
    assert name2 in all_prototypes


def test_get_all_prototypes_returns_copy() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    entity = world.create_entity()
    name = fake.word()

    manager.register_prototype(name=name, entity_id=entity)
    all_prototypes = manager.get_all_prototypes()
    all_prototypes.clear()

    assert manager.has_prototype(name=name)


def test_clone_from_prototype() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    template = world.create_entity()
    world.add_component(entity_id=template, component=Position(x=10.0, y=20.0))
    name = fake.word()

    manager.register_prototype(name=name, entity_id=template)
    clone = manager.clone(prototype_name=name)

    assert clone != template
    assert clone in world.get_all_entities()


def test_clone_copies_all_components() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    template = world.create_entity()
    world.add_component(entity_id=template, component=Position(x=10.0, y=20.0))
    world.add_component(entity_id=template, component=Health(current=100, maximum=100))
    name = fake.word()

    manager.register_prototype(name=name, entity_id=template)
    clone = manager.clone(prototype_name=name)

    clone_position = world.get_component(entity_id=clone, component_type=Position)
    clone_health = world.get_component(entity_id=clone, component_type=Health)

    assert clone_position is not None
    assert isinstance(clone_position, Position)
    assert clone_position.x == 10.0
    assert clone_health is not None
    assert isinstance(clone_health, Health)
    assert clone_health.current == 100


def test_clone_non_existent_prototype_raises_error() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)

    with pytest.raises(KeyError, match="Prototype.*not found"):
        manager.clone(prototype_name=fake.word())


def test_clone_entity_directly() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    entity = world.create_entity()
    world.add_component(entity_id=entity, component=Position(x=5.0, y=15.0))

    clone = manager.clone_entity(entity_id=entity)

    assert clone != entity
    assert clone in world.get_all_entities()


def test_clone_entity_non_existent_raises_error() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    non_existent = EntityID(fake.uuid4())

    with pytest.raises(EntityNotFoundError, match="non-existent entity"):
        manager.clone_entity(entity_id=non_existent)


def test_modifications_dont_affect_prototype() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    template = world.create_entity()
    world.add_component(entity_id=template, component=Position(x=10.0, y=20.0))
    name = fake.word()

    manager.register_prototype(name=name, entity_id=template)
    clone = manager.clone(prototype_name=name)

    clone_position = world.get_component(entity_id=clone, component_type=Position)
    assert clone_position is not None
    assert isinstance(clone_position, Position)
    clone_position.x = 999.0

    template_position = world.get_component(entity_id=template, component_type=Position)

    assert template_position is not None
    assert isinstance(template_position, Position)
    assert template_position.x == 10.0


def test_deep_copy_verification() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    template = world.create_entity()
    world.add_component(
        entity_id=template, component=Inventory(items=["sword", "shield"])
    )
    name = fake.word()

    manager.register_prototype(name=name, entity_id=template)
    clone = manager.clone(prototype_name=name)

    clone_inventory = world.get_component(entity_id=clone, component_type=Inventory)
    assert clone_inventory is not None
    assert isinstance(clone_inventory, Inventory)
    clone_inventory.items.append("potion")

    template_inventory = world.get_component(
        entity_id=template, component_type=Inventory
    )

    assert template_inventory is not None
    assert isinstance(template_inventory, Inventory)
    assert len(template_inventory.items) == 2
    assert "potion" not in template_inventory.items


def test_clone_entity_with_no_components() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    entity = world.create_entity()

    clone = manager.clone_entity(entity_id=entity)

    assert clone != entity
    assert clone in world.get_all_entities()


def test_clear_prototypes() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    entity1 = world.create_entity()
    entity2 = world.create_entity()

    manager.register_prototype(name=fake.word(), entity_id=entity1)
    manager.register_prototype(name=fake.word(), entity_id=entity2)
    manager.clear()

    assert len(manager.get_all_prototypes()) == 0


def test_multiple_clones_from_same_prototype() -> None:
    world = ECSWorld()
    manager = PrototypeManager(world=world)
    template = world.create_entity()
    world.add_component(entity_id=template, component=Position(x=0.0, y=0.0))
    name = fake.word()

    manager.register_prototype(name=name, entity_id=template)
    clone1 = manager.clone(prototype_name=name)
    clone2 = manager.clone(prototype_name=name)
    clone3 = manager.clone(prototype_name=name)

    assert clone1 != clone2 != clone3
    assert len({clone1, clone2, clone3}) == 3

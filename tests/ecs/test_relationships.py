"""Tests for entity relationship management."""

from faker import Faker

from yuna.ecs.relationships import RelationshipManager
from yuna.types.identifiers import EntityID

fake = Faker()


def test_relationship_manager_creation() -> None:
    """Test RelationshipManager can be instantiated."""
    manager = RelationshipManager()
    assert manager is not None


def test_add_relationship() -> None:
    """Test adding relationship between entities."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    relationship_type = fake.word()

    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )

    assert manager.has_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )


def test_remove_relationship() -> None:
    """Test removing relationship between entities."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    relationship_type = fake.word()

    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )
    manager.remove_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )

    assert not manager.has_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )


def test_get_relationships_forward() -> None:
    """Test getting forward relationships."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    entity_c = EntityID(fake.uuid4())
    relationship_type = fake.word()

    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )
    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_c,
        relationship_type=relationship_type,
    )

    relationships = manager.get_relationships(
        entity_id=entity_a,
        relationship_type=relationship_type,
        direction="forward",
    )

    assert relationships == {entity_b, entity_c}


def test_get_relationships_reverse() -> None:
    """Test getting reverse relationships."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    entity_c = EntityID(fake.uuid4())
    relationship_type = fake.word()

    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_c,
        relationship_type=relationship_type,
    )
    manager.add_relationship(
        from_entity=entity_b,
        to_entity=entity_c,
        relationship_type=relationship_type,
    )

    relationships = manager.get_relationships(
        entity_id=entity_c,
        relationship_type=relationship_type,
        direction="reverse",
    )

    assert relationships == {entity_a, entity_b}


def test_get_relationships_empty() -> None:
    """Test getting relationships when none exist."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    relationship_type = fake.word()

    relationships = manager.get_relationships(
        entity_id=entity_a,
        relationship_type=relationship_type,
        direction="forward",
    )

    assert relationships == set()


def test_get_relationships_empty_reverse() -> None:
    """Test getting reverse relationships when none exist."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    relationship_type = fake.word()

    relationships = manager.get_relationships(
        entity_id=entity_a,
        relationship_type=relationship_type,
        direction="reverse",
    )

    assert relationships == set()


def test_get_relationships_returns_copy() -> None:
    """Test get_relationships returns copy not reference."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    relationship_type = fake.word()

    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )

    relationships_1 = manager.get_relationships(
        entity_id=entity_a,
        relationship_type=relationship_type,
    )
    relationships_2 = manager.get_relationships(
        entity_id=entity_a,
        relationship_type=relationship_type,
    )

    assert relationships_1 == relationships_2
    assert relationships_1 is not relationships_2


def test_has_relationship_returns_false_for_nonexistent() -> None:
    """Test has_relationship returns False for nonexistent relationship."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    relationship_type = fake.word()

    assert not manager.has_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )


def test_multiple_relationship_types() -> None:
    """Test entities can have multiple relationship types."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    type_1 = fake.word()
    type_2 = fake.word()

    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=type_1,
    )
    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=type_2,
    )

    assert manager.has_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=type_1,
    )
    assert manager.has_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=type_2,
    )


def test_remove_all_relationships_forward() -> None:
    """Test removing all relationships for entity (forward)."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    entity_c = EntityID(fake.uuid4())
    relationship_type = fake.word()

    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )
    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_c,
        relationship_type=relationship_type,
    )

    manager.remove_all_relationships(entity_id=entity_a)

    assert not manager.has_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )
    assert not manager.has_relationship(
        from_entity=entity_a,
        to_entity=entity_c,
        relationship_type=relationship_type,
    )


def test_remove_all_relationships_reverse() -> None:
    """Test removing all relationships for entity (reverse)."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    entity_c = EntityID(fake.uuid4())
    relationship_type = fake.word()

    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_c,
        relationship_type=relationship_type,
    )
    manager.add_relationship(
        from_entity=entity_b,
        to_entity=entity_c,
        relationship_type=relationship_type,
    )

    manager.remove_all_relationships(entity_id=entity_c)

    assert not manager.has_relationship(
        from_entity=entity_a,
        to_entity=entity_c,
        relationship_type=relationship_type,
    )
    assert not manager.has_relationship(
        from_entity=entity_b,
        to_entity=entity_c,
        relationship_type=relationship_type,
    )


def test_remove_all_relationships_multiple_types() -> None:
    """Test removing all relationships across multiple types."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    type_1 = fake.word()
    type_2 = fake.word()

    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=type_1,
    )
    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=type_2,
    )

    manager.remove_all_relationships(entity_id=entity_a)

    assert not manager.has_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=type_1,
    )
    assert not manager.has_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=type_2,
    )


def test_get_all_relationship_types() -> None:
    """Test getting all relationship types."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    type_1 = fake.word()
    type_2 = fake.word()

    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=type_1,
    )
    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=type_2,
    )

    types = manager.get_all_relationship_types()

    assert types == {type_1, type_2}


def test_get_all_relationship_types_empty() -> None:
    """Test getting relationship types when none exist."""
    manager = RelationshipManager()

    types = manager.get_all_relationship_types()

    assert types == set()


def test_remove_relationship_nonexistent_type() -> None:
    """Test removing relationship with nonexistent type does nothing."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    relationship_type = fake.word()

    manager.remove_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )


def test_add_same_relationship_twice_is_idempotent() -> None:
    """Test adding same relationship twice has no effect."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    relationship_type = fake.word()

    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )
    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )

    relationships = manager.get_relationships(
        entity_id=entity_a,
        relationship_type=relationship_type,
    )

    assert relationships == {entity_b}


def test_bidirectional_tracking() -> None:
    """Test relationships tracked bidirectionally."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    relationship_type = fake.word()

    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )

    forward = manager.get_relationships(
        entity_id=entity_a,
        relationship_type=relationship_type,
        direction="forward",
    )
    reverse = manager.get_relationships(
        entity_id=entity_b,
        relationship_type=relationship_type,
        direction="reverse",
    )

    assert forward == {entity_b}
    assert reverse == {entity_a}


def test_remove_relationship_cleans_up_empty_sets() -> None:
    """Test removing last relationship cleans up empty data structures."""
    manager = RelationshipManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    relationship_type = fake.word()

    manager.add_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )
    manager.remove_relationship(
        from_entity=entity_a,
        to_entity=entity_b,
        relationship_type=relationship_type,
    )

    assert entity_a not in manager._forward.get(relationship_type, {})
    assert entity_b not in manager._reverse.get(relationship_type, {})

"""Tests for modifier relationships."""

from faker import Faker

from yuna.modifiers.modifier import Modifier
from yuna.modifiers.relationships import (
    Relationships,
    RelationshipType,
)
from yuna.modifiers.types import ModificationType, ModifierPriority
from yuna.types.identifiers import EntityID

fake = Faker()


def test_requires_modifier_creates_relationship() -> None:
    """Test requires_modifier creates correct relationship."""
    modifier_id = fake.uuid4()

    relationship = Relationships.requires_modifier(modifier_id=modifier_id)

    assert relationship.relationship_type == RelationshipType.REQUIRES
    assert relationship.target_modifier_id == modifier_id
    assert relationship.target_tags is None
    assert relationship.target_category is None


def test_requires_tag_creates_relationship() -> None:
    """Test requires_tag creates correct relationship."""
    tag = fake.word()

    relationship = Relationships.requires_tag(tag=tag)

    assert relationship.relationship_type == RelationshipType.REQUIRES
    assert relationship.target_modifier_id is None
    assert relationship.target_tags == frozenset({tag})
    assert relationship.target_category is None


def test_requires_category_creates_relationship() -> None:
    """Test requires_category creates correct relationship."""
    category = fake.word()

    relationship = Relationships.requires_category(category=category)

    assert relationship.relationship_type == RelationshipType.REQUIRES
    assert relationship.target_modifier_id is None
    assert relationship.target_tags is None
    assert relationship.target_category == category


def test_blocks_modifier_creates_relationship() -> None:
    """Test blocks_modifier creates correct relationship."""
    modifier_id = fake.uuid4()

    relationship = Relationships.blocks_modifier(modifier_id=modifier_id)

    assert relationship.relationship_type == RelationshipType.BLOCKS
    assert relationship.target_modifier_id == modifier_id
    assert relationship.target_tags is None
    assert relationship.target_category is None


def test_blocks_tag_creates_relationship() -> None:
    """Test blocks_tag creates correct relationship."""
    tag = fake.word()

    relationship = Relationships.blocks_tag(tag=tag)

    assert relationship.relationship_type == RelationshipType.BLOCKS
    assert relationship.target_modifier_id is None
    assert relationship.target_tags == frozenset({tag})
    assert relationship.target_category is None


def test_blocks_category_creates_relationship() -> None:
    """Test blocks_category creates correct relationship."""
    category = fake.word()

    relationship = Relationships.blocks_category(category=category)

    assert relationship.relationship_type == RelationshipType.BLOCKS
    assert relationship.target_modifier_id is None
    assert relationship.target_tags is None
    assert relationship.target_category == category


def test_replaces_modifier_creates_relationship() -> None:
    """Test replaces_modifier creates correct relationship."""
    modifier_id = fake.uuid4()

    relationship = Relationships.replaces_modifier(modifier_id=modifier_id)

    assert relationship.relationship_type == RelationshipType.REPLACES
    assert relationship.target_modifier_id == modifier_id
    assert relationship.target_tags is None
    assert relationship.target_category is None


def test_replaces_tag_creates_relationship() -> None:
    """Test replaces_tag creates correct relationship."""
    tag = fake.word()

    relationship = Relationships.replaces_tag(tag=tag)

    assert relationship.relationship_type == RelationshipType.REPLACES
    assert relationship.target_modifier_id is None
    assert relationship.target_tags == frozenset({tag})
    assert relationship.target_category is None


def test_replaces_category_creates_relationship() -> None:
    """Test replaces_category creates correct relationship."""
    category = fake.word()

    relationship = Relationships.replaces_category(category=category)

    assert relationship.relationship_type == RelationshipType.REPLACES
    assert relationship.target_modifier_id is None
    assert relationship.target_tags is None
    assert relationship.target_category == category


def test_exclusive_with_modifier_creates_relationship() -> None:
    """Test exclusive_with_modifier creates correct relationship."""
    modifier_id = fake.uuid4()
    strength = fake.pyfloat(min_value=0.1, max_value=10.0)

    relationship = Relationships.exclusive_with_modifier(
        modifier_id=modifier_id, strength=strength
    )

    assert relationship.relationship_type == RelationshipType.EXCLUSIVE_WITH
    assert relationship.target_modifier_id == modifier_id
    assert relationship.target_tags is None
    assert relationship.target_category is None
    assert relationship.strength == strength


def test_exclusive_with_modifier_default_strength() -> None:
    """Test exclusive_with_modifier uses default strength."""
    modifier_id = fake.uuid4()

    relationship = Relationships.exclusive_with_modifier(modifier_id=modifier_id)

    assert relationship.strength == 1.0


def test_exclusive_with_tag_creates_relationship() -> None:
    """Test exclusive_with_tag creates correct relationship."""
    tag = fake.word()
    strength = fake.pyfloat(min_value=0.1, max_value=10.0)

    relationship = Relationships.exclusive_with_tag(tag=tag, strength=strength)

    assert relationship.relationship_type == RelationshipType.EXCLUSIVE_WITH
    assert relationship.target_modifier_id is None
    assert relationship.target_tags == frozenset({tag})
    assert relationship.target_category is None
    assert relationship.strength == strength


def test_exclusive_with_tag_default_strength() -> None:
    """Test exclusive_with_tag uses default strength."""
    tag = fake.word()

    relationship = Relationships.exclusive_with_tag(tag=tag)

    assert relationship.strength == 1.0


def test_exclusive_with_category_creates_relationship() -> None:
    """Test exclusive_with_category creates correct relationship."""
    category = fake.word()
    strength = fake.pyfloat(min_value=0.1, max_value=10.0)

    relationship = Relationships.exclusive_with_category(
        category=category, strength=strength
    )

    assert relationship.relationship_type == RelationshipType.EXCLUSIVE_WITH
    assert relationship.target_modifier_id is None
    assert relationship.target_tags is None
    assert relationship.target_category == category
    assert relationship.strength == strength


def test_exclusive_with_category_default_strength() -> None:
    """Test exclusive_with_category uses default strength."""
    category = fake.word()

    relationship = Relationships.exclusive_with_category(category=category)

    assert relationship.strength == 1.0


def test_triggers_modifier_creates_relationship() -> None:
    """Test triggers_modifier creates correct relationship."""
    triggered_modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
    )

    relationship = Relationships.triggers_modifier(modifier=triggered_modifier)

    assert relationship.relationship_type == RelationshipType.TRIGGERS
    assert relationship.target_modifier_id == triggered_modifier.modifier_id

"""Tests for RelationshipStage."""

from faker import Faker

from yuna.modifiers.config import ModifierConfig
from yuna.modifiers.context import ModifierContext
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.relationships import (
    ModifierRelationship,
    Relationships,
    RelationshipType,
)
from yuna.modifiers.stages import RelationshipStage
from yuna.modifiers.types import ModificationType, ModifierPriority
from yuna.pipeline.context import PipelineContext
from yuna.types.identifiers import EntityID

fake = Faker()


def test_relationship_stage_name() -> None:
    """Test relationship stage has correct name."""
    stage = RelationshipStage()

    assert stage.name == "relationship"


def test_relationship_stage_no_relationships() -> None:
    """Test relationship stage passes through modifiers without relationships."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    context = ModifierContext(modifiers=[modifier], config=ModifierConfig())
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is modifier


def test_relationship_stage_removes_modifier_missing_requirement() -> None:
    """Test relationship stage removes modifier missing required modifier."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())

    modifier_with_requirement = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        relationships=(Relationships.requires_modifier(modifier_id=fake.uuid4()),),
    )

    context = ModifierContext(
        modifiers=[modifier_with_requirement], config=ModifierConfig()
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 0


def test_relationship_stage_keeps_modifier_with_satisfied_requirement() -> None:
    """Test relationship stage keeps modifier when requirement is satisfied."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    required_id = fake.uuid4()

    required_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=required_id,
    )

    dependent_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        relationships=(Relationships.requires_modifier(modifier_id=required_id),),
    )

    context = ModifierContext(
        modifiers=[required_modifier, dependent_modifier], config=ModifierConfig()
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 2


def test_relationship_stage_requires_tag() -> None:
    """Test relationship stage requires tag functionality."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    required_tag = fake.word()

    tagged_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        tags=frozenset({required_tag}),
    )

    dependent_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.requires_tag(tag=required_tag),),
    )

    context = ModifierContext(
        modifiers=[tagged_modifier, dependent_modifier], config=ModifierConfig()
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 2


def test_relationship_stage_requires_category() -> None:
    """Test relationship stage requires category functionality."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    required_category = fake.word()

    categorized_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(required_category,),
    )

    dependent_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.requires_category(category=required_category),),
    )

    context = ModifierContext(
        modifiers=[categorized_modifier, dependent_modifier], config=ModifierConfig()
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 2


def test_relationship_stage_blocks_modifier() -> None:
    """Test relationship stage blocks specific modifier."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    blocked_id = fake.uuid4()

    blocking_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.blocks_modifier(modifier_id=blocked_id),),
    )

    blocked_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=blocked_id,
    )

    context = ModifierContext(
        modifiers=[blocking_modifier, blocked_modifier], config=ModifierConfig()
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is blocking_modifier


def test_relationship_stage_blocks_tag() -> None:
    """Test relationship stage blocks modifiers with tag."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    blocked_tag = fake.word()

    blocking_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.blocks_tag(tag=blocked_tag),),
    )

    blocked_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        tags=frozenset({blocked_tag}),
    )

    context = ModifierContext(
        modifiers=[blocking_modifier, blocked_modifier], config=ModifierConfig()
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is blocking_modifier


def test_relationship_stage_blocks_category() -> None:
    """Test relationship stage blocks modifiers in category."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    blocked_category = fake.word()

    blocking_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.blocks_category(category=blocked_category),),
    )

    blocked_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(blocked_category,),
    )

    context = ModifierContext(
        modifiers=[blocking_modifier, blocked_modifier], config=ModifierConfig()
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is blocking_modifier


def test_relationship_stage_replaces_modifier() -> None:
    """Test relationship stage replaces specific modifier."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    replaced_id = fake.uuid4()

    replacing_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.replaces_modifier(modifier_id=replaced_id),),
    )

    replaced_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=replaced_id,
    )

    context = ModifierContext(
        modifiers=[replacing_modifier, replaced_modifier], config=ModifierConfig()
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is replacing_modifier


def test_relationship_stage_replaces_tag() -> None:
    """Test relationship stage replaces modifiers with tag."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    replaced_tag = fake.word()

    replacing_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.replaces_tag(tag=replaced_tag),),
    )

    replaced_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        tags=frozenset({replaced_tag}),
    )

    context = ModifierContext(
        modifiers=[replacing_modifier, replaced_modifier], config=ModifierConfig()
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is replacing_modifier


def test_relationship_stage_replaces_category() -> None:
    """Test relationship stage replaces modifiers in category."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    replaced_category = fake.word()

    replacing_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.replaces_category(category=replaced_category),),
    )

    replaced_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(replaced_category,),
    )

    context = ModifierContext(
        modifiers=[replacing_modifier, replaced_modifier], config=ModifierConfig()
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is replacing_modifier


def test_relationship_stage_exclusive_with_modifier_higher_strength_wins() -> None:
    """Test exclusive relationship with higher strength wins."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    exclusive_id_1 = fake.uuid4()
    exclusive_id_2 = fake.uuid4()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=exclusive_id_1,
        relationships=(
            Relationships.exclusive_with_modifier(
                modifier_id=exclusive_id_2, strength=1.0
            ),
        ),
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=exclusive_id_2,
        relationships=(
            Relationships.exclusive_with_modifier(
                modifier_id=exclusive_id_1, strength=2.0
            ),
        ),
    )

    context = ModifierContext(modifiers=[modifier1, modifier2], config=ModifierConfig())
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is modifier2


def test_relationship_stage_exclusive_with_category() -> None:
    """Test exclusive relationship with category."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    exclusive_category = fake.word()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(exclusive_category,),
        relationships=(
            Relationships.exclusive_with_category(
                category=exclusive_category, strength=1.0
            ),
        ),
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(exclusive_category,),
        relationships=(
            Relationships.exclusive_with_category(
                category=exclusive_category, strength=2.0
            ),
        ),
    )

    context = ModifierContext(modifiers=[modifier1, modifier2], config=ModifierConfig())
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is modifier2


def test_relationship_stage_with_profiling_enabled() -> None:
    """Test relationship stage with profiling enabled."""
    stage = RelationshipStage(profiling_enabled=True)
    entity_id = EntityID(fake.uuid4())

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
    )

    context = ModifierContext(modifiers=[modifier], config=ModifierConfig())
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is modifier


def test_relationship_stage_requirement_no_match() -> None:
    """Test relationship requirement with no matching modifiers."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())

    modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.requires_tag(tag=fake.word()),),
    )

    context = ModifierContext(modifiers=[modifier], config=ModifierConfig())
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 0


def test_relationship_stage_exclusive_with_tag() -> None:
    """Test exclusive relationship with tags."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    exclusive_tag = fake.word()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        tags=frozenset({exclusive_tag}),
        relationships=(
            Relationships.exclusive_with_tag(tag=exclusive_tag, strength=1.0),
        ),
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        tags=frozenset({exclusive_tag}),
        relationships=(
            Relationships.exclusive_with_tag(tag=exclusive_tag, strength=2.0),
        ),
    )

    context = ModifierContext(modifiers=[modifier1, modifier2], config=ModifierConfig())
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is modifier2


def test_relationship_stage_exclusive_lower_strength_loses() -> None:
    """Test exclusive relationship where lower strength is excluded."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    exclusive_category = fake.word()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(exclusive_category,),
        relationships=(
            Relationships.exclusive_with_category(
                category=exclusive_category, strength=2.0
            ),
        ),
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(exclusive_category,),
        relationships=(
            Relationships.exclusive_with_category(
                category=exclusive_category, strength=1.0
            ),
        ),
    )

    context = ModifierContext(modifiers=[modifier1, modifier2], config=ModifierConfig())
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is modifier1


def test_relationship_stage_exclusive_modifier_higher_strength_excludes_other() -> None:
    """Test exclusive modifier relationship where higher strength excludes other."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    modifier1_id = fake.uuid4()
    modifier2_id = fake.uuid4()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=modifier1_id,
        relationships=(
            Relationships.exclusive_with_modifier(
                modifier_id=modifier2_id, strength=2.0
            ),
        ),
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=modifier2_id,
        relationships=(
            Relationships.exclusive_with_modifier(
                modifier_id=modifier1_id, strength=1.0
            ),
        ),
    )

    context = ModifierContext(modifiers=[modifier1, modifier2], config=ModifierConfig())
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is modifier1


def test_relationship_stage_exclusive_tags_higher_strength_excludes_other() -> None:
    """Test exclusive tags relationship where higher strength excludes other."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    shared_tag = fake.word()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        tags=frozenset({shared_tag}),
        relationships=(Relationships.exclusive_with_tag(tag=shared_tag, strength=2.0),),
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        tags=frozenset({shared_tag}),
        relationships=(Relationships.exclusive_with_tag(tag=shared_tag, strength=1.0),),
    )

    context = ModifierContext(modifiers=[modifier1, modifier2], config=ModifierConfig())
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is modifier1


def test_relationship_stage_exclusive_category_default_strength() -> None:
    """Test exclusive category uses default strength when no explicit strength."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    exclusive_category = fake.word()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(exclusive_category,),
        relationships=(
            Relationships.exclusive_with_category(
                category=exclusive_category, strength=0.5
            ),
        ),
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(exclusive_category,),
        relationships=(
            Relationships.exclusive_with_category(category=exclusive_category),
        ),
    )

    context = ModifierContext(modifiers=[modifier1, modifier2], config=ModifierConfig())
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is modifier2


def test_relationship_stage_exclusive_modifier_default_strength() -> None:
    """Test exclusive modifier uses default strength when no explicit strength."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    modifier1_id = fake.uuid4()
    modifier2_id = fake.uuid4()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=modifier1_id,
        relationships=(
            Relationships.exclusive_with_modifier(
                modifier_id=modifier2_id, strength=0.5
            ),
        ),
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=modifier2_id,
        relationships=(
            Relationships.exclusive_with_modifier(modifier_id=modifier1_id),
        ),
    )

    context = ModifierContext(modifiers=[modifier1, modifier2], config=ModifierConfig())
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is modifier2


def test_relationship_stage_exclusive_tags_default_strength() -> None:
    """Test exclusive tags uses default strength for no relationship."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())
    shared_tag = fake.word()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        tags=frozenset({shared_tag}),
        relationships=(Relationships.exclusive_with_tag(tag=shared_tag, strength=0.5),),
    )

    modifier2 = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        tags=frozenset({shared_tag}),
        relationships=(Relationships.exclusive_with_tag(tag=shared_tag),),
    )

    context = ModifierContext(modifiers=[modifier1, modifier2], config=ModifierConfig())
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 1
    assert result.modifiers[0] is modifier2


def test_relationship_stage_blocks_relationship_with_no_targets() -> None:
    """Test relationship with no valid targets doesn't match anything."""
    stage = RelationshipStage()
    entity_id = EntityID(fake.uuid4())

    invalid_relationship = ModifierRelationship(
        relationship_type=RelationshipType.BLOCKS
    )

    blocking_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(invalid_relationship,),
    )

    other_modifier = Modifier(
        entity_id=entity_id,
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=fake.uuid4(),
        tags=frozenset({fake.word()}),
        categories=(fake.word(),),
    )

    context = ModifierContext(
        modifiers=[blocking_modifier, other_modifier], config=ModifierConfig()
    )
    pipe_context = PipelineContext()

    result = stage.process(value=context, context=pipe_context)

    assert len(result.modifiers) == 2


def test_get_exclusivity_strength_returns_default_when_no_match() -> None:
    """Test helper returns default strength when no matching relationship."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.exclusive_with_category(category=fake.word()),),
    )

    strength = RelationshipStage._get_exclusivity_strength(
        modifier=modifier, category=fake.word()
    )

    assert strength == 1.0


def test_get_exclusivity_strength_for_modifier_returns_default_when_no_match() -> None:
    """Test helper returns default strength when no matching relationship."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(
            Relationships.exclusive_with_modifier(modifier_id=fake.uuid4()),
        ),
    )

    strength = RelationshipStage._get_exclusivity_strength_for_modifier(
        modifier=modifier, target_id=fake.uuid4()
    )

    assert strength == 1.0


def test_get_exclusivity_strength_for_tags_returns_default_when_no_match() -> None:
    """Test helper returns default strength when no matching relationship."""
    modifier = Modifier(
        entity_id=EntityID(fake.uuid4()),
        stat=fake.word(),
        modification_type=ModificationType.FLAT,
        value=fake.pyfloat(min_value=1.0, max_value=100.0),
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.exclusive_with_tag(tag=fake.word()),),
    )

    strength = RelationshipStage._get_exclusivity_strength_for_tags(
        modifier=modifier, target_tags=frozenset({fake.word()})
    )

    assert strength == 1.0

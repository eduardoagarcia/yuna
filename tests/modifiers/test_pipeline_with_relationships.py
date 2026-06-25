"""Integration tests for ModifierPipeline with relationship features."""

from faker import Faker

from yuna.modifiers.config import ModifierConfig, StackingRule
from yuna.modifiers.modifier import Modifier
from yuna.modifiers.pipeline import ModifierPipeline
from yuna.modifiers.relationships import Relationships
from yuna.modifiers.types import ModificationType, ModifierPriority
from yuna.types.identifiers import EntityID

fake = Faker()


def create_test_pipeline() -> tuple[ModifierConfig, ModifierPipeline]:
    """Create pipeline with test stats registered."""
    config = ModifierConfig()
    config.register_stat(
        name="power",
        min_value=0.0,
        max_value=1000.0,
        stacking_rule=StackingRule.ADD,
    )
    pipeline = ModifierPipeline(config=config)
    return config, pipeline


def test_pipeline_removes_modifier_missing_requirement() -> None:
    """Test pipeline removes modifier when requirement is not met."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())

    modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=50.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.requires_modifier(modifier_id=fake.uuid4()),),
    )

    pipeline.queue_modifier(modifier=modifier)
    results = pipeline.process(current_tick=0)

    assert (entity_id, "power") not in results


def test_pipeline_keeps_modifier_when_requirement_satisfied() -> None:
    """Test pipeline keeps modifier when requirement is satisfied."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    required_id = fake.uuid4()

    required_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=required_id,
    )

    dependent_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.requires_modifier(modifier_id=required_id),),
    )

    pipeline.queue_modifier(modifier=required_modifier)
    pipeline.queue_modifier(modifier=dependent_modifier)
    results = pipeline.process(current_tick=0)

    assert results[(entity_id, "power")] == 30.0


def test_pipeline_blocks_modifier() -> None:
    """Test pipeline blocks modifier when blocking relationship exists."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    blocked_id = fake.uuid4()

    blocking_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.blocks_modifier(modifier_id=blocked_id),),
    )

    blocked_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=blocked_id,
    )

    pipeline.queue_modifier(modifier=blocking_modifier)
    pipeline.queue_modifier(modifier=blocked_modifier)
    results = pipeline.process(current_tick=0)

    assert results[(entity_id, "power")] == 10.0


def test_pipeline_replaces_modifier() -> None:
    """Test pipeline replaces modifier when replacement relationship exists."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    replaced_id = fake.uuid4()

    replacing_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=30.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.replaces_modifier(modifier_id=replaced_id),),
    )

    replaced_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=replaced_id,
    )

    pipeline.queue_modifier(modifier=replacing_modifier)
    pipeline.queue_modifier(modifier=replaced_modifier)
    results = pipeline.process(current_tick=0)

    assert results[(entity_id, "power")] == 30.0


def test_pipeline_exclusive_modifiers_higher_strength_wins() -> None:
    """Test pipeline resolves exclusive modifiers based on strength."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    exclusive_id_1 = fake.uuid4()
    exclusive_id_2 = fake.uuid4()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=10.0,
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
        stat="power",
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=exclusive_id_2,
        relationships=(
            Relationships.exclusive_with_modifier(
                modifier_id=exclusive_id_1, strength=2.0
            ),
        ),
    )

    pipeline.queue_modifier(modifier=modifier1)
    pipeline.queue_modifier(modifier=modifier2)
    results = pipeline.process(current_tick=0)

    assert results[(entity_id, "power")] == 20.0


def test_pipeline_requires_tag() -> None:
    """Test pipeline requires tag functionality."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    required_tag = fake.word()

    tagged_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        tags=frozenset({required_tag}),
    )

    dependent_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.requires_tag(tag=required_tag),),
    )

    pipeline.queue_modifier(modifier=tagged_modifier)
    pipeline.queue_modifier(modifier=dependent_modifier)
    results = pipeline.process(current_tick=0)

    assert results[(entity_id, "power")] == 30.0


def test_pipeline_blocks_tag() -> None:
    """Test pipeline blocks tag functionality."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    blocked_tag = fake.word()

    blocking_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.blocks_tag(tag=blocked_tag),),
    )

    blocked_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        tags=frozenset({blocked_tag}),
    )

    pipeline.queue_modifier(modifier=blocking_modifier)
    pipeline.queue_modifier(modifier=blocked_modifier)
    results = pipeline.process(current_tick=0)

    assert results[(entity_id, "power")] == 10.0


def test_pipeline_replaces_category() -> None:
    """Test pipeline replaces category functionality."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    replaced_category = fake.word()

    replacing_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=30.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.replaces_category(category=replaced_category),),
    )

    replaced_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(replaced_category,),
    )

    pipeline.queue_modifier(modifier=replacing_modifier)
    pipeline.queue_modifier(modifier=replaced_modifier)
    results = pipeline.process(current_tick=0)

    assert results[(entity_id, "power")] == 30.0


def test_pipeline_exclusive_category() -> None:
    """Test pipeline resolves exclusive category based on strength."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    exclusive_category = fake.word()

    modifier1 = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=10.0,
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
        stat="power",
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        categories=(exclusive_category,),
        relationships=(
            Relationships.exclusive_with_category(
                category=exclusive_category, strength=2.0
            ),
        ),
    )

    pipeline.queue_modifier(modifier=modifier1)
    pipeline.queue_modifier(modifier=modifier2)
    results = pipeline.process(current_tick=0)

    assert results[(entity_id, "power")] == 20.0


def test_pipeline_complex_relationship_chain() -> None:
    """Test pipeline handles complex relationship chains correctly."""
    config, pipeline = create_test_pipeline()
    entity_id = EntityID(fake.uuid4())
    base_id = fake.uuid4()
    enhanced_id = fake.uuid4()

    base_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=base_id,
    )

    enhanced_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=enhanced_id,
        relationships=(Relationships.requires_modifier(modifier_id=base_id),),
    )

    ultimate_modifier = Modifier(
        entity_id=entity_id,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=30.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.requires_modifier(modifier_id=enhanced_id),),
    )

    pipeline.queue_modifier(modifier=base_modifier)
    pipeline.queue_modifier(modifier=enhanced_modifier)
    pipeline.queue_modifier(modifier=ultimate_modifier)
    results = pipeline.process(current_tick=0)

    assert results[(entity_id, "power")] == 60.0


def test_pipeline_isolates_relationships_between_entities() -> None:
    """Test pipeline correctly isolates relationships between different entities."""
    config, pipeline = create_test_pipeline()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    required_id = fake.uuid4()

    required_modifier = Modifier(
        entity_id=entity1,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=10.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        modifier_id=required_id,
    )

    dependent_modifier = Modifier(
        entity_id=entity2,
        stat="power",
        modification_type=ModificationType.FLAT,
        value=20.0,
        priority=ModifierPriority.NORMAL,
        source=fake.word(),
        relationships=(Relationships.requires_modifier(modifier_id=required_id),),
    )

    pipeline.queue_modifier(modifier=required_modifier)
    pipeline.queue_modifier(modifier=dependent_modifier)
    results = pipeline.process(current_tick=0)

    assert results[(entity1, "power")] == 10.0
    assert (entity2, "power") not in results

"""Tests for steering behaviors."""

from unittest.mock import MagicMock

from faker import Faker

from yuna.ai.steering import (
    AvoidanceBehavior,
    FleeBehavior,
    FlockingBehavior,
    SeekBehavior,
    SteeringComponent,
    SteeringContext,
    SteeringSystem,
    WanderBehavior,
)
from yuna.ecs.world import ECSWorld
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

fake = Faker()


def test_steering_context_creation() -> None:
    """Test creating SteeringContext with defaults."""
    position = Vector2(x=0.0, y=0.0)
    velocity = Vector2(x=1.0, y=0.0)
    max_speed = 10.0
    max_force = 5.0

    context = SteeringContext(
        position=position,
        velocity=velocity,
        max_speed=max_speed,
        max_force=max_force,
    )

    assert context.position == position
    assert context.velocity == velocity
    assert context.max_speed == max_speed
    assert context.max_force == max_force
    assert context.target is None
    assert context.entities_nearby == []


def test_steering_context_with_target() -> None:
    """Test creating SteeringContext with target."""
    target = Vector2(x=10.0, y=10.0)
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        target=target,
    )

    assert context.target == target


def test_seek_behavior_toward_target() -> None:
    """Test SeekBehavior calculates force toward target."""
    behavior = SeekBehavior()
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        target=Vector2(x=10.0, y=0.0),
    )

    force = behavior.calculate(context=context)

    assert force.x > 0.0
    assert force.y == 0.0
    assert force.magnitude() <= context.max_force


def test_seek_behavior_no_target() -> None:
    """Test SeekBehavior with no target returns zero force."""
    behavior = SeekBehavior()
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        target=None,
    )

    force = behavior.calculate(context=context)

    assert force.x == 0.0
    assert force.y == 0.0


def test_seek_behavior_at_target() -> None:
    """Test SeekBehavior when already at target."""
    behavior = SeekBehavior()
    context = SteeringContext(
        position=Vector2(x=5.0, y=5.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        target=Vector2(x=5.0, y=5.0),
    )

    force = behavior.calculate(context=context)

    assert force.x == 0.0
    assert force.y == 0.0


def test_seek_behavior_clamps_to_max_force() -> None:
    """Test SeekBehavior clamps steering force to max_force."""
    behavior = SeekBehavior()
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=-10.0, y=0.0),
        max_speed=10.0,
        max_force=2.0,
        target=Vector2(x=10.0, y=0.0),
    )

    force = behavior.calculate(context=context)

    assert force.magnitude() <= context.max_force


def test_flee_behavior_away_from_target() -> None:
    """Test FleeBehavior calculates force away from target."""
    behavior = FleeBehavior()
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        target=Vector2(x=10.0, y=0.0),
    )

    force = behavior.calculate(context=context)

    assert force.x < 0.0
    assert force.magnitude() <= context.max_force


def test_flee_behavior_no_target() -> None:
    """Test FleeBehavior with no target returns zero force."""
    behavior = FleeBehavior()
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        target=None,
    )

    force = behavior.calculate(context=context)

    assert force.x == 0.0
    assert force.y == 0.0


def test_flee_behavior_at_target() -> None:
    """Test FleeBehavior when at target position."""
    behavior = FleeBehavior()
    context = SteeringContext(
        position=Vector2(x=5.0, y=5.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        target=Vector2(x=5.0, y=5.0),
    )

    force = behavior.calculate(context=context)

    assert force.x == 0.0
    assert force.y == 0.0


def test_flee_behavior_clamps_to_max_force() -> None:
    """Test FleeBehavior clamps steering force to max_force."""
    behavior = FleeBehavior()
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=10.0, y=0.0),
        max_speed=10.0,
        max_force=2.0,
        target=Vector2(x=10.0, y=0.0),
    )

    force = behavior.calculate(context=context)

    assert force.magnitude() <= context.max_force


def test_wander_behavior_creation() -> None:
    """Test creating WanderBehavior with defaults."""
    behavior = WanderBehavior()

    assert behavior._wander_radius == 5.0
    assert behavior._wander_distance == 10.0
    assert behavior._angle_change == 0.3


def test_wander_behavior_with_custom_parameters() -> None:
    """Test creating WanderBehavior with custom parameters."""
    behavior = WanderBehavior(
        wander_radius=3.0,
        wander_distance=7.0,
        angle_change=0.5,
    )

    assert behavior._wander_radius == 3.0
    assert behavior._wander_distance == 7.0
    assert behavior._angle_change == 0.5


def test_wander_behavior_generates_force() -> None:
    """Test WanderBehavior generates steering force."""
    behavior = WanderBehavior()
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=1.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
    )

    force = behavior.calculate(context=context)

    assert force.magnitude() <= context.max_force


def test_wander_behavior_with_zero_velocity() -> None:
    """Test WanderBehavior with zero velocity."""
    behavior = WanderBehavior()
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
    )

    force = behavior.calculate(context=context)

    assert force.magnitude() <= context.max_force


def test_wander_behavior_angle_changes() -> None:
    """Test WanderBehavior changes angle over time."""
    behavior = WanderBehavior(angle_change=0.5)
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=1.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
    )

    initial_angle = behavior._wander_angle
    behavior.calculate(context=context)

    assert behavior._wander_angle != initial_angle


def test_avoidance_behavior_creation() -> None:
    """Test creating AvoidanceBehavior with defaults."""
    behavior = AvoidanceBehavior()

    assert behavior._avoidance_radius == 3.0


def test_avoidance_behavior_with_custom_radius() -> None:
    """Test creating AvoidanceBehavior with custom radius."""
    behavior = AvoidanceBehavior(avoidance_radius=5.0)

    assert behavior._avoidance_radius == 5.0


def test_avoidance_behavior_avoids_nearby_entity() -> None:
    """Test AvoidanceBehavior generates force away from nearby entity."""
    behavior = AvoidanceBehavior(avoidance_radius=5.0)
    entity_id = EntityID(fake.uuid4())
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        entities_nearby=[(entity_id, Vector2(x=2.0, y=0.0))],
    )

    force = behavior.calculate(context=context)

    assert force.x < 0.0
    assert force.magnitude() <= context.max_force


def test_avoidance_behavior_ignores_distant_entity() -> None:
    """Test AvoidanceBehavior ignores entities outside radius."""
    behavior = AvoidanceBehavior(avoidance_radius=3.0)
    entity_id = EntityID(fake.uuid4())
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        entities_nearby=[(entity_id, Vector2(x=10.0, y=0.0))],
    )

    force = behavior.calculate(context=context)

    assert force.x == 0.0
    assert force.y == 0.0


def test_avoidance_behavior_no_nearby_entities() -> None:
    """Test AvoidanceBehavior with no nearby entities."""
    behavior = AvoidanceBehavior()
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        entities_nearby=[],
    )

    force = behavior.calculate(context=context)

    assert force.x == 0.0
    assert force.y == 0.0


def test_avoidance_behavior_multiple_entities() -> None:
    """Test AvoidanceBehavior with multiple nearby entities."""
    behavior = AvoidanceBehavior(avoidance_radius=5.0)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        entities_nearby=[
            (entity1, Vector2(x=2.0, y=0.0)),
            (entity2, Vector2(x=0.0, y=2.0)),
        ],
    )

    force = behavior.calculate(context=context)

    assert force.magnitude() > 0.0
    assert force.magnitude() <= context.max_force


def test_flocking_behavior_creation() -> None:
    """Test creating FlockingBehavior with defaults."""
    behavior = FlockingBehavior()

    assert behavior._separation_weight == 1.5
    assert behavior._alignment_weight == 1.0
    assert behavior._cohesion_weight == 1.0
    assert behavior._neighbor_radius == 10.0


def test_flocking_behavior_with_custom_parameters() -> None:
    """Test creating FlockingBehavior with custom parameters."""
    behavior = FlockingBehavior(
        separation_weight=2.0,
        alignment_weight=1.5,
        cohesion_weight=0.5,
        neighbor_radius=15.0,
    )

    assert behavior._separation_weight == 2.0
    assert behavior._alignment_weight == 1.5
    assert behavior._cohesion_weight == 0.5
    assert behavior._neighbor_radius == 15.0


def test_flocking_behavior_no_neighbors() -> None:
    """Test FlockingBehavior with no neighbors."""
    behavior = FlockingBehavior()
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        entities_nearby=[],
    )

    force = behavior.calculate(context=context)

    assert force.x == 0.0
    assert force.y == 0.0


def test_flocking_behavior_with_neighbors() -> None:
    """Test FlockingBehavior generates force with neighbors."""
    behavior = FlockingBehavior(neighbor_radius=10.0)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        entities_nearby=[
            (entity1, Vector2(x=2.0, y=0.0)),
            (entity2, Vector2(x=0.0, y=2.0)),
        ],
    )

    force = behavior.calculate(context=context)

    assert force.magnitude() <= context.max_force


def test_flocking_behavior_ignores_distant_neighbors() -> None:
    """Test FlockingBehavior ignores neighbors outside radius."""
    behavior = FlockingBehavior(neighbor_radius=5.0)
    entity_id = EntityID(fake.uuid4())
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=5.0,
        entities_nearby=[(entity_id, Vector2(x=20.0, y=0.0))],
    )

    force = behavior.calculate(context=context)

    assert force.x == 0.0
    assert force.y == 0.0


def test_flocking_behavior_separation() -> None:
    """Test FlockingBehavior separation component."""
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    neighbors = [
        (entity1, Vector2(x=1.0, y=0.0)),
        (entity2, Vector2(x=0.0, y=1.0)),
    ]

    separation = FlockingBehavior._calculate_separation(
        position=Vector2(x=0.0, y=0.0), neighbors=neighbors
    )

    assert separation.magnitude() > 0.0


def test_flocking_behavior_cohesion() -> None:
    """Test FlockingBehavior cohesion component."""
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    neighbors = [
        (entity1, Vector2(x=5.0, y=0.0)),
        (entity2, Vector2(x=0.0, y=5.0)),
    ]

    cohesion = FlockingBehavior._calculate_cohesion(
        position=Vector2(x=0.0, y=0.0), neighbors=neighbors
    )

    assert cohesion.magnitude() > 0.0


def test_flocking_behavior_cohesion_empty_neighbors() -> None:
    """Test FlockingBehavior cohesion with empty neighbors."""
    cohesion = FlockingBehavior._calculate_cohesion(
        position=Vector2(x=0.0, y=0.0), neighbors=[]
    )

    assert cohesion.x == 0.0
    assert cohesion.y == 0.0


def test_flocking_behavior_alignment() -> None:
    """Test FlockingBehavior alignment component."""
    entity1 = EntityID(fake.uuid4())
    neighbors = [(entity1, Vector2(x=1.0, y=1.0))]

    alignment = FlockingBehavior._calculate_alignment(
        velocity=Vector2(x=1.0, y=0.0), neighbors=neighbors
    )

    assert alignment.x == 0.0
    assert alignment.y == 0.0


def test_steering_component_creation() -> None:
    """Test creating SteeringComponent with defaults."""
    component = SteeringComponent()

    assert component.behaviors == []
    assert component.weights == []
    assert component.max_speed == 10.0
    assert component.max_force == 5.0


def test_steering_component_with_custom_values() -> None:
    """Test creating SteeringComponent with custom values."""
    component = SteeringComponent(max_speed=15.0, max_force=7.0)

    assert component.max_speed == 15.0
    assert component.max_force == 7.0


def test_steering_component_add_behavior() -> None:
    """Test adding behavior to SteeringComponent."""
    component = SteeringComponent()
    behavior = SeekBehavior()

    component.add_behavior(behavior=behavior, weight=2.0)

    assert len(component.behaviors) == 1
    assert component.behaviors[0] == behavior
    assert component.weights[0] == 2.0


def test_steering_component_add_multiple_behaviors() -> None:
    """Test adding multiple behaviors to SteeringComponent."""
    component = SteeringComponent()
    seek = SeekBehavior()
    flee = FleeBehavior()

    component.add_behavior(behavior=seek, weight=1.0)
    component.add_behavior(behavior=flee, weight=0.5)

    assert len(component.behaviors) == 2
    assert len(component.weights) == 2


def test_steering_component_remove_behavior() -> None:
    """Test removing behavior from SteeringComponent."""
    component = SteeringComponent()
    behavior = SeekBehavior()
    component.add_behavior(behavior=behavior, weight=1.0)

    component.remove_behavior(behavior=behavior)

    assert len(component.behaviors) == 0
    assert len(component.weights) == 0


def test_steering_component_remove_nonexistent_behavior() -> None:
    """Test removing behavior that doesn't exist."""
    component = SteeringComponent()
    behavior = SeekBehavior()

    component.remove_behavior(behavior=behavior)

    assert len(component.behaviors) == 0


def test_steering_component_remove_specific_behavior() -> None:
    """Test removing specific behavior from multiple."""
    component = SteeringComponent()
    seek = SeekBehavior()
    flee = FleeBehavior()
    component.add_behavior(behavior=seek, weight=1.0)
    component.add_behavior(behavior=flee, weight=0.5)

    component.remove_behavior(behavior=seek)

    assert len(component.behaviors) == 1
    assert component.behaviors[0] == flee
    assert component.weights[0] == 0.5


def test_steering_system_creation() -> None:
    """Test creating SteeringSystem."""
    system = SteeringSystem()

    assert system._spatial_grid is None
    assert system.priority == 300


def test_steering_system_with_spatial_grid() -> None:
    """Test creating SteeringSystem with spatial grid."""
    spatial_grid = MagicMock()
    system = SteeringSystem(spatial_grid=spatial_grid)

    assert system._spatial_grid == spatial_grid


def test_steering_system_update() -> None:
    """Test SteeringSystem update method."""
    world = ECSWorld()
    system = SteeringSystem()

    system.update(world=world, delta_time=0.016)


def test_avoidance_behavior_strength_scaling() -> None:
    """Test AvoidanceBehavior scales strength by distance."""
    behavior = AvoidanceBehavior(avoidance_radius=10.0)
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity_far = EntityID(fake.uuid4())

    context_multiple_close = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=20.0,
        entities_nearby=[
            (entity1, Vector2(x=2.0, y=0.0)),
            (entity2, Vector2(x=0.0, y=2.0)),
        ],
    )

    context_single_far = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=20.0,
        entities_nearby=[(entity_far, Vector2(x=8.0, y=0.0))],
    )

    force_multiple_close = behavior.calculate(context=context_multiple_close)
    force_single_far = behavior.calculate(context=context_single_far)

    assert force_multiple_close.magnitude() >= force_single_far.magnitude()


def test_flocking_behavior_force_clamping() -> None:
    """Test FlockingBehavior clamps combined force to max_force."""
    behavior = FlockingBehavior(
        separation_weight=0.0,
        alignment_weight=0.0,
        cohesion_weight=5.0,
        neighbor_radius=20.0,
    )
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    context = SteeringContext(
        position=Vector2(x=0.0, y=0.0),
        velocity=Vector2(x=0.0, y=0.0),
        max_speed=10.0,
        max_force=0.1,
        entities_nearby=[
            (entity1, Vector2(x=10.0, y=0.0)),
            (entity2, Vector2(x=0.0, y=10.0)),
        ],
    )

    force = behavior.calculate(context=context)

    assert force.magnitude() <= context.max_force
    assert 0.09 <= force.magnitude() <= 0.11

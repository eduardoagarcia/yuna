"""Tests for perception system."""

import math
from typing import cast
from unittest.mock import MagicMock

from faker import Faker

from yuna.ai.events import EntityLost, EntityPerceived
from yuna.ai.perception import (
    HearingRadius,
    Perceivable,
    PerceivedEntities,
    PerceptionSystem,
    VisionCone,
)
from yuna.ecs.world import ECSWorld
from yuna.events.bus import EventBus
from yuna.spatial.integration import Position
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

fake = Faker()


def test_vision_cone_creation() -> None:
    """Test creating VisionCone with defaults."""
    vision = VisionCone(range=10.0)

    assert vision.range == 10.0
    assert vision.fov_angle == 1.57
    assert vision.direction == 0.0
    assert vision.update_interval == 5


def test_vision_cone_with_custom_values() -> None:
    """Test creating VisionCone with custom values."""
    vision = VisionCone(
        range=20.0,
        fov_angle=3.14,
        direction=1.57,
        update_interval=10,
    )

    assert vision.range == 20.0
    assert vision.fov_angle == 3.14
    assert vision.direction == 1.57
    assert vision.update_interval == 10


def test_hearing_radius_creation() -> None:
    """Test creating HearingRadius with defaults."""
    hearing = HearingRadius(range=15.0)

    assert hearing.range == 15.0
    assert hearing.update_interval == 10


def test_hearing_radius_with_custom_interval() -> None:
    """Test creating HearingRadius with custom update interval."""
    hearing = HearingRadius(range=20.0, update_interval=5)

    assert hearing.range == 20.0
    assert hearing.update_interval == 5


def test_perceived_entities_creation() -> None:
    """Test creating PerceivedEntities with defaults."""
    perceived = PerceivedEntities()

    assert perceived.visible == set()
    assert perceived.audible == set()
    assert perceived.last_update_tick == 0
    assert perceived.history == {}


def test_perceived_entities_add_visible() -> None:
    """Test adding entity to visible set."""
    perceived = PerceivedEntities()
    entity_id = EntityID(fake.uuid4())

    was_new = perceived.add_visible(entity_id=entity_id)

    assert was_new is True
    assert entity_id in perceived.visible


def test_perceived_entities_add_visible_already_present() -> None:
    """Test adding entity that's already visible."""
    perceived = PerceivedEntities()
    entity_id = EntityID(fake.uuid4())

    perceived.add_visible(entity_id=entity_id)
    was_new = perceived.add_visible(entity_id=entity_id)

    assert was_new is False
    assert entity_id in perceived.visible


def test_perceived_entities_remove_visible() -> None:
    """Test removing entity from visible set."""
    perceived = PerceivedEntities()
    entity_id = EntityID(fake.uuid4())

    perceived.add_visible(entity_id=entity_id)
    was_visible = perceived.remove_visible(entity_id=entity_id)

    assert was_visible is True
    assert entity_id not in perceived.visible


def test_perceived_entities_remove_visible_not_present() -> None:
    """Test removing entity that wasn't visible."""
    perceived = PerceivedEntities()
    entity_id = EntityID(fake.uuid4())

    was_visible = perceived.remove_visible(entity_id=entity_id)

    assert was_visible is False


def test_perceived_entities_add_audible() -> None:
    """Test adding entity to audible set."""
    perceived = PerceivedEntities()
    entity_id = EntityID(fake.uuid4())

    was_new = perceived.add_audible(entity_id=entity_id)

    assert was_new is True
    assert entity_id in perceived.audible


def test_perceived_entities_add_audible_already_present() -> None:
    """Test adding entity that's already audible."""
    perceived = PerceivedEntities()
    entity_id = EntityID(fake.uuid4())

    perceived.add_audible(entity_id=entity_id)
    was_new = perceived.add_audible(entity_id=entity_id)

    assert was_new is False
    assert entity_id in perceived.audible


def test_perceived_entities_remove_audible() -> None:
    """Test removing entity from audible set."""
    perceived = PerceivedEntities()
    entity_id = EntityID(fake.uuid4())

    perceived.add_audible(entity_id=entity_id)
    was_audible = perceived.remove_audible(entity_id=entity_id)

    assert was_audible is True
    assert entity_id not in perceived.audible


def test_perceived_entities_remove_audible_not_present() -> None:
    """Test removing entity that wasn't audible."""
    perceived = PerceivedEntities()
    entity_id = EntityID(fake.uuid4())

    was_audible = perceived.remove_audible(entity_id=entity_id)

    assert was_audible is False


def test_perceived_entities_update_history() -> None:
    """Test updating perception history."""
    perceived = PerceivedEntities()
    entity_id = EntityID(fake.uuid4())
    position = Vector2(x=10.0, y=20.0)

    perceived.update_history(entity_id=entity_id, position=position)

    assert perceived.history[entity_id] == position


def test_perceived_entities_update_history_overwrites() -> None:
    """Test updating history overwrites previous position."""
    perceived = PerceivedEntities()
    entity_id = EntityID(fake.uuid4())
    old_position = Vector2(x=10.0, y=20.0)
    new_position = Vector2(x=30.0, y=40.0)

    perceived.update_history(entity_id=entity_id, position=old_position)
    perceived.update_history(entity_id=entity_id, position=new_position)

    assert perceived.history[entity_id] == new_position


def test_perceivable_creation() -> None:
    """Test creating Perceivable with defaults."""
    perceivable = Perceivable()

    assert perceivable.visible is True
    assert perceivable.audible is False
    assert perceivable.sight_priority == 0
    assert perceivable.sound_priority == 0


def test_perceivable_with_custom_values() -> None:
    """Test creating Perceivable with custom values."""
    perceivable = Perceivable(
        visible=False,
        audible=True,
        sight_priority=10,
        sound_priority=5,
    )

    assert perceivable.visible is False
    assert perceivable.audible is True
    assert perceivable.sight_priority == 10
    assert perceivable.sound_priority == 5


def test_perception_system_creation() -> None:
    """Test creating PerceptionSystem."""
    spatial_grid = MagicMock()
    event_bus = MagicMock()

    system = PerceptionSystem(spatial_grid=spatial_grid, event_bus=event_bus)

    assert system._spatial_grid == spatial_grid
    assert system._event_bus == event_bus
    assert system._current_tick == 0


def test_perception_system_priority() -> None:
    """Test PerceptionSystem priority."""
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    assert system.priority == 100


def test_perception_system_update_increments_tick() -> None:
    """Test update increments current tick."""
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)
    world = ECSWorld()

    system.update(world=world, delta_time=0.016)

    assert system._current_tick == 1


def test_is_in_vision_cone_directly_ahead() -> None:
    """Test vision cone with target directly ahead."""
    observer_pos = Vector2(x=0.0, y=0.0)
    observer_direction = 0.0
    fov_angle = math.pi / 2
    target_pos = Vector2(x=10.0, y=0.0)
    max_range = 15.0

    result = PerceptionSystem._is_in_vision_cone(
        observer_pos=observer_pos,
        observer_direction=observer_direction,
        fov_angle=fov_angle,
        target_pos=target_pos,
        max_range=max_range,
    )

    assert result is True


def test_is_in_vision_cone_within_fov() -> None:
    """Test vision cone with target within FOV."""
    observer_pos = Vector2(x=0.0, y=0.0)
    observer_direction = 0.0
    fov_angle = math.pi / 2
    target_pos = Vector2(x=10.0, y=5.0)
    max_range = 15.0

    result = PerceptionSystem._is_in_vision_cone(
        observer_pos=observer_pos,
        observer_direction=observer_direction,
        fov_angle=fov_angle,
        target_pos=target_pos,
        max_range=max_range,
    )

    assert result is True


def test_is_in_vision_cone_outside_fov() -> None:
    """Test vision cone with target outside FOV."""
    observer_pos = Vector2(x=0.0, y=0.0)
    observer_direction = 0.0
    fov_angle = math.pi / 4
    target_pos = Vector2(x=5.0, y=10.0)
    max_range = 15.0

    result = PerceptionSystem._is_in_vision_cone(
        observer_pos=observer_pos,
        observer_direction=observer_direction,
        fov_angle=fov_angle,
        target_pos=target_pos,
        max_range=max_range,
    )

    assert result is False


def test_is_in_vision_cone_behind() -> None:
    """Test vision cone with target behind observer."""
    observer_pos = Vector2(x=0.0, y=0.0)
    observer_direction = 0.0
    fov_angle = math.pi / 2
    target_pos = Vector2(x=-10.0, y=0.0)
    max_range = 15.0

    result = PerceptionSystem._is_in_vision_cone(
        observer_pos=observer_pos,
        observer_direction=observer_direction,
        fov_angle=fov_angle,
        target_pos=target_pos,
        max_range=max_range,
    )

    assert result is False


def test_is_in_vision_cone_out_of_range() -> None:
    """Test vision cone with target beyond max range."""
    observer_pos = Vector2(x=0.0, y=0.0)
    observer_direction = 0.0
    fov_angle = math.pi
    target_pos = Vector2(x=20.0, y=0.0)
    max_range = 10.0

    result = PerceptionSystem._is_in_vision_cone(
        observer_pos=observer_pos,
        observer_direction=observer_direction,
        fov_angle=fov_angle,
        target_pos=target_pos,
        max_range=max_range,
    )

    assert result is False


def test_is_in_vision_cone_at_same_position() -> None:
    """Test vision cone with target at same position as observer."""
    observer_pos = Vector2(x=0.0, y=0.0)
    observer_direction = 0.0
    fov_angle = math.pi
    target_pos = Vector2(x=0.0, y=0.0)
    max_range = 10.0

    result = PerceptionSystem._is_in_vision_cone(
        observer_pos=observer_pos,
        observer_direction=observer_direction,
        fov_angle=fov_angle,
        target_pos=target_pos,
        max_range=max_range,
    )

    assert result is False


def test_is_in_vision_cone_360_degree_fov() -> None:
    """Test vision cone with 360-degree FOV sees all directions."""
    observer_pos = Vector2(x=0.0, y=0.0)
    observer_direction = 0.0
    fov_angle = 2 * math.pi
    target_pos = Vector2(x=-5.0, y=-5.0)
    max_range = 10.0

    result = PerceptionSystem._is_in_vision_cone(
        observer_pos=observer_pos,
        observer_direction=observer_direction,
        fov_angle=fov_angle,
        target_pos=target_pos,
        max_range=max_range,
    )

    assert result is True


def test_is_in_vision_cone_different_direction() -> None:
    """Test vision cone looking north."""
    observer_pos = Vector2(x=0.0, y=0.0)
    observer_direction = math.pi / 2
    fov_angle = math.pi / 2
    target_pos = Vector2(x=0.0, y=10.0)
    max_range = 15.0

    result = PerceptionSystem._is_in_vision_cone(
        observer_pos=observer_pos,
        observer_direction=observer_direction,
        fov_angle=fov_angle,
        target_pos=target_pos,
        max_range=max_range,
    )

    assert result is True


def test_vision_update_detects_visible_entity() -> None:
    """Test vision update detects entity in vision cone."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    event_bus = EventBus()
    system = PerceptionSystem(spatial_grid=spatial_grid, event_bus=event_bus)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=VisionCone(range=20.0, fov_angle=math.pi, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(visible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=10.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id in perceived.visible
    assert perceived.last_update_tick == 1


def test_vision_update_ignores_self() -> None:
    """Test vision update ignores observer itself."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    observer_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=VisionCone(range=20.0, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )
    world.add_component(
        entity_id=observer_id,
        component=Perceivable(visible=True),
    )

    spatial_grid.get_in_radius.return_value = {observer_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert observer_id not in perceived.visible


def test_vision_update_respects_perceivable() -> None:
    """Test vision update only detects perceivable entities."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=VisionCone(range=20.0, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=10.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id not in perceived.visible


def test_vision_update_respects_visible_flag() -> None:
    """Test vision update respects Perceivable visible flag."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=VisionCone(range=20.0, fov_angle=math.pi, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(visible=False),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=10.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id not in perceived.visible


def test_vision_update_checks_fov() -> None:
    """Test vision update only detects entities within FOV."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=VisionCone(
            range=20.0, fov_angle=math.pi / 4, direction=0.0, update_interval=1
        ),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(visible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=0.0, y=10.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id not in perceived.visible


def test_vision_update_updates_history() -> None:
    """Test vision update adds perceived entity to history."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    target_position = Vector2(x=10.0, y=5.0)

    world.add_component(
        entity_id=observer_id,
        component=VisionCone(range=20.0, fov_angle=math.pi, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(visible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=target_position),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert perceived.history[target_id] == target_position


def test_vision_update_respects_update_interval() -> None:
    """Test vision update only runs at specified interval."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=VisionCone(range=20.0, fov_angle=math.pi, update_interval=5),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(visible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=10.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id not in perceived.visible

    for _ in range(4):
        system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id in perceived.visible


def test_vision_update_emits_perceived_event() -> None:
    """Test vision update emits EntityPerceived event."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    event_bus = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid, event_bus=event_bus)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    target_position = Vector2(x=10.0, y=0.0)

    world.add_component(
        entity_id=observer_id,
        component=VisionCone(range=20.0, fov_angle=math.pi, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(visible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=target_position),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    event_bus.emit.assert_called_once()
    emitted_event = event_bus.emit.call_args.kwargs["event"]

    assert isinstance(emitted_event, EntityPerceived)
    assert emitted_event.perceiver == observer_id
    assert emitted_event.perceived == target_id
    assert emitted_event.perception_type == "vision"
    assert emitted_event.position == target_position


def test_vision_update_does_not_emit_event_for_already_visible() -> None:
    """Test vision update doesn't emit event if entity already visible."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    event_bus = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid, event_bus=event_bus)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=VisionCone(range=20.0, fov_angle=math.pi, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(visible={target_id}),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(visible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=10.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    event_bus.emit.assert_not_called()


def test_vision_update_emits_lost_event() -> None:
    """Test vision update emits EntityLost event when entity leaves FOV."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    event_bus = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid, event_bus=event_bus)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    last_known_position = Vector2(x=10.0, y=0.0)

    world.add_component(
        entity_id=observer_id,
        component=VisionCone(range=20.0, fov_angle=math.pi, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(
            visible={target_id},
            history={target_id: last_known_position},
        ),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = set()

    system.update(world=world, delta_time=0.016)

    event_bus.emit.assert_called_once()
    emitted_event = event_bus.emit.call_args.kwargs["event"]

    assert isinstance(emitted_event, EntityLost)
    assert emitted_event.perceiver == observer_id
    assert emitted_event.lost == target_id
    assert emitted_event.perception_type == "vision"
    assert emitted_event.last_known_position == last_known_position


def test_hearing_update_detects_audible_entity() -> None:
    """Test hearing update detects entity within hearing range."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=HearingRadius(range=15.0, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(audible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=10.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id in perceived.audible


def test_hearing_update_ignores_self() -> None:
    """Test hearing update ignores observer itself."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    observer_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=HearingRadius(range=15.0, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )
    world.add_component(
        entity_id=observer_id,
        component=Perceivable(audible=True),
    )

    spatial_grid.get_in_radius.return_value = {observer_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert observer_id not in perceived.audible


def test_hearing_update_respects_perceivable() -> None:
    """Test hearing update only detects perceivable entities."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=HearingRadius(range=15.0, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=10.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id not in perceived.audible


def test_hearing_update_respects_audible_flag() -> None:
    """Test hearing update respects Perceivable audible flag."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=HearingRadius(range=15.0, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(audible=False),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=10.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id not in perceived.audible


def test_hearing_update_checks_range() -> None:
    """Test hearing update only detects entities within range."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=HearingRadius(range=5.0, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(audible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=10.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id not in perceived.audible


def test_hearing_update_updates_history() -> None:
    """Test hearing update adds perceived entity to history."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    target_position = Vector2(x=10.0, y=5.0)

    world.add_component(
        entity_id=observer_id,
        component=HearingRadius(range=15.0, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(audible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=target_position),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert perceived.history[target_id] == target_position


def test_hearing_update_respects_update_interval() -> None:
    """Test hearing update only runs at specified interval."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=HearingRadius(range=15.0, update_interval=10),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(audible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=10.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id not in perceived.audible

    for _ in range(9):
        system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id in perceived.audible


def test_hearing_update_emits_perceived_event() -> None:
    """Test hearing update emits EntityPerceived event."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    event_bus = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid, event_bus=event_bus)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    target_position = Vector2(x=10.0, y=0.0)

    world.add_component(
        entity_id=observer_id,
        component=HearingRadius(range=15.0, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(audible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=target_position),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    event_bus.emit.assert_called_once()
    emitted_event = event_bus.emit.call_args.kwargs["event"]

    assert isinstance(emitted_event, EntityPerceived)
    assert emitted_event.perceiver == observer_id
    assert emitted_event.perceived == target_id
    assert emitted_event.perception_type == "hearing"
    assert emitted_event.position == target_position


def test_hearing_update_does_not_emit_event_for_already_audible() -> None:
    """Test hearing update doesn't emit event if entity already audible."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    event_bus = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid, event_bus=event_bus)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=HearingRadius(range=15.0, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(audible={target_id}),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(audible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=10.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    event_bus.emit.assert_not_called()


def test_hearing_update_emits_lost_event() -> None:
    """Test hearing update emits EntityLost event when entity leaves range."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    event_bus = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid, event_bus=event_bus)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    last_known_position = Vector2(x=10.0, y=0.0)

    world.add_component(
        entity_id=observer_id,
        component=HearingRadius(range=15.0, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(
            audible={target_id},
            history={target_id: last_known_position},
        ),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = set()

    system.update(world=world, delta_time=0.016)

    event_bus.emit.assert_called_once()
    emitted_event = event_bus.emit.call_args.kwargs["event"]

    assert isinstance(emitted_event, EntityLost)
    assert emitted_event.perceiver == observer_id
    assert emitted_event.lost == target_id
    assert emitted_event.perception_type == "hearing"
    assert emitted_event.last_known_position == last_known_position


def test_perception_system_without_event_bus() -> None:
    """Test PerceptionSystem works without event bus."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    system = PerceptionSystem(spatial_grid=spatial_grid, event_bus=None)

    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=VisionCone(range=20.0, fov_angle=math.pi, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )

    world.add_component(
        entity_id=target_id,
        component=Perceivable(visible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=10.0, y=0.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id in perceived.visible


def test_vision_system_skips_target_without_position() -> None:
    """Test vision system skips targets without Position component."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    event_bus = EventBus()
    system = PerceptionSystem(spatial_grid=spatial_grid, event_bus=event_bus)
    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=VisionCone(
            range=10.0, fov_angle=math.pi, direction=0.0, update_interval=1
        ),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )
    world.add_component(
        entity_id=target_id,
        component=Perceivable(visible=True),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id not in perceived.visible


def test_hearing_system_skips_target_without_position() -> None:
    """Test hearing system skips targets without Position component."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    event_bus = EventBus()
    system = PerceptionSystem(spatial_grid=spatial_grid, event_bus=event_bus)
    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=HearingRadius(range=10.0, update_interval=1),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )
    world.add_component(
        entity_id=target_id,
        component=Perceivable(audible=True),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id not in perceived.audible


def test_vision_cone_angle_wrapping_around_zero() -> None:
    """Test vision cone angle normalization when wrapping around 0/2π."""
    world = ECSWorld()
    spatial_grid = MagicMock()
    event_bus = EventBus()
    system = PerceptionSystem(spatial_grid=spatial_grid, event_bus=event_bus)
    observer_id = world.create_entity()
    target_id = world.create_entity()

    world.add_component(
        entity_id=observer_id,
        component=VisionCone(
            range=10.0,
            fov_angle=math.pi,
            direction=math.pi * 1.95,
            update_interval=1,
        ),
    )
    world.add_component(
        entity_id=observer_id,
        component=PerceivedEntities(),
    )
    world.add_component(
        entity_id=observer_id,
        component=Position(position=Vector2(x=0.0, y=0.0)),
    )
    world.add_component(
        entity_id=target_id,
        component=Perceivable(visible=True),
    )
    world.add_component(
        entity_id=target_id,
        component=Position(position=Vector2(x=1.0, y=1.0)),
    )

    spatial_grid.get_in_radius.return_value = {target_id}

    system.update(world=world, delta_time=0.016)

    perceived = cast(
        PerceivedEntities,
        world.get_component(
            entity_id=observer_id,
            component_type=PerceivedEntities,
        ),
    )

    assert target_id in perceived.visible

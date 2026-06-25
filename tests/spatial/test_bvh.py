"""Tests for BoundingVolumeHierarchy spatial index implementation."""

from faker import Faker

from yuna.spatial.bvh import AABB, BoundingVolumeHierarchy
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

fake = Faker()


def test_aabb_from_point() -> None:
    """Test AABB.from_point method."""
    position = Vector2(x=100.0, y=200.0)
    aabb = AABB.from_point(position=position, padding=1.0)

    assert aabb.min_x == 99.0
    assert aabb.min_y == 199.0
    assert aabb.max_x == 101.0
    assert aabb.max_y == 201.0


def test_aabb_merge() -> None:
    """Test AABB.merge method."""
    aabb1 = AABB(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)
    aabb2 = AABB(min_x=50.0, min_y=50.0, max_x=150.0, max_y=150.0)

    merged = AABB.merge(a=aabb1, b=aabb2)

    assert merged.min_x == 0.0
    assert merged.min_y == 0.0
    assert merged.max_x == 150.0
    assert merged.max_y == 150.0


def test_aabb_contains_point() -> None:
    """Test AABB.contains_point method."""
    aabb = AABB(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)

    assert aabb.contains_point(position=Vector2(x=50.0, y=50.0))
    assert aabb.contains_point(position=Vector2(x=0.0, y=0.0))
    assert aabb.contains_point(position=Vector2(x=100.0, y=100.0))
    assert not aabb.contains_point(position=Vector2(x=-1.0, y=50.0))
    assert not aabb.contains_point(position=Vector2(x=101.0, y=50.0))


def test_aabb_intersects_circle() -> None:
    """Test AABB.intersects_circle method."""
    aabb = AABB(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)

    assert aabb.intersects_circle(center=Vector2(x=50.0, y=50.0), radius=10.0)
    assert aabb.intersects_circle(center=Vector2(x=0.0, y=0.0), radius=1.0)
    assert aabb.intersects_circle(center=Vector2(x=105.0, y=50.0), radius=10.0)
    assert not aabb.intersects_circle(center=Vector2(x=200.0, y=200.0), radius=50.0)


def test_aabb_intersects_aabb() -> None:
    """Test AABB.intersects_aabb method."""
    aabb1 = AABB(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)
    aabb2 = AABB(min_x=50.0, min_y=50.0, max_x=150.0, max_y=150.0)
    aabb3 = AABB(min_x=200.0, min_y=200.0, max_x=300.0, max_y=300.0)

    assert aabb1.intersects_aabb(other=aabb2)
    assert aabb2.intersects_aabb(other=aabb1)
    assert not aabb1.intersects_aabb(other=aabb3)
    assert not aabb3.intersects_aabb(other=aabb1)


def test_aabb_surface_area() -> None:
    """Test AABB.surface_area method."""
    aabb = AABB(min_x=0.0, min_y=0.0, max_x=100.0, max_y=50.0)
    area = aabb.surface_area()

    assert area == 300.0


def test_bvh_creation() -> None:
    """Test BVH can be created."""
    bvh = BoundingVolumeHierarchy()
    assert bvh is not None


def test_bvh_add_single_entity() -> None:
    """Test adding single entity to BVH."""
    bvh = BoundingVolumeHierarchy()
    entity_id = EntityID(fake.uuid4())
    position = Vector2(x=500.0, y=500.0)

    bvh.add(entity_id=entity_id, position=position)

    result = bvh.get_at(position=position)
    assert entity_id in result


def test_bvh_add_multiple_entities() -> None:
    """Test adding multiple entities to BVH."""
    bvh = BoundingVolumeHierarchy()

    entities = [
        (EntityID(fake.uuid4()), Vector2(x=100.0, y=100.0)),
        (EntityID(fake.uuid4()), Vector2(x=200.0, y=200.0)),
        (EntityID(fake.uuid4()), Vector2(x=300.0, y=300.0)),
    ]

    for entity_id, position in entities:
        bvh.add(entity_id=entity_id, position=position)

    for entity_id, position in entities:
        result = bvh.get_at(position=position)
        assert entity_id in result


def test_bvh_remove_entity() -> None:
    """Test removing entity from BVH."""
    bvh = BoundingVolumeHierarchy()
    entity_id = EntityID(fake.uuid4())
    position = Vector2(x=500.0, y=500.0)

    bvh.add(entity_id=entity_id, position=position)
    bvh.remove(entity_id=entity_id)

    result = bvh.get_at(position=position)
    assert entity_id not in result


def test_bvh_move_entity() -> None:
    """Test moving entity in BVH."""
    bvh = BoundingVolumeHierarchy()
    entity_id = EntityID(fake.uuid4())
    old_position = Vector2(x=100.0, y=100.0)
    new_position = Vector2(x=900.0, y=900.0)

    bvh.add(entity_id=entity_id, position=old_position)
    bvh.move(entity_id=entity_id, new_position=new_position)

    assert entity_id not in bvh.get_at(position=old_position)
    assert entity_id in bvh.get_at(position=new_position)


def test_bvh_get_in_radius() -> None:
    """Test radius query in BVH."""
    bvh = BoundingVolumeHierarchy()

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    bvh.add(entity_id=entity1, position=Vector2(x=500.0, y=500.0))
    bvh.add(entity_id=entity2, position=Vector2(x=505.0, y=505.0))
    bvh.add(entity_id=entity3, position=Vector2(x=600.0, y=600.0))

    result = bvh.get_in_radius(position=Vector2(x=500.0, y=500.0), radius=10.0)

    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result


def test_bvh_get_in_bounds() -> None:
    """Test rectangular bounds query in BVH."""
    bvh = BoundingVolumeHierarchy()

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    bvh.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    bvh.add(entity_id=entity2, position=Vector2(x=150.0, y=150.0))
    bvh.add(entity_id=entity3, position=Vector2(x=300.0, y=300.0))

    result = bvh.get_in_bounds(
        min_pos=Vector2(x=50.0, y=50.0),
        max_pos=Vector2(x=200.0, y=200.0),
    )

    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result


def test_bvh_raycast() -> None:
    """Test raycast query in BVH."""
    bvh = BoundingVolumeHierarchy()

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    bvh.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    bvh.add(entity_id=entity2, position=Vector2(x=200.0, y=200.0))
    bvh.add(entity_id=entity3, position=Vector2(x=500.0, y=100.0))

    result = bvh.raycast(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=500.0,
    )

    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result


def test_bvh_get_nearest() -> None:
    """Test k-nearest neighbors query in BVH."""
    bvh = BoundingVolumeHierarchy()

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())
    entity4 = EntityID(fake.uuid4())

    bvh.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    bvh.add(entity_id=entity2, position=Vector2(x=105.0, y=105.0))
    bvh.add(entity_id=entity3, position=Vector2(x=200.0, y=200.0))
    bvh.add(entity_id=entity4, position=Vector2(x=500.0, y=500.0))

    result = bvh.get_nearest(position=Vector2(x=100.0, y=100.0), count=2)

    assert len(result) == 2
    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result
    assert entity4 not in result


def test_bvh_empty_queries() -> None:
    """Test queries on empty BVH."""
    bvh = BoundingVolumeHierarchy()

    assert bvh.get_at(position=Vector2(x=500.0, y=500.0)) == set()
    assert bvh.get_in_radius(position=Vector2(x=500.0, y=500.0), radius=10.0) == set()
    assert (
        bvh.get_in_bounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        )
        == set()
    )
    assert (
        bvh.raycast(
            origin=Vector2(x=0.0, y=0.0),
            direction=Vector2(x=1.0, y=0.0),
            max_distance=100.0,
        )
        == []
    )
    assert bvh.get_nearest(position=Vector2(x=500.0, y=500.0), count=5) == []


def test_bvh_rebuilds_on_query() -> None:
    """Test BVH rebuilds tree when needed."""
    bvh = BoundingVolumeHierarchy()

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    bvh.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    bvh.add(entity_id=entity2, position=Vector2(x=200.0, y=200.0))

    result = bvh.get_at(position=Vector2(x=100.0, y=100.0))
    assert entity1 in result

    bvh.move(entity_id=entity1, new_position=Vector2(x=300.0, y=300.0))

    result = bvh.get_at(position=Vector2(x=300.0, y=300.0))
    assert entity1 in result


def test_bvh_remove_nonexistent_entity() -> None:
    """Test removing entity that doesn't exist."""
    bvh = BoundingVolumeHierarchy()
    entity_id = EntityID(fake.uuid4())

    bvh.remove(entity_id=entity_id)


def test_bvh_build_tree_with_single_entity() -> None:
    """Test building tree with single entity."""
    bvh = BoundingVolumeHierarchy()
    entity_id = EntityID(fake.uuid4())

    bvh.add(entity_id=entity_id, position=Vector2(x=100.0, y=100.0))

    result = bvh.get_at(position=Vector2(x=100.0, y=100.0))
    assert entity_id in result


def test_bvh_build_tree_splits_by_width() -> None:
    """Test tree splits by width when wider than tall."""
    bvh = BoundingVolumeHierarchy()

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    bvh.add(entity_id=entity1, position=Vector2(x=0.0, y=50.0))
    bvh.add(entity_id=entity2, position=Vector2(x=1000.0, y=50.0))

    result = bvh.get_at(position=Vector2(x=0.0, y=50.0))
    assert entity1 in result


def test_bvh_build_tree_splits_by_height() -> None:
    """Test tree splits by height when taller than wide."""
    bvh = BoundingVolumeHierarchy()

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    bvh.add(entity_id=entity1, position=Vector2(x=50.0, y=0.0))
    bvh.add(entity_id=entity2, position=Vector2(x=50.0, y=1000.0))

    result = bvh.get_at(position=Vector2(x=50.0, y=0.0))
    assert entity1 in result


def test_bvh_raycast_ordering() -> None:
    """Test raycast returns entities in distance order."""
    bvh = BoundingVolumeHierarchy()

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    bvh.add(entity_id=entity1, position=Vector2(x=300.0, y=300.0))
    bvh.add(entity_id=entity2, position=Vector2(x=100.0, y=100.0))
    bvh.add(entity_id=entity3, position=Vector2(x=200.0, y=200.0))

    result = bvh.raycast(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=500.0,
    )

    assert result[0] == entity2
    assert result[1] == entity3
    assert result[2] == entity1


def test_bvh_get_nearest_ordering() -> None:
    """Test get_nearest returns entities in distance order."""
    bvh = BoundingVolumeHierarchy()

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    bvh.add(entity_id=entity1, position=Vector2(x=300.0, y=300.0))
    bvh.add(entity_id=entity2, position=Vector2(x=105.0, y=105.0))
    bvh.add(entity_id=entity3, position=Vector2(x=110.0, y=110.0))

    result = bvh.get_nearest(position=Vector2(x=100.0, y=100.0), count=3)

    assert result[0] == entity2
    assert result[1] == entity3
    assert result[2] == entity1


def test_bvh_multiple_rebuilds() -> None:
    """Test BVH handles multiple rebuild cycles."""
    bvh = BoundingVolumeHierarchy()

    entity1 = EntityID(fake.uuid4())

    bvh.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    bvh.get_at(position=Vector2(x=100.0, y=100.0))

    bvh.move(entity_id=entity1, new_position=Vector2(x=200.0, y=200.0))
    bvh.get_at(position=Vector2(x=200.0, y=200.0))

    bvh.move(entity_id=entity1, new_position=Vector2(x=300.0, y=300.0))
    result = bvh.get_at(position=Vector2(x=300.0, y=300.0))

    assert entity1 in result


def test_bvh_remove_before_rebuild() -> None:
    """Test removing entity before tree is built."""
    bvh = BoundingVolumeHierarchy()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    bvh.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    bvh.add(entity_id=entity2, position=Vector2(x=200.0, y=200.0))

    bvh.remove(entity_id=entity1)

    result = bvh.get_at(position=Vector2(x=100.0, y=100.0))
    assert entity1 not in result


def test_bvh_query_near_but_not_at_position() -> None:
    """Test querying position near but not exactly at entity."""
    bvh = BoundingVolumeHierarchy()
    entity_id = EntityID(fake.uuid4())

    bvh.add(entity_id=entity_id, position=Vector2(x=100.0, y=100.0))

    result = bvh.get_at(position=Vector2(x=100.1, y=100.1))
    assert entity_id not in result


def test_bvh_query_near_but_not_in_radius() -> None:
    """Test querying just outside radius."""
    bvh = BoundingVolumeHierarchy()
    entity_id = EntityID(fake.uuid4())

    bvh.add(entity_id=entity_id, position=Vector2(x=100.0, y=100.0))

    result = bvh.get_in_radius(position=Vector2(x=100.0, y=100.0), radius=0.5)
    assert entity_id in result

    result = bvh.get_in_radius(position=Vector2(x=120.0, y=120.0), radius=10.0)
    assert entity_id not in result


def test_bvh_query_near_but_not_in_bounds() -> None:
    """Test querying just outside bounds."""
    bvh = BoundingVolumeHierarchy()
    entity_id = EntityID(fake.uuid4())

    bvh.add(entity_id=entity_id, position=Vector2(x=100.0, y=100.0))

    result = bvh.get_in_bounds(
        min_pos=Vector2(x=101.0, y=101.0),
        max_pos=Vector2(x=200.0, y=200.0),
    )
    assert entity_id not in result


def test_bvh_remove_entity_from_nodes() -> None:
    """Test removing entity that was previously queried and is in nodes."""
    bvh = BoundingVolumeHierarchy()
    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())

    bvh.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    bvh.add(entity_id=entity2, position=Vector2(x=200.0, y=200.0))

    bvh.get_at(position=Vector2(x=100.0, y=100.0))

    bvh.remove(entity_id=entity1)

    result = bvh.get_at(position=Vector2(x=100.0, y=100.0))
    assert entity1 not in result
    assert entity2 in bvh.get_at(position=Vector2(x=200.0, y=200.0))


def test_bvh_aabb_contains_but_entity_outside_radius() -> None:
    """Test AABB intersects circle but entity is just outside radius."""
    bvh = BoundingVolumeHierarchy()
    entity_id = EntityID(fake.uuid4())

    bvh.add(entity_id=entity_id, position=Vector2(x=100.0, y=100.0))

    result = bvh.get_in_radius(position=Vector2(x=100.3, y=100.3), radius=0.1)
    assert entity_id not in result


def test_bvh_aabb_contains_but_entity_outside_bounds() -> None:
    """Test AABB intersects bounds but entity is just outside."""
    bvh = BoundingVolumeHierarchy()
    entity_id = EntityID(fake.uuid4())

    bvh.add(entity_id=entity_id, position=Vector2(x=100.0, y=100.0))

    result = bvh.get_in_bounds(
        min_pos=Vector2(x=99.6, y=99.6),
        max_pos=Vector2(x=99.9, y=99.9),
    )
    assert entity_id not in result


def test_raycast_equal_distance_resolves_by_entity_id() -> None:
    """Equal-distance BVH raycast hits resolve in canonical entity_id order.

    Regression for a determinism bug where equal-distance ties resolved via
    non-deterministic set iteration order rather than a stable entity_id key.
    """
    position = Vector2(x=100.0, y=100.0)
    forward = BoundingVolumeHierarchy()
    reverse = BoundingVolumeHierarchy()
    for entity_id in ("aaaa", "bbbb", "cccc"):
        forward.add(entity_id=EntityID(entity_id), position=position)
    for entity_id in ("cccc", "bbbb", "aaaa"):
        reverse.add(entity_id=EntityID(entity_id), position=position)

    origin = Vector2(x=0.0, y=0.0)
    direction = Vector2(x=1.0, y=1.0).normalize()
    forward_hits = forward.raycast(
        origin=origin, direction=direction, max_distance=500.0
    )
    reverse_hits = reverse.raycast(
        origin=origin, direction=direction, max_distance=500.0
    )

    assert forward_hits == reverse_hits


def test_get_nearest_equal_distance_resolves_by_entity_id() -> None:
    """Equal-distance BVH get_nearest results resolve in canonical order."""
    position = Vector2(x=50.0, y=50.0)
    forward = BoundingVolumeHierarchy()
    reverse = BoundingVolumeHierarchy()
    for entity_id in ("aaaa", "bbbb", "cccc"):
        forward.add(entity_id=EntityID(entity_id), position=position)
    for entity_id in ("cccc", "bbbb", "aaaa"):
        reverse.add(entity_id=EntityID(entity_id), position=position)

    query = Vector2(x=0.0, y=0.0)
    forward_nearest = forward.get_nearest(position=query, count=2)
    reverse_nearest = reverse.get_nearest(position=query, count=2)

    assert forward_nearest == reverse_nearest
    assert forward_nearest == [EntityID("aaaa"), EntityID("bbbb")]

"""Tests for QuadTree spatial index implementation."""

from faker import Faker

from yuna.spatial.quadtree import Bounds, QuadTree
from yuna.types.identifiers import EntityID
from yuna.types.vector import Vector2

fake = Faker()


def test_bounds_contains() -> None:
    """Test Bounds.contains method."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)
    assert bounds.contains(position=Vector2(x=50.0, y=50.0))
    assert bounds.contains(position=Vector2(x=0.0, y=0.0))
    assert bounds.contains(position=Vector2(x=100.0, y=100.0))
    assert not bounds.contains(position=Vector2(x=-1.0, y=50.0))
    assert not bounds.contains(position=Vector2(x=101.0, y=50.0))


def test_bounds_intersects_circle() -> None:
    """Test Bounds.intersects_circle method."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)
    assert bounds.intersects_circle(center=Vector2(x=50.0, y=50.0), radius=10.0)
    assert bounds.intersects_circle(center=Vector2(x=0.0, y=0.0), radius=1.0)
    assert bounds.intersects_circle(center=Vector2(x=105.0, y=50.0), radius=10.0)
    assert not bounds.intersects_circle(center=Vector2(x=200.0, y=200.0), radius=50.0)


def test_bounds_intersects_bounds() -> None:
    """Test Bounds.intersects_bounds method."""
    bounds1 = Bounds(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)
    bounds2 = Bounds(min_x=50.0, min_y=50.0, max_x=150.0, max_y=150.0)
    bounds3 = Bounds(min_x=200.0, min_y=200.0, max_x=300.0, max_y=300.0)

    assert bounds1.intersects_bounds(other=bounds2)
    assert bounds2.intersects_bounds(other=bounds1)
    assert not bounds1.intersects_bounds(other=bounds3)
    assert not bounds3.intersects_bounds(other=bounds1)


def test_quadtree_creation() -> None:
    """Test QuadTree can be created."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)
    assert tree is not None


def test_quadtree_add_single_entity() -> None:
    """Test adding single entity to quadtree."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)
    entity_id = EntityID(fake.uuid4())
    position = Vector2(x=500.0, y=500.0)

    tree.add(entity_id=entity_id, position=position)

    result = tree.get_at(position=position)
    assert entity_id in result


def test_quadtree_add_multiple_entities() -> None:
    """Test adding multiple entities to quadtree."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)

    entities = [
        (EntityID(fake.uuid4()), Vector2(x=100.0, y=100.0)),
        (EntityID(fake.uuid4()), Vector2(x=200.0, y=200.0)),
        (EntityID(fake.uuid4()), Vector2(x=300.0, y=300.0)),
    ]

    for entity_id, position in entities:
        tree.add(entity_id=entity_id, position=position)

    for entity_id, position in entities:
        result = tree.get_at(position=position)
        assert entity_id in result


def test_quadtree_subdivision() -> None:
    """Test quadtree subdivides when capacity exceeded."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds, max_objects=2, max_depth=4)

    entities = [EntityID(fake.uuid4()) for _ in range(5)]
    positions = [
        Vector2(x=100.0, y=100.0),
        Vector2(x=150.0, y=150.0),
        Vector2(x=200.0, y=200.0),
        Vector2(x=250.0, y=250.0),
        Vector2(x=300.0, y=300.0),
    ]

    for entity_id, position in zip(entities, positions, strict=False):
        tree.add(entity_id=entity_id, position=position)

    for entity_id, position in zip(entities, positions, strict=False):
        result = tree.get_at(position=position)
        assert entity_id in result


def test_quadtree_remove_entity() -> None:
    """Test removing entity from quadtree."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)
    entity_id = EntityID(fake.uuid4())
    position = Vector2(x=500.0, y=500.0)

    tree.add(entity_id=entity_id, position=position)
    tree.remove(entity_id=entity_id)

    result = tree.get_at(position=position)
    assert entity_id not in result


def test_quadtree_move_entity() -> None:
    """Test moving entity in quadtree."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)
    entity_id = EntityID(fake.uuid4())
    old_position = Vector2(x=100.0, y=100.0)
    new_position = Vector2(x=900.0, y=900.0)

    tree.add(entity_id=entity_id, position=old_position)
    tree.move(entity_id=entity_id, new_position=new_position)

    assert entity_id not in tree.get_at(position=old_position)
    assert entity_id in tree.get_at(position=new_position)


def test_quadtree_get_in_radius() -> None:
    """Test radius query in quadtree."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    tree.add(entity_id=entity1, position=Vector2(x=500.0, y=500.0))
    tree.add(entity_id=entity2, position=Vector2(x=505.0, y=505.0))
    tree.add(entity_id=entity3, position=Vector2(x=600.0, y=600.0))

    result = tree.get_in_radius(position=Vector2(x=500.0, y=500.0), radius=10.0)

    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result


def test_quadtree_get_in_bounds() -> None:
    """Test rectangular bounds query in quadtree."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    tree.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    tree.add(entity_id=entity2, position=Vector2(x=150.0, y=150.0))
    tree.add(entity_id=entity3, position=Vector2(x=300.0, y=300.0))

    result = tree.get_in_bounds(
        min_pos=Vector2(x=50.0, y=50.0),
        max_pos=Vector2(x=200.0, y=200.0),
    )

    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result


def test_quadtree_raycast() -> None:
    """Test raycast query in quadtree."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    tree.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    tree.add(entity_id=entity2, position=Vector2(x=200.0, y=200.0))
    tree.add(entity_id=entity3, position=Vector2(x=500.0, y=100.0))

    result = tree.raycast(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=500.0,
    )

    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result


def test_quadtree_get_nearest() -> None:
    """Test k-nearest neighbors query in quadtree."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())
    entity4 = EntityID(fake.uuid4())

    tree.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    tree.add(entity_id=entity2, position=Vector2(x=105.0, y=105.0))
    tree.add(entity_id=entity3, position=Vector2(x=200.0, y=200.0))
    tree.add(entity_id=entity4, position=Vector2(x=500.0, y=500.0))

    result = tree.get_nearest(position=Vector2(x=100.0, y=100.0), count=2)

    assert len(result) == 2
    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result
    assert entity4 not in result


def test_quadtree_empty_queries() -> None:
    """Test queries on empty quadtree."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)

    assert tree.get_at(position=Vector2(x=500.0, y=500.0)) == set()
    assert tree.get_in_radius(position=Vector2(x=500.0, y=500.0), radius=10.0) == set()
    assert (
        tree.get_in_bounds(
            min_pos=Vector2(x=0.0, y=0.0),
            max_pos=Vector2(x=100.0, y=100.0),
        )
        == set()
    )
    assert (
        tree.raycast(
            origin=Vector2(x=0.0, y=0.0),
            direction=Vector2(x=1.0, y=0.0),
            max_distance=100.0,
        )
        == []
    )
    assert tree.get_nearest(position=Vector2(x=500.0, y=500.0), count=5) == []


def test_quadtree_max_depth_prevents_infinite_subdivision() -> None:
    """Test max depth prevents infinite subdivision."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds, max_objects=1, max_depth=2)

    entities = [EntityID(fake.uuid4()) for _ in range(10)]

    for i, entity_id in enumerate(entities):
        position = Vector2(x=100.0 + i * 0.1, y=100.0 + i * 0.1)
        tree.add(entity_id=entity_id, position=position)

    for i, entity_id in enumerate(entities):
        position = Vector2(x=100.0 + i * 0.1, y=100.0 + i * 0.1)
        result = tree.get_at(position=position)
        assert entity_id in result


def test_quadtree_remove_nonexistent_entity() -> None:
    """Test removing entity that doesn't exist."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)
    entity_id = EntityID(fake.uuid4())

    tree.remove(entity_id=entity_id)


def test_quadtree_move_nonexistent_entity() -> None:
    """Test moving entity that doesn't exist."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)
    entity_id = EntityID(fake.uuid4())

    tree.move(entity_id=entity_id, new_position=Vector2(x=500.0, y=500.0))


def test_quadtree_entities_in_different_quadrants() -> None:
    """Test entities distributed across quadrants."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds, max_objects=2, max_depth=4)

    nw_entity = EntityID(fake.uuid4())
    ne_entity = EntityID(fake.uuid4())
    sw_entity = EntityID(fake.uuid4())
    se_entity = EntityID(fake.uuid4())

    tree.add(entity_id=nw_entity, position=Vector2(x=250.0, y=750.0))
    tree.add(entity_id=ne_entity, position=Vector2(x=750.0, y=750.0))
    tree.add(entity_id=sw_entity, position=Vector2(x=250.0, y=250.0))
    tree.add(entity_id=se_entity, position=Vector2(x=750.0, y=250.0))

    assert nw_entity in tree.get_at(position=Vector2(x=250.0, y=750.0))
    assert ne_entity in tree.get_at(position=Vector2(x=750.0, y=750.0))
    assert sw_entity in tree.get_at(position=Vector2(x=250.0, y=250.0))
    assert se_entity in tree.get_at(position=Vector2(x=750.0, y=250.0))


def test_quadtree_raycast_ordering() -> None:
    """Test raycast returns entities in distance order."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    tree.add(entity_id=entity1, position=Vector2(x=300.0, y=300.0))
    tree.add(entity_id=entity2, position=Vector2(x=100.0, y=100.0))
    tree.add(entity_id=entity3, position=Vector2(x=200.0, y=200.0))

    result = tree.raycast(
        origin=Vector2(x=0.0, y=0.0),
        direction=Vector2(x=1.0, y=1.0).normalize(),
        max_distance=500.0,
    )

    assert result[0] == entity2
    assert result[1] == entity3
    assert result[2] == entity1


def test_quadtree_get_nearest_ordering() -> None:
    """Test get_nearest returns entities in distance order."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds)

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    tree.add(entity_id=entity1, position=Vector2(x=300.0, y=300.0))
    tree.add(entity_id=entity2, position=Vector2(x=105.0, y=105.0))
    tree.add(entity_id=entity3, position=Vector2(x=110.0, y=110.0))

    result = tree.get_nearest(position=Vector2(x=100.0, y=100.0), count=3)

    assert result[0] == entity2
    assert result[1] == entity3
    assert result[2] == entity1


def test_quadtree_insert_outside_bounds() -> None:
    """Test inserting entity outside quadtree bounds returns False."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)
    tree = QuadTree(bounds=bounds)
    entity_id = EntityID(fake.uuid4())

    tree.add(entity_id=entity_id, position=Vector2(x=200.0, y=200.0))

    result = tree.get_at(position=Vector2(x=200.0, y=200.0))
    assert entity_id not in result


def test_quadtree_remove_from_subdivided_tree() -> None:
    """Test removing entity from subdivided quadtree."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds, max_objects=2, max_depth=4)

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())

    tree.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    tree.add(entity_id=entity2, position=Vector2(x=200.0, y=200.0))
    tree.add(entity_id=entity3, position=Vector2(x=800.0, y=800.0))

    tree.remove(entity_id=entity2)

    assert entity1 in tree.get_at(position=Vector2(x=100.0, y=100.0))
    assert entity2 not in tree.get_at(position=Vector2(x=200.0, y=200.0))
    assert entity3 in tree.get_at(position=Vector2(x=800.0, y=800.0))


def test_quadtree_query_outside_bounds() -> None:
    """Test querying outside quadtree bounds returns empty."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=100.0, max_y=100.0)
    tree = QuadTree(bounds=bounds)
    entity_id = EntityID(fake.uuid4())

    tree.add(entity_id=entity_id, position=Vector2(x=50.0, y=50.0))

    result = tree.get_at(position=Vector2(x=200.0, y=200.0))
    assert len(result) == 0

    result = tree.get_in_radius(position=Vector2(x=200.0, y=200.0), radius=10.0)
    assert len(result) == 0


def test_quadtree_radius_query_after_subdivision() -> None:
    """Test radius query works correctly after tree subdivision."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds, max_objects=2, max_depth=4)

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())
    entity4 = EntityID(fake.uuid4())

    tree.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    tree.add(entity_id=entity2, position=Vector2(x=105.0, y=105.0))
    tree.add(entity_id=entity3, position=Vector2(x=800.0, y=800.0))
    tree.add(entity_id=entity4, position=Vector2(x=805.0, y=805.0))

    result = tree.get_in_radius(position=Vector2(x=102.0, y=102.0), radius=10.0)

    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result
    assert entity4 not in result


def test_quadtree_bounds_query_after_subdivision() -> None:
    """Test bounds query works correctly after tree subdivision."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    tree = QuadTree(bounds=bounds, max_objects=2, max_depth=4)

    entity1 = EntityID(fake.uuid4())
    entity2 = EntityID(fake.uuid4())
    entity3 = EntityID(fake.uuid4())
    entity4 = EntityID(fake.uuid4())

    tree.add(entity_id=entity1, position=Vector2(x=100.0, y=100.0))
    tree.add(entity_id=entity2, position=Vector2(x=150.0, y=150.0))
    tree.add(entity_id=entity3, position=Vector2(x=800.0, y=800.0))
    tree.add(entity_id=entity4, position=Vector2(x=850.0, y=850.0))

    result = tree.get_in_bounds(
        min_pos=Vector2(x=50.0, y=50.0),
        max_pos=Vector2(x=200.0, y=200.0),
    )

    assert entity1 in result
    assert entity2 in result
    assert entity3 not in result
    assert entity4 not in result


def test_raycast_equal_distance_resolves_by_entity_id() -> None:
    """Equal-distance quadtree raycast hits resolve in canonical order.

    Regression for a determinism bug where equal-distance ties resolved via
    non-deterministic set iteration order rather than a stable entity_id key.
    """
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    position = Vector2(x=100.0, y=100.0)
    forward = QuadTree(bounds=bounds)
    reverse = QuadTree(bounds=bounds)
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
    """Equal-distance quadtree get_nearest results resolve in canonical order."""
    bounds = Bounds(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0)
    position = Vector2(x=50.0, y=50.0)
    forward = QuadTree(bounds=bounds)
    reverse = QuadTree(bounds=bounds)
    for entity_id in ("aaaa", "bbbb", "cccc"):
        forward.add(entity_id=EntityID(entity_id), position=position)
    for entity_id in ("cccc", "bbbb", "aaaa"):
        reverse.add(entity_id=EntityID(entity_id), position=position)

    query = Vector2(x=0.0, y=0.0)
    forward_nearest = forward.get_nearest(position=query, count=2)
    reverse_nearest = reverse.get_nearest(position=query, count=2)

    assert forward_nearest == reverse_nearest
    assert forward_nearest == [EntityID("aaaa"), EntityID("bbbb")]

"""Tests for entity hierarchy management."""

import pytest
from faker import Faker

from yuna.ecs.hierarchy import (
    CircularHierarchyError,
    HierarchyManager,
)
from yuna.types.identifiers import EntityID

fake = Faker()


def test_hierarchy_manager_creation() -> None:
    """Test HierarchyManager can be instantiated."""
    manager = HierarchyManager()
    assert manager is not None


def test_set_parent() -> None:
    """Test setting parent-child relationship."""
    manager = HierarchyManager()
    parent = EntityID(fake.uuid4())
    child = EntityID(fake.uuid4())

    manager.set_parent(child_id=child, parent_id=parent)

    assert manager.get_parent(entity_id=child) == parent
    assert child in manager.get_children(entity_id=parent)


def test_get_parent_returns_none_when_no_parent() -> None:
    """Test get_parent returns None for entity without parent."""
    manager = HierarchyManager()
    entity = EntityID(fake.uuid4())

    assert manager.get_parent(entity_id=entity) is None


def test_get_children_returns_empty_list_when_no_children() -> None:
    """Test get_children returns empty list when no children."""
    manager = HierarchyManager()
    entity = EntityID(fake.uuid4())

    assert manager.get_children(entity_id=entity) == []


def test_get_children_returns_copy() -> None:
    """Test get_children returns copy not reference."""
    manager = HierarchyManager()
    parent = EntityID(fake.uuid4())
    child = EntityID(fake.uuid4())

    manager.set_parent(child_id=child, parent_id=parent)

    children_1 = manager.get_children(entity_id=parent)
    children_2 = manager.get_children(entity_id=parent)

    assert children_1 == children_2
    assert children_1 is not children_2


def test_set_parent_replaces_old_parent() -> None:
    """Test setting new parent removes old parent relationship."""
    manager = HierarchyManager()
    old_parent = EntityID(fake.uuid4())
    new_parent = EntityID(fake.uuid4())
    child = EntityID(fake.uuid4())

    manager.set_parent(child_id=child, parent_id=old_parent)
    manager.set_parent(child_id=child, parent_id=new_parent)

    assert manager.get_parent(entity_id=child) == new_parent
    assert child not in manager.get_children(entity_id=old_parent)
    assert child in manager.get_children(entity_id=new_parent)


def test_remove_parent() -> None:
    """Test removing parent from child."""
    manager = HierarchyManager()
    parent = EntityID(fake.uuid4())
    child = EntityID(fake.uuid4())

    manager.set_parent(child_id=child, parent_id=parent)
    manager.remove_parent(child_id=child)

    assert manager.get_parent(entity_id=child) is None
    assert child not in manager.get_children(entity_id=parent)


def test_remove_parent_when_no_parent() -> None:
    """Test removing parent when entity has no parent does nothing."""
    manager = HierarchyManager()
    entity = EntityID(fake.uuid4())

    manager.remove_parent(child_id=entity)

    assert manager.get_parent(entity_id=entity) is None


def test_get_descendants_single_level() -> None:
    """Test getting descendants with single level."""
    manager = HierarchyManager()
    parent = EntityID(fake.uuid4())
    child_1 = EntityID(fake.uuid4())
    child_2 = EntityID(fake.uuid4())

    manager.set_parent(child_id=child_1, parent_id=parent)
    manager.set_parent(child_id=child_2, parent_id=parent)

    descendants = manager.get_descendants(entity_id=parent)

    assert set(descendants) == {child_1, child_2}


def test_get_descendants_multiple_levels() -> None:
    """Test getting descendants with multiple levels."""
    manager = HierarchyManager()
    root = EntityID(fake.uuid4())
    child = EntityID(fake.uuid4())
    grandchild = EntityID(fake.uuid4())

    manager.set_parent(child_id=child, parent_id=root)
    manager.set_parent(child_id=grandchild, parent_id=child)

    descendants = manager.get_descendants(entity_id=root)

    assert set(descendants) == {child, grandchild}


def test_get_descendants_empty() -> None:
    """Test getting descendants when entity has no children."""
    manager = HierarchyManager()
    entity = EntityID(fake.uuid4())

    descendants = manager.get_descendants(entity_id=entity)

    assert descendants == []


def test_get_ancestors() -> None:
    """Test getting ancestors."""
    manager = HierarchyManager()
    root = EntityID(fake.uuid4())
    middle = EntityID(fake.uuid4())
    leaf = EntityID(fake.uuid4())

    manager.set_parent(child_id=middle, parent_id=root)
    manager.set_parent(child_id=leaf, parent_id=middle)

    ancestors = manager.get_ancestors(entity_id=leaf)

    assert ancestors == [middle, root]


def test_get_ancestors_empty() -> None:
    """Test getting ancestors when entity has no parent."""
    manager = HierarchyManager()
    entity = EntityID(fake.uuid4())

    ancestors = manager.get_ancestors(entity_id=entity)

    assert ancestors == []


def test_get_root_with_no_parent() -> None:
    """Test get_root returns self when no parent."""
    manager = HierarchyManager()
    entity = EntityID(fake.uuid4())

    root = manager.get_root(entity_id=entity)

    assert root == entity


def test_get_root_with_ancestors() -> None:
    """Test get_root returns topmost ancestor."""
    manager = HierarchyManager()
    root = EntityID(fake.uuid4())
    middle = EntityID(fake.uuid4())
    leaf = EntityID(fake.uuid4())

    manager.set_parent(child_id=middle, parent_id=root)
    manager.set_parent(child_id=leaf, parent_id=middle)

    assert manager.get_root(entity_id=leaf) == root
    assert manager.get_root(entity_id=middle) == root
    assert manager.get_root(entity_id=root) == root


def test_get_entities_to_destroy() -> None:
    """Test getting entities for recursive destruction."""
    manager = HierarchyManager()
    root = EntityID(fake.uuid4())
    child_1 = EntityID(fake.uuid4())
    child_2 = EntityID(fake.uuid4())
    grandchild = EntityID(fake.uuid4())

    manager.set_parent(child_id=child_1, parent_id=root)
    manager.set_parent(child_id=child_2, parent_id=root)
    manager.set_parent(child_id=grandchild, parent_id=child_1)

    entities = manager.get_entities_to_destroy(entity_id=root)

    assert root in entities
    assert child_1 in entities
    assert child_2 in entities
    assert grandchild in entities
    assert entities.index(grandchild) < entities.index(child_1)
    assert entities.index(child_1) < entities.index(root)
    assert entities.index(child_2) < entities.index(root)


def test_remove_entity() -> None:
    """Test removing entity from hierarchy."""
    manager = HierarchyManager()
    parent = EntityID(fake.uuid4())
    child = EntityID(fake.uuid4())
    grandchild = EntityID(fake.uuid4())

    manager.set_parent(child_id=child, parent_id=parent)
    manager.set_parent(child_id=grandchild, parent_id=child)

    manager.remove_entity(entity_id=child)

    assert manager.get_parent(entity_id=child) is None
    assert child not in manager.get_children(entity_id=parent)
    assert manager.get_parent(entity_id=grandchild) is None


def test_prevent_circular_hierarchy_direct() -> None:
    """Test preventing direct circular hierarchy (entity as own parent)."""
    manager = HierarchyManager()
    entity = EntityID(fake.uuid4())

    with pytest.raises(CircularHierarchyError):
        manager.set_parent(child_id=entity, parent_id=entity)


def test_prevent_circular_hierarchy_indirect() -> None:
    """Test preventing indirect circular hierarchy."""
    manager = HierarchyManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())
    entity_c = EntityID(fake.uuid4())

    manager.set_parent(child_id=entity_b, parent_id=entity_a)
    manager.set_parent(child_id=entity_c, parent_id=entity_b)

    with pytest.raises(CircularHierarchyError):
        manager.set_parent(child_id=entity_a, parent_id=entity_c)


def test_prevent_circular_hierarchy_two_level() -> None:
    """Test preventing two-level circular hierarchy."""
    manager = HierarchyManager()
    entity_a = EntityID(fake.uuid4())
    entity_b = EntityID(fake.uuid4())

    manager.set_parent(child_id=entity_b, parent_id=entity_a)

    with pytest.raises(CircularHierarchyError):
        manager.set_parent(child_id=entity_a, parent_id=entity_b)


def test_multiple_children_same_parent() -> None:
    """Test multiple children can have same parent."""
    manager = HierarchyManager()
    parent = EntityID(fake.uuid4())
    child_1 = EntityID(fake.uuid4())
    child_2 = EntityID(fake.uuid4())
    child_3 = EntityID(fake.uuid4())

    manager.set_parent(child_id=child_1, parent_id=parent)
    manager.set_parent(child_id=child_2, parent_id=parent)
    manager.set_parent(child_id=child_3, parent_id=parent)

    children = manager.get_children(entity_id=parent)

    assert set(children) == {child_1, child_2, child_3}


def test_complex_hierarchy() -> None:
    """Test complex multi-level hierarchy."""
    manager = HierarchyManager()
    root = EntityID(fake.uuid4())
    branch_1 = EntityID(fake.uuid4())
    branch_2 = EntityID(fake.uuid4())
    leaf_1 = EntityID(fake.uuid4())
    leaf_2 = EntityID(fake.uuid4())
    leaf_3 = EntityID(fake.uuid4())

    manager.set_parent(child_id=branch_1, parent_id=root)
    manager.set_parent(child_id=branch_2, parent_id=root)
    manager.set_parent(child_id=leaf_1, parent_id=branch_1)
    manager.set_parent(child_id=leaf_2, parent_id=branch_1)
    manager.set_parent(child_id=leaf_3, parent_id=branch_2)

    assert set(manager.get_children(entity_id=root)) == {branch_1, branch_2}
    assert set(manager.get_children(entity_id=branch_1)) == {leaf_1, leaf_2}
    assert set(manager.get_children(entity_id=branch_2)) == {leaf_3}
    assert set(manager.get_descendants(entity_id=root)) == {
        branch_1,
        branch_2,
        leaf_1,
        leaf_2,
        leaf_3,
    }


def test_reparenting_entity() -> None:
    """Test moving entity to new parent updates hierarchy correctly."""
    manager = HierarchyManager()
    old_parent = EntityID(fake.uuid4())
    new_parent = EntityID(fake.uuid4())
    child = EntityID(fake.uuid4())

    manager.set_parent(child_id=child, parent_id=old_parent)
    manager.set_parent(child_id=child, parent_id=new_parent)

    assert manager.get_parent(entity_id=child) == new_parent
    assert manager.get_children(entity_id=old_parent) == []
    assert child in manager.get_children(entity_id=new_parent)


def test_get_entities_to_destroy_single_entity() -> None:
    """Test get_entities_to_destroy for entity with no descendants."""
    manager = HierarchyManager()
    entity = EntityID(fake.uuid4())

    entities = manager.get_entities_to_destroy(entity_id=entity)

    assert entities == [entity]


def test_descendants_depth_first_order() -> None:
    """Test descendants returned in depth-first order."""
    manager = HierarchyManager()
    root = EntityID(fake.uuid4())
    child_1 = EntityID(fake.uuid4())
    child_2 = EntityID(fake.uuid4())
    grandchild_1 = EntityID(fake.uuid4())

    manager.set_parent(child_id=child_1, parent_id=root)
    manager.set_parent(child_id=child_2, parent_id=root)
    manager.set_parent(child_id=grandchild_1, parent_id=child_1)

    descendants = manager.get_descendants(entity_id=root)

    assert descendants.index(child_1) < descendants.index(grandchild_1)


def test_remove_entity_cleans_up_children_list() -> None:
    """Test removing entity cleans up empty children lists."""
    manager = HierarchyManager()
    parent = EntityID(fake.uuid4())
    child = EntityID(fake.uuid4())

    manager.set_parent(child_id=child, parent_id=parent)
    manager.remove_parent(child_id=child)

    assert parent not in manager._children

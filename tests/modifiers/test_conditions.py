"""Tests for modifier condition helpers."""

from unittest.mock import Mock

from faker import Faker

from yuna.modifiers.conditions import Conditions
from yuna.modifiers.config import ModifierConfig
from yuna.modifiers.context import ModifierContext
from yuna.types.identifiers import EntityID

fake = Faker()


def test_stat_above_returns_true_when_above_threshold() -> None:
    """Test stat_above condition returns True when stat > threshold."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 75.0

    condition = Conditions.stat_above(stat_name="health", threshold=50.0)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True
    world.get_stat.assert_called_once_with(entity_id=entity_id, stat="health")


def test_stat_above_returns_false_when_below_threshold() -> None:
    """Test stat_above condition returns False when stat < threshold."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 30.0

    condition = Conditions.stat_above(stat_name="health", threshold=50.0)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_stat_above_returns_false_when_equal_to_threshold() -> None:
    """Test stat_above condition returns False when stat == threshold."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 50.0

    condition = Conditions.stat_above(stat_name="health", threshold=50.0)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_stat_above_returns_false_when_no_world() -> None:
    """Test stat_above condition returns False when world is None."""
    condition = Conditions.stat_above(stat_name="health", threshold=50.0)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=None)
    context.entity_id = EntityID(fake.uuid4())

    result = condition(context)

    assert result is False


def test_stat_below_returns_true_when_below_threshold() -> None:
    """Test stat_below condition returns True when stat < threshold."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 30.0

    condition = Conditions.stat_below(stat_name="health", threshold=50.0)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True
    world.get_stat.assert_called_once_with(entity_id=entity_id, stat="health")


def test_stat_below_returns_false_when_above_threshold() -> None:
    """Test stat_below condition returns False when stat > threshold."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 75.0

    condition = Conditions.stat_below(stat_name="health", threshold=50.0)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_stat_below_returns_false_when_equal_to_threshold() -> None:
    """Test stat_below condition returns False when stat == threshold."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 50.0

    condition = Conditions.stat_below(stat_name="health", threshold=50.0)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_stat_below_returns_false_when_no_world() -> None:
    """Test stat_below condition returns False when world is None."""
    condition = Conditions.stat_below(stat_name="health", threshold=50.0)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=None)
    context.entity_id = EntityID(fake.uuid4())

    result = condition(context)

    assert result is False


def test_has_tag_returns_true_when_entity_has_tag() -> None:
    """Test has_tag condition returns True when entity has tag."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_entity_tags.return_value = frozenset({"buff", "temporary"})

    condition = Conditions.has_tag(tag="buff")

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True
    world.get_entity_tags.assert_called_once_with(entity_id=entity_id)


def test_has_tag_returns_false_when_entity_lacks_tag() -> None:
    """Test has_tag condition returns False when entity lacks tag."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_entity_tags.return_value = frozenset({"debuff"})

    condition = Conditions.has_tag(tag="buff")

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_has_tag_returns_false_when_no_world() -> None:
    """Test has_tag condition returns False when world is None."""
    condition = Conditions.has_tag(tag="buff")

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=None)
    context.entity_id = EntityID(fake.uuid4())

    result = condition(context)

    assert result is False


def test_lacks_tag_returns_true_when_entity_lacks_tag() -> None:
    """Test lacks_tag condition returns True when entity lacks tag."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_entity_tags.return_value = frozenset({"debuff"})

    condition = Conditions.lacks_tag(tag="buff")

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True
    world.get_entity_tags.assert_called_once_with(entity_id=entity_id)


def test_lacks_tag_returns_false_when_entity_has_tag() -> None:
    """Test lacks_tag condition returns False when entity has tag."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_entity_tags.return_value = frozenset({"buff", "temporary"})

    condition = Conditions.lacks_tag(tag="buff")

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_lacks_tag_returns_false_when_no_world() -> None:
    """Test lacks_tag condition returns False when world is None."""
    condition = Conditions.lacks_tag(tag="buff")

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=None)
    context.entity_id = EntityID(fake.uuid4())

    result = condition(context)

    assert result is False


def test_tick_range_returns_true_when_within_range() -> None:
    """Test tick_range condition returns True when tick is within range."""
    world = Mock()
    world.tick = 150

    condition = Conditions.tick_range(min_tick=100, max_tick=200)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)

    result = condition(context)

    assert result is True


def test_tick_range_returns_true_at_min_boundary() -> None:
    """Test tick_range condition returns True at min boundary."""
    world = Mock()
    world.tick = 100

    condition = Conditions.tick_range(min_tick=100, max_tick=200)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)

    result = condition(context)

    assert result is True


def test_tick_range_returns_true_at_max_boundary() -> None:
    """Test tick_range condition returns True at max boundary."""
    world = Mock()
    world.tick = 200

    condition = Conditions.tick_range(min_tick=100, max_tick=200)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)

    result = condition(context)

    assert result is True


def test_tick_range_returns_false_when_below_range() -> None:
    """Test tick_range condition returns False when tick < min."""
    world = Mock()
    world.tick = 50

    condition = Conditions.tick_range(min_tick=100, max_tick=200)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)

    result = condition(context)

    assert result is False


def test_tick_range_returns_false_when_above_range() -> None:
    """Test tick_range condition returns False when tick > max."""
    world = Mock()
    world.tick = 250

    condition = Conditions.tick_range(min_tick=100, max_tick=200)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)

    result = condition(context)

    assert result is False


def test_tick_range_returns_false_when_no_world() -> None:
    """Test tick_range condition returns False when world is None."""
    condition = Conditions.tick_range(min_tick=100, max_tick=200)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=None)

    result = condition(context)

    assert result is False


def test_all_of_returns_true_when_all_conditions_true() -> None:
    """Test all_of condition returns True when all subconditions are True."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 75.0
    world.get_entity_tags.return_value = frozenset({"buff"})

    condition = Conditions.all_of(
        Conditions.stat_above("health", 50.0), Conditions.has_tag("buff")
    )

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True


def test_all_of_returns_false_when_one_condition_false() -> None:
    """Test all_of condition returns False when one subcondition is False."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 30.0
    world.get_entity_tags.return_value = frozenset({"buff"})

    condition = Conditions.all_of(
        Conditions.stat_above("health", 50.0), Conditions.has_tag("buff")
    )

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_all_of_returns_false_when_all_conditions_false() -> None:
    """Test all_of condition returns False when all subconditions are False."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 30.0
    world.get_entity_tags.return_value = frozenset({"debuff"})

    condition = Conditions.all_of(
        Conditions.stat_above("health", 50.0), Conditions.has_tag("buff")
    )

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_any_of_returns_true_when_all_conditions_true() -> None:
    """Test any_of condition returns True when all subconditions are True."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 75.0
    world.get_entity_tags.return_value = frozenset({"buff"})

    condition = Conditions.any_of(
        Conditions.stat_above("health", 50.0), Conditions.has_tag("buff")
    )

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True


def test_any_of_returns_true_when_one_condition_true() -> None:
    """Test any_of condition returns True when one subcondition is True."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 30.0
    world.get_entity_tags.return_value = frozenset({"buff"})

    condition = Conditions.any_of(
        Conditions.stat_above("health", 50.0), Conditions.has_tag("buff")
    )

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True


def test_any_of_returns_false_when_all_conditions_false() -> None:
    """Test any_of condition returns False when all subconditions are False."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 30.0
    world.get_entity_tags.return_value = frozenset({"debuff"})

    condition = Conditions.any_of(
        Conditions.stat_above("health", 50.0), Conditions.has_tag("buff")
    )

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_stat_equals_returns_true_when_bool_matches() -> None:
    """Test stat_equals returns True when boolean stat matches."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = True

    condition = Conditions.stat_equals(stat_name="in_combat", value=True)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True
    world.get_stat.assert_called_once_with(entity_id=entity_id, stat="in_combat")


def test_stat_equals_returns_false_when_bool_does_not_match() -> None:
    """Test stat_equals returns False when boolean stat does not match."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = False

    condition = Conditions.stat_equals(stat_name="in_combat", value=True)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_stat_equals_returns_true_when_string_matches() -> None:
    """Test stat_equals returns True when string stat matches."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = "fire"

    condition = Conditions.stat_equals(stat_name="element", value="fire")

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True
    world.get_stat.assert_called_once_with(entity_id=entity_id, stat="element")


def test_stat_equals_returns_false_when_string_does_not_match() -> None:
    """Test stat_equals returns False when string stat does not match."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = "ice"

    condition = Conditions.stat_equals(stat_name="element", value="fire")

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_stat_equals_returns_true_when_int_matches() -> None:
    """Test stat_equals returns True when int stat matches."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 10

    condition = Conditions.stat_equals(stat_name="level", value=10)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True


def test_stat_equals_returns_false_when_int_does_not_match() -> None:
    """Test stat_equals returns False when int stat does not match."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 5

    condition = Conditions.stat_equals(stat_name="level", value=10)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_stat_equals_returns_false_when_no_world() -> None:
    """Test stat_equals returns False when world is None."""
    condition = Conditions.stat_equals(stat_name="in_combat", value=True)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=None)
    context.entity_id = EntityID(fake.uuid4())

    result = condition(context)

    assert result is False


def test_stat_not_equals_returns_true_when_bool_does_not_match() -> None:
    """Test stat_not_equals returns True when boolean stat does not match."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = False

    condition = Conditions.stat_not_equals(stat_name="in_combat", value=True)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True
    world.get_stat.assert_called_once_with(entity_id=entity_id, stat="in_combat")


def test_stat_not_equals_returns_false_when_bool_matches() -> None:
    """Test stat_not_equals returns False when boolean stat matches."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = True

    condition = Conditions.stat_not_equals(stat_name="in_combat", value=True)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_stat_not_equals_returns_true_when_string_does_not_match() -> None:
    """Test stat_not_equals returns True when string stat does not match."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = "ice"

    condition = Conditions.stat_not_equals(stat_name="element", value="fire")

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True


def test_stat_not_equals_returns_false_when_string_matches() -> None:
    """Test stat_not_equals returns False when string stat matches."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = "fire"

    condition = Conditions.stat_not_equals(stat_name="element", value="fire")

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_stat_not_equals_returns_false_when_no_world() -> None:
    """Test stat_not_equals returns False when world is None."""
    condition = Conditions.stat_not_equals(stat_name="in_combat", value=True)

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=None)
    context.entity_id = EntityID(fake.uuid4())

    result = condition(context)

    assert result is False


def test_stat_in_returns_true_when_value_in_set() -> None:
    """Test stat_in returns True when stat value is in set."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = "fire"

    condition = Conditions.stat_in(
        stat_name="element", values=frozenset({"fire", "ice", "lightning"})
    )

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True
    world.get_stat.assert_called_once_with(entity_id=entity_id, stat="element")


def test_stat_in_returns_false_when_value_not_in_set() -> None:
    """Test stat_in returns False when stat value is not in set."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = "water"

    condition = Conditions.stat_in(
        stat_name="element", values=frozenset({"fire", "ice", "lightning"})
    )

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_stat_in_works_with_numeric_values() -> None:
    """Test stat_in works with numeric values."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 20

    condition = Conditions.stat_in(stat_name="level", values=frozenset({10, 20, 30}))

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True


def test_stat_in_returns_false_when_no_world() -> None:
    """Test stat_in returns False when world is None."""
    condition = Conditions.stat_in(
        stat_name="element", values=frozenset({"fire", "ice"})
    )

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=None)
    context.entity_id = EntityID(fake.uuid4())

    result = condition(context)

    assert result is False


def test_stat_not_in_returns_true_when_value_not_in_set() -> None:
    """Test stat_not_in returns True when stat value is not in set."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = "water"

    condition = Conditions.stat_not_in(
        stat_name="element", values=frozenset({"fire", "ice", "lightning"})
    )

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True
    world.get_stat.assert_called_once_with(entity_id=entity_id, stat="element")


def test_stat_not_in_returns_false_when_value_in_set() -> None:
    """Test stat_not_in returns False when stat value is in set."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = "fire"

    condition = Conditions.stat_not_in(
        stat_name="element", values=frozenset({"fire", "ice", "lightning"})
    )

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is False


def test_stat_not_in_works_with_numeric_values() -> None:
    """Test stat_not_in works with numeric values."""
    entity_id = EntityID(fake.uuid4())
    world = Mock()
    world.get_stat.return_value = 5

    condition = Conditions.stat_not_in(
        stat_name="level", values=frozenset({10, 20, 30})
    )

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=world)
    context.entity_id = entity_id

    result = condition(context)

    assert result is True


def test_stat_not_in_returns_false_when_no_world() -> None:
    """Test stat_not_in returns False when world is None."""
    condition = Conditions.stat_not_in(
        stat_name="element", values=frozenset({"fire", "ice"})
    )

    context = ModifierContext(modifiers=[], config=ModifierConfig(), world=None)
    context.entity_id = EntityID(fake.uuid4())

    result = condition(context)

    assert result is False

"""Tests for event filtering."""

import time
from dataclasses import dataclass
from unittest.mock import MagicMock

from faker import Faker

from yuna.events.dispatcher import EventDispatcher
from yuna.events.event import Event
from yuna.events.filtering import (
    CompositeFilter,
    CompositeMode,
    EntityFilter,
    EventFilter,
    PredicateFilter,
    TypeFilter,
)
from yuna.types.identifiers import EntityID

fake = Faker()


@dataclass(frozen=True)
class TestEntityEvent(Event):
    """Test event with entity ID."""

    entity_id: EntityID
    message: str


@dataclass(frozen=True)
class TestEvent(Event):
    """Test event implementation."""

    message: str


@dataclass(frozen=True)
class TestValueEvent(Event):
    """Test event with value field."""

    value: int


def test_event_filter_protocol() -> None:
    """Test that filter classes implement EventFilter protocol."""
    entity_id = EntityID(fake.uuid4())

    assert isinstance(EntityFilter(entity_id=entity_id), EventFilter)
    assert isinstance(TypeFilter(event_types=["TestEvent"]), EventFilter)
    assert isinstance(PredicateFilter(predicate=lambda e: True), EventFilter)
    assert isinstance(CompositeFilter(filters=[]), EventFilter)


def test_entity_filter_matches_correct_entity() -> None:
    """Test EntityFilter matches events with correct entity ID."""
    entity_id = EntityID(fake.uuid4())
    event_filter = EntityFilter(entity_id=entity_id)

    event = TestEntityEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        entity_id=entity_id,
        message=fake.text(),
    )

    assert event_filter.matches(event=event) is True


def test_entity_filter_does_not_match_different_entity() -> None:
    """Test EntityFilter does not match events with different entity ID."""
    entity_id_1 = EntityID(fake.uuid4())
    entity_id_2 = EntityID(fake.uuid4())
    event_filter = EntityFilter(entity_id=entity_id_1)

    event = TestEntityEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        entity_id=entity_id_2,
        message=fake.text(),
    )

    assert event_filter.matches(event=event) is False


def test_entity_filter_does_not_match_event_without_entity_id() -> None:
    """Test EntityFilter does not match events without entity_id field."""
    entity_id = EntityID(fake.uuid4())
    event_filter = EntityFilter(entity_id=entity_id)

    event = TestEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    assert event_filter.matches(event=event) is False


def test_type_filter_matches_correct_type() -> None:
    """Test TypeFilter matches events with correct type."""
    event_filter = TypeFilter(event_types=["TestEvent"])

    event = TestEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    assert event_filter.matches(event=event) is True


def test_type_filter_does_not_match_different_type() -> None:
    """Test TypeFilter does not match events with different type."""
    event_filter = TypeFilter(event_types=["TestValueEvent"])

    event = TestEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    assert event_filter.matches(event=event) is False


def test_type_filter_matches_multiple_types() -> None:
    """Test TypeFilter matches any of multiple event types."""
    event_filter = TypeFilter(event_types=["TestEvent", "TestValueEvent"])

    event_1 = TestEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )
    event_2 = TestValueEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        value=fake.random_int(min=0, max=100),
    )

    assert event_filter.matches(event=event_1) is True
    assert event_filter.matches(event=event_2) is True


def test_type_filter_accepts_set() -> None:
    """Test TypeFilter can be initialized with set."""
    event_filter = TypeFilter(event_types={"TestEvent"})

    event = TestEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    assert event_filter.matches(event=event) is True


def test_predicate_filter_matches_when_predicate_true() -> None:
    """Test PredicateFilter matches when predicate returns True."""
    event_filter = PredicateFilter(
        predicate=lambda e: hasattr(e, "value") and e.value > 50
    )

    event = TestValueEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        value=75,
    )

    assert event_filter.matches(event=event) is True


def test_predicate_filter_does_not_match_when_predicate_false() -> None:
    """Test PredicateFilter does not match when predicate returns False."""
    event_filter = PredicateFilter(
        predicate=lambda e: hasattr(e, "value") and e.value > 50
    )

    event = TestValueEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        value=25,
    )

    assert event_filter.matches(event=event) is False


def test_composite_filter_and_mode_all_match() -> None:
    """Test CompositeFilter with AND mode matches when all filters match."""
    entity_id = EntityID(fake.uuid4())
    entity_filter = EntityFilter(entity_id=entity_id)
    type_filter = TypeFilter(event_types=["TestEntityEvent"])

    composite_filter = CompositeFilter(
        filters=[entity_filter, type_filter],
        mode=CompositeMode.AND,
    )

    event = TestEntityEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        entity_id=entity_id,
        message=fake.text(),
    )

    assert composite_filter.matches(event=event) is True


def test_composite_filter_and_mode_one_fails() -> None:
    """Test CompositeFilter with AND mode does not match when one filter fails."""
    entity_id_1 = EntityID(fake.uuid4())
    entity_id_2 = EntityID(fake.uuid4())
    entity_filter = EntityFilter(entity_id=entity_id_1)
    type_filter = TypeFilter(event_types=["TestEntityEvent"])

    composite_filter = CompositeFilter(
        filters=[entity_filter, type_filter],
        mode=CompositeMode.AND,
    )

    event = TestEntityEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        entity_id=entity_id_2,
        message=fake.text(),
    )

    assert composite_filter.matches(event=event) is False


def test_composite_filter_or_mode_one_matches() -> None:
    """Test CompositeFilter with OR mode matches when any filter matches."""
    entity_id_1 = EntityID(fake.uuid4())
    entity_id_2 = EntityID(fake.uuid4())
    entity_filter = EntityFilter(entity_id=entity_id_1)
    type_filter = TypeFilter(event_types=["TestEntityEvent"])

    composite_filter = CompositeFilter(
        filters=[entity_filter, type_filter],
        mode=CompositeMode.OR,
    )

    event = TestEntityEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        entity_id=entity_id_2,
        message=fake.text(),
    )

    assert composite_filter.matches(event=event) is True


def test_composite_filter_or_mode_none_match() -> None:
    """Test CompositeFilter with OR mode does not match when no filters match."""
    entity_id_1 = EntityID(fake.uuid4())
    entity_id_2 = EntityID(fake.uuid4())
    entity_filter = EntityFilter(entity_id=entity_id_1)
    type_filter = TypeFilter(event_types=["TestValueEvent"])

    composite_filter = CompositeFilter(
        filters=[entity_filter, type_filter],
        mode=CompositeMode.OR,
    )

    event = TestEntityEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        entity_id=entity_id_2,
        message=fake.text(),
    )

    assert composite_filter.matches(event=event) is False


def test_composite_filter_empty_list_matches() -> None:
    """Test CompositeFilter with empty filter list matches all events."""
    composite_filter = CompositeFilter(filters=[])

    event = TestEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    assert composite_filter.matches(event=event) is True


def test_composite_filter_defaults_to_and_mode() -> None:
    """Test CompositeFilter defaults to AND mode."""
    entity_id = EntityID(fake.uuid4())
    entity_filter = EntityFilter(entity_id=entity_id)
    type_filter = TypeFilter(event_types=["TestEntityEvent"])

    composite_filter = CompositeFilter(filters=[entity_filter, type_filter])

    event = TestEntityEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        entity_id=entity_id,
        message=fake.text(),
    )

    assert composite_filter.matches(event=event) is True


def test_dispatcher_with_entity_filter() -> None:
    """Test dispatcher with EntityFilter only calls matching handlers."""
    dispatcher = EventDispatcher()
    entity_id_1 = EntityID(fake.uuid4())
    entity_id_2 = EntityID(fake.uuid4())

    handler_1 = MagicMock()
    handler_2 = MagicMock()

    dispatcher.subscribe(
        event_type="TestEntityEvent",
        handler=handler_1,
        event_filter=EntityFilter(entity_id=entity_id_1),
    )
    dispatcher.subscribe(
        event_type="TestEntityEvent",
        handler=handler_2,
        event_filter=EntityFilter(entity_id=entity_id_2),
    )

    event = TestEntityEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        entity_id=entity_id_1,
        message=fake.text(),
    )

    dispatcher.dispatch(event=event)

    handler_1.assert_called_once_with(event)
    handler_2.assert_not_called()


def test_dispatcher_with_type_filter() -> None:
    """Test dispatcher with TypeFilter only calls matching handlers."""
    dispatcher = EventDispatcher()

    handler_1 = MagicMock()
    handler_2 = MagicMock()

    dispatcher.subscribe_all(
        handler=handler_1,
        event_filter=TypeFilter(event_types=["TestEvent"]),
    )
    dispatcher.subscribe_all(
        handler=handler_2,
        event_filter=TypeFilter(event_types=["TestValueEvent"]),
    )

    event = TestEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    dispatcher.dispatch(event=event)

    handler_1.assert_called_once_with(event)
    handler_2.assert_not_called()


def test_dispatcher_with_predicate_filter() -> None:
    """Test dispatcher with PredicateFilter only calls matching handlers."""
    dispatcher = EventDispatcher()

    handler_high = MagicMock()
    handler_low = MagicMock()

    dispatcher.subscribe(
        event_type="TestValueEvent",
        handler=handler_high,
        event_filter=PredicateFilter(predicate=lambda e: e.value > 50),  # type: ignore[attr-defined]
    )
    dispatcher.subscribe(
        event_type="TestValueEvent",
        handler=handler_low,
        event_filter=PredicateFilter(predicate=lambda e: e.value <= 50),  # type: ignore[attr-defined]
    )

    event = TestValueEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        value=75,
    )

    dispatcher.dispatch(event=event)

    handler_high.assert_called_once_with(event)
    handler_low.assert_not_called()


def test_dispatcher_with_composite_filter() -> None:
    """Test dispatcher with CompositeFilter only calls matching handlers."""
    dispatcher = EventDispatcher()
    entity_id = EntityID(fake.uuid4())

    handler = MagicMock()

    composite_filter = CompositeFilter(
        filters=[
            EntityFilter(entity_id=entity_id),
            PredicateFilter(predicate=lambda e: len(e.message) > 5),  # type: ignore[attr-defined]
        ],
        mode=CompositeMode.AND,
    )

    dispatcher.subscribe(
        event_type="TestEntityEvent",
        handler=handler,
        event_filter=composite_filter,
    )

    event_match = TestEntityEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        entity_id=entity_id,
        message="long message",
    )
    event_no_match = TestEntityEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        entity_id=entity_id,
        message="hi",
    )

    dispatcher.dispatch(event=event_match)
    dispatcher.dispatch(event=event_no_match)

    handler.assert_called_once_with(event_match)


def test_dispatcher_with_no_filter() -> None:
    """Test dispatcher without filter calls handler for all events."""
    dispatcher = EventDispatcher()
    handler = MagicMock()

    dispatcher.subscribe(event_type="TestEvent", handler=handler)

    event_1 = TestEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )
    event_2 = TestEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    dispatcher.dispatch(event=event_1)
    dispatcher.dispatch(event=event_2)

    assert handler.call_count == 2


def test_filtered_handler_not_called_when_filter_fails() -> None:
    """Test handler with filter is not called when filter does not match."""
    dispatcher = EventDispatcher()
    handler = MagicMock()

    dispatcher.subscribe(
        event_type="TestValueEvent",
        handler=handler,
        event_filter=PredicateFilter(predicate=lambda e: e.value > 100),  # type: ignore[attr-defined]
    )

    event = TestValueEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        value=50,
    )

    dispatcher.dispatch(event=event)

    handler.assert_not_called()


def test_multiple_handlers_with_different_filters() -> None:
    """Test multiple handlers with different filters called appropriately."""
    dispatcher = EventDispatcher()
    handler_1 = MagicMock()
    handler_2 = MagicMock()
    handler_3 = MagicMock()

    dispatcher.subscribe(
        event_type="TestValueEvent",
        handler=handler_1,
        event_filter=PredicateFilter(predicate=lambda e: e.value < 50),  # type: ignore[attr-defined]
    )
    dispatcher.subscribe(
        event_type="TestValueEvent",
        handler=handler_2,
        event_filter=PredicateFilter(predicate=lambda e: e.value >= 50),  # type: ignore[attr-defined]
    )
    dispatcher.subscribe(event_type="TestValueEvent", handler=handler_3)

    event = TestValueEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        value=75,
    )

    dispatcher.dispatch(event=event)

    handler_1.assert_not_called()
    handler_2.assert_called_once_with(event)
    handler_3.assert_called_once_with(event)

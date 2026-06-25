"""Tests for event consumption."""

import time
from dataclasses import dataclass
from unittest.mock import MagicMock

from faker import Faker

from yuna.events.consumption import ConsumableEvent
from yuna.events.dispatcher import EventDispatcher
from yuna.events.event import Event

fake = Faker()


@dataclass(frozen=True)
class TestConsumableEvent(Event, ConsumableEvent):
    """Test consumable event implementation."""

    message: str


@dataclass(frozen=True)
class TestNonConsumableEvent(Event):
    """Test non-consumable event implementation."""

    message: str


def test_consumable_event_not_consumed_initially() -> None:
    """Test consumable event is not consumed by default."""
    event = TestConsumableEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )
    assert event.is_consumed is False


def test_consumable_event_can_be_consumed() -> None:
    """Test consumable event can be marked as consumed."""
    event = TestConsumableEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )
    event.consume()
    assert event.is_consumed is True


def test_consumed_event_stops_propagation_to_type_specific_handlers() -> None:
    """Test consumed event stops propagation to remaining type-specific handlers."""
    dispatcher = EventDispatcher()
    handler_1 = MagicMock()
    handler_2 = MagicMock()

    def consuming_handler(event: Event) -> None:
        if isinstance(event, ConsumableEvent):
            event.consume()

    event = TestConsumableEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    dispatcher.subscribe(event_type="TestConsumableEvent", handler=handler_1)
    dispatcher.subscribe(event_type="TestConsumableEvent", handler=consuming_handler)
    dispatcher.subscribe(event_type="TestConsumableEvent", handler=handler_2)

    dispatcher.dispatch(event=event)

    handler_1.assert_called_once_with(event)
    handler_2.assert_not_called()


def test_consumed_event_stops_propagation_to_wildcard_handlers() -> None:
    """Test consumed event stops propagation to wildcard handlers."""
    dispatcher = EventDispatcher()
    specific_handler = MagicMock()
    wildcard_handler = MagicMock()

    def consuming_handler(event: Event) -> None:
        if isinstance(event, ConsumableEvent):
            event.consume()

    event = TestConsumableEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    dispatcher.subscribe(event_type="TestConsumableEvent", handler=specific_handler)
    dispatcher.subscribe(
        event_type="TestConsumableEvent",
        handler=consuming_handler,
    )
    dispatcher.subscribe_all(handler=wildcard_handler)

    dispatcher.dispatch(event=event)

    specific_handler.assert_called_once_with(event)
    wildcard_handler.assert_not_called()


def test_consume_flag_automatically_consumes_event() -> None:
    """Test handlers with consume=True automatically consume events."""
    dispatcher = EventDispatcher()
    handler_1 = MagicMock()
    handler_2 = MagicMock()

    event = TestConsumableEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    dispatcher.subscribe(event_type="TestConsumableEvent", handler=handler_1)
    dispatcher.subscribe(
        event_type="TestConsumableEvent",
        handler=handler_2,
        consume=True,
    )
    dispatcher.subscribe(event_type="TestConsumableEvent", handler=MagicMock())

    dispatcher.dispatch(event=event)

    handler_1.assert_called_once_with(event)
    handler_2.assert_called_once_with(event)
    assert event.is_consumed is True


def test_consume_flag_on_wildcard_handler() -> None:
    """Test wildcard handler with consume=True consumes events."""
    dispatcher = EventDispatcher()
    wildcard_handler = MagicMock()
    later_handler = MagicMock()

    event = TestConsumableEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    dispatcher.subscribe_all(handler=wildcard_handler, consume=True)
    dispatcher.subscribe_all(handler=later_handler)

    dispatcher.dispatch(event=event)

    wildcard_handler.assert_called_once_with(event)
    later_handler.assert_not_called()


def test_non_consumable_events_ignore_consumption() -> None:
    """Test non-consumable events work normally regardless of consume flag."""
    dispatcher = EventDispatcher()
    handler_1 = MagicMock()
    handler_2 = MagicMock()

    event = TestNonConsumableEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    dispatcher.subscribe(
        event_type="TestNonConsumableEvent",
        handler=handler_1,
        consume=True,
    )
    dispatcher.subscribe(event_type="TestNonConsumableEvent", handler=handler_2)

    dispatcher.dispatch(event=event)

    handler_1.assert_called_once_with(event)
    handler_2.assert_called_once_with(event)


def test_consumed_event_between_type_specific_and_wildcard() -> None:
    """Test consumption in type-specific handlers stops wildcard handlers."""
    dispatcher = EventDispatcher()
    specific_handler = MagicMock()
    wildcard_handler = MagicMock()

    event = TestConsumableEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    dispatcher.subscribe(
        event_type="TestConsumableEvent",
        handler=specific_handler,
        consume=True,
    )
    dispatcher.subscribe_all(handler=wildcard_handler)

    dispatcher.dispatch(event=event)

    specific_handler.assert_called_once_with(event)
    wildcard_handler.assert_not_called()


def test_multiple_consumable_events_independent() -> None:
    """Test consumption state is independent between events."""
    dispatcher = EventDispatcher()
    handler = MagicMock()

    event_1 = TestConsumableEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )
    event_2 = TestConsumableEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    event_1.consume()

    dispatcher.subscribe(event_type="TestConsumableEvent", handler=handler)

    dispatcher.dispatch(event=event_1)
    dispatcher.dispatch(event=event_2)

    handler.assert_called_once_with(event_2)


def test_consume_flag_false_does_not_consume() -> None:
    """Test handlers with consume=False do not consume events."""
    dispatcher = EventDispatcher()
    handler_1 = MagicMock()
    handler_2 = MagicMock()

    event = TestConsumableEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    dispatcher.subscribe(
        event_type="TestConsumableEvent",
        handler=handler_1,
        consume=False,
    )
    dispatcher.subscribe(event_type="TestConsumableEvent", handler=handler_2)

    dispatcher.dispatch(event=event)

    handler_1.assert_called_once_with(event)
    handler_2.assert_called_once_with(event)
    assert event.is_consumed is False


def test_weakset_allows_garbage_collection() -> None:
    """Test consumed events can be garbage collected."""
    event = TestConsumableEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )
    event.consume()
    assert event.is_consumed is True
    del event

    new_event = TestConsumableEvent(
        timestamp=time.time(),
        tick=fake.random_int(min=0, max=1000),
        message=fake.text(),
    )

    assert new_event.is_consumed is False

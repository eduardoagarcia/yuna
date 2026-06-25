"""Tests for event dispatcher."""

import time
from dataclasses import dataclass
from unittest.mock import MagicMock

from faker import Faker

from yuna.events.dispatcher import EventDispatcher
from yuna.events.event import Event

fake = Faker()


@dataclass(frozen=True)
class TestEvent(Event):
    """Test event implementation."""

    message: str


@dataclass(frozen=True)
class AnotherEvent(Event):
    """Another test event implementation."""

    value: int


def test_event_dispatcher_creation() -> None:
    """Test EventDispatcher can be instantiated."""
    dispatcher = EventDispatcher()
    assert dispatcher is not None


def test_subscribe_to_event_type() -> None:
    """Test subscribing handler to specific event type."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    dispatcher.subscribe(event_type="TestEvent", handler=handler)
    assert dispatcher.count_subscriptions(event_type="TestEvent") == 1


def test_dispatch_calls_subscribed_handler() -> None:
    """Test dispatching event calls subscribed handler."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    dispatcher.subscribe(event_type="TestEvent", handler=handler)
    dispatcher.dispatch(event=event)
    handler.assert_called_once_with(event)


def test_dispatch_does_not_call_unsubscribed_handlers() -> None:
    """Test dispatching event does not call handlers for different type."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    dispatcher.subscribe(event_type="AnotherEvent", handler=handler)
    dispatcher.dispatch(event=event)
    handler.assert_not_called()


def test_subscribe_all() -> None:
    """Test subscribing wildcard handler to all events."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    dispatcher.subscribe_all(handler=handler)
    assert dispatcher.count_wildcard_subscriptions() == 1


def test_wildcard_handler_receives_all_events() -> None:
    """Test wildcard handler called for any event type."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    dispatcher.subscribe_all(handler=handler)
    event_1 = TestEvent(timestamp=time.time(), tick=0, message="test")
    event_2 = AnotherEvent(timestamp=time.time(), tick=0, value=42)
    dispatcher.dispatch(event=event_1)
    dispatcher.dispatch(event=event_2)
    assert handler.call_count == 2


def test_unsubscribe_handler() -> None:
    """Test unsubscribing handler from event type."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    dispatcher.subscribe(event_type="TestEvent", handler=handler)
    dispatcher.unsubscribe(event_type="TestEvent", handler=handler)
    assert dispatcher.count_subscriptions(event_type="TestEvent") == 0


def test_unsubscribe_prevents_handler_from_being_called() -> None:
    """Test unsubscribed handler not called on dispatch."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    dispatcher.subscribe(event_type="TestEvent", handler=handler)
    dispatcher.unsubscribe(event_type="TestEvent", handler=handler)
    dispatcher.dispatch(event=event)
    handler.assert_not_called()


def test_unsubscribe_all_wildcard_handler() -> None:
    """Test unsubscribing wildcard handler."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    dispatcher.subscribe_all(handler=handler)
    dispatcher.unsubscribe_all(handler=handler)
    assert dispatcher.count_wildcard_subscriptions() == 0


def test_unsubscribe_all_prevents_wildcard_handler_from_being_called() -> None:
    """Test unsubscribed wildcard handler not called."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    dispatcher.subscribe_all(handler=handler)
    dispatcher.unsubscribe_all(handler=handler)
    dispatcher.dispatch(event=event)
    handler.assert_not_called()


def test_multiple_handlers_for_same_event() -> None:
    """Test multiple handlers can subscribe to same event type."""
    dispatcher = EventDispatcher()
    handler_1 = MagicMock()
    handler_2 = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    dispatcher.subscribe(event_type="TestEvent", handler=handler_1)
    dispatcher.subscribe(event_type="TestEvent", handler=handler_2)
    dispatcher.dispatch(event=event)
    handler_1.assert_called_once_with(event)
    handler_2.assert_called_once_with(event)


def test_same_handler_subscribed_once() -> None:
    """Test subscribing same handler multiple times only adds it once."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    dispatcher.subscribe(event_type="TestEvent", handler=handler)
    dispatcher.subscribe(event_type="TestEvent", handler=handler)
    assert dispatcher.count_subscriptions(event_type="TestEvent") == 1


def test_same_wildcard_handler_subscribed_once() -> None:
    """Test subscribing same wildcard handler multiple times only adds it once."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    dispatcher.subscribe_all(handler=handler)
    dispatcher.subscribe_all(handler=handler)
    assert dispatcher.count_wildcard_subscriptions() == 1


def test_dispatch_with_no_subscribers() -> None:
    """Test dispatching event with no subscribers completes without error."""
    dispatcher = EventDispatcher()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    dispatcher.dispatch(event=event)


def test_unsubscribe_non_existent_handler() -> None:
    """Test unsubscribing non-existent handler completes without error."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    dispatcher.unsubscribe(event_type="TestEvent", handler=handler)


def test_unsubscribe_non_existent_event_type() -> None:
    """Test unsubscribing from non-existent event type."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    dispatcher.unsubscribe(event_type="NonExistentEvent", handler=handler)


def test_unsubscribe_all_non_existent_wildcard() -> None:
    """Test unsubscribing non-existent wildcard handler."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    dispatcher.unsubscribe_all(handler=handler)


def test_count_subscriptions_returns_zero_for_non_existent_type() -> None:
    """Test count_subscriptions returns 0 for unsubscribed type."""
    dispatcher = EventDispatcher()
    assert dispatcher.count_subscriptions(event_type="TestEvent") == 0


def test_count_wildcard_subscriptions_returns_zero_initially() -> None:
    """Test count_wildcard_subscriptions returns 0 initially."""
    dispatcher = EventDispatcher()
    assert dispatcher.count_wildcard_subscriptions() == 0


def test_type_specific_and_wildcard_handlers_both_called() -> None:
    """Test both type-specific and wildcard handlers called for event."""
    dispatcher = EventDispatcher()
    specific_handler = MagicMock()
    wildcard_handler = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    dispatcher.subscribe(event_type="TestEvent", handler=specific_handler)
    dispatcher.subscribe_all(handler=wildcard_handler)
    dispatcher.dispatch(event=event)
    specific_handler.assert_called_once_with(event)
    wildcard_handler.assert_called_once_with(event)


def test_type_specific_handlers_called_before_wildcard() -> None:
    """Test type-specific handlers called before wildcard handlers."""
    dispatcher = EventDispatcher()
    call_order = []

    def specific_handler(event: Event) -> None:
        call_order.append("specific")

    def wildcard_handler(event: Event) -> None:
        call_order.append("wildcard")

    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    dispatcher.subscribe(event_type="TestEvent", handler=specific_handler)
    dispatcher.subscribe_all(handler=wildcard_handler)
    dispatcher.dispatch(event=event)
    assert call_order == ["specific", "wildcard"]


def test_multiple_wildcard_handlers() -> None:
    """Test multiple wildcard handlers can be subscribed."""
    dispatcher = EventDispatcher()
    handler_1 = MagicMock()
    handler_2 = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    dispatcher.subscribe_all(handler=handler_1)
    dispatcher.subscribe_all(handler=handler_2)
    dispatcher.dispatch(event=event)
    handler_1.assert_called_once_with(event)
    handler_2.assert_called_once_with(event)


def test_unsubscribe_one_of_multiple_handlers() -> None:
    """Test unsubscribing one handler does not affect others."""
    dispatcher = EventDispatcher()
    handler_1 = MagicMock()
    handler_2 = MagicMock()
    event = TestEvent(timestamp=time.time(), tick=0, message="test")
    dispatcher.subscribe(event_type="TestEvent", handler=handler_1)
    dispatcher.subscribe(event_type="TestEvent", handler=handler_2)
    dispatcher.unsubscribe(event_type="TestEvent", handler=handler_1)
    dispatcher.dispatch(event=event)
    handler_1.assert_not_called()
    handler_2.assert_called_once_with(event)


def test_unsubscribe_removes_empty_event_type() -> None:
    """Test unsubscribing last handler removes event type."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    dispatcher.subscribe(event_type="TestEvent", handler=handler)
    dispatcher.unsubscribe(event_type="TestEvent", handler=handler)
    assert dispatcher.count_subscriptions(event_type="TestEvent") == 0


def test_handler_receives_correct_event_data() -> None:
    """Test handler receives event with correct data."""
    dispatcher = EventDispatcher()
    received_events = []

    def handler(event: Event) -> None:
        received_events.append(event)

    message = "test message"
    event = TestEvent(timestamp=time.time(), tick=42, message=message)
    dispatcher.subscribe(event_type="TestEvent", handler=handler)
    dispatcher.dispatch(event=event)
    assert len(received_events) == 1
    assert received_events[0].message == message  # type: ignore[attr-defined]
    assert received_events[0].tick == 42


def test_dispatch_multiple_events_in_sequence() -> None:
    """Test dispatching multiple events in sequence."""
    dispatcher = EventDispatcher()
    handler = MagicMock()
    dispatcher.subscribe(event_type="TestEvent", handler=handler)
    event_1 = TestEvent(timestamp=time.time(), tick=0, message="first")
    event_2 = TestEvent(timestamp=time.time(), tick=1, message="second")
    event_3 = TestEvent(timestamp=time.time(), tick=2, message="third")
    dispatcher.dispatch(event=event_1)
    dispatcher.dispatch(event=event_2)
    dispatcher.dispatch(event=event_3)
    assert handler.call_count == 3

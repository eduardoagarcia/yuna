"""Tests for replay recording configuration."""

from faker import Faker

from yuna.replay.config import RecordingConfig

fake = Faker()


def test_recording_config_default_values() -> None:
    """Test recording config has correct default values."""
    config = RecordingConfig()

    assert config.included_components is None
    assert config.excluded_components == set()
    assert config.included_event_types is None
    assert config.excluded_event_types == set()
    assert config.record_commands is True
    assert config.record_metadata is True
    assert config.skip_empty_marker_components is True
    assert config.frame_update_components == set()


def test_should_include_component_with_inclusion_list() -> None:
    """Test component inclusion when inclusion list is specified."""
    component1 = fake.unique.word()
    component2 = fake.unique.word()
    component3 = fake.unique.word()

    config = RecordingConfig(included_components={component1, component2})

    assert config.should_include_component(component_name=component1) is True
    assert config.should_include_component(component_name=component2) is True
    assert config.should_include_component(component_name=component3) is False


def test_should_include_component_with_exclusion_list() -> None:
    """Test component inclusion when exclusion list is specified."""
    component1 = fake.unique.word()
    component2 = fake.unique.word()
    component3 = fake.unique.word()

    config = RecordingConfig(excluded_components={component1})

    assert config.should_include_component(component_name=component1) is False
    assert config.should_include_component(component_name=component2) is True
    assert config.should_include_component(component_name=component3) is True


def test_should_include_component_defaults_to_true() -> None:
    """Test component inclusion defaults to true when no filters specified."""
    config = RecordingConfig()

    component_name = fake.word()
    assert config.should_include_component(component_name=component_name) is True


def test_should_include_event_with_inclusion_list() -> None:
    """Test event inclusion when inclusion list is specified."""
    event1 = fake.unique.word()
    event2 = fake.unique.word()
    event3 = fake.unique.word()

    config = RecordingConfig(included_event_types={event1, event2})

    assert config.should_include_event(event_type=event1) is True
    assert config.should_include_event(event_type=event2) is True
    assert config.should_include_event(event_type=event3) is False


def test_should_include_event_with_exclusion_list() -> None:
    """Test event inclusion when exclusion list is specified."""
    event1 = fake.unique.word()
    event2 = fake.unique.word()
    event3 = fake.unique.word()

    config = RecordingConfig(excluded_event_types={event1})

    assert config.should_include_event(event_type=event1) is False
    assert config.should_include_event(event_type=event2) is True
    assert config.should_include_event(event_type=event3) is True


def test_should_include_event_defaults_to_true() -> None:
    """Test event inclusion defaults to true when no filters specified."""
    config = RecordingConfig()

    event_type = fake.word()
    assert config.should_include_event(event_type=event_type) is True


def test_recording_config_with_all_options() -> None:
    """Test creating recording config with all options specified."""
    included_components = {fake.word() for _ in range(3)}
    excluded_components = {fake.word() for _ in range(2)}
    included_events = {fake.word() for _ in range(3)}
    excluded_events = {fake.word() for _ in range(2)}

    config = RecordingConfig(
        included_components=included_components,
        excluded_components=excluded_components,
        included_event_types=included_events,
        excluded_event_types=excluded_events,
        record_commands=False,
        record_metadata=False,
        skip_empty_marker_components=False,
    )

    assert config.included_components == included_components
    assert config.excluded_components == excluded_components
    assert config.included_event_types == included_events
    assert config.excluded_event_types == excluded_events
    assert config.record_commands is False
    assert config.record_metadata is False
    assert config.skip_empty_marker_components is False


def test_inclusion_list_takes_precedence_over_exclusion() -> None:
    """Test that inclusion list takes precedence over exclusion list."""
    component1 = fake.unique.word()
    component2 = fake.unique.word()

    config = RecordingConfig(
        included_components={component1},
        excluded_components={component1, component2},
    )

    assert config.should_include_component(component_name=component1) is True
    assert config.should_include_component(component_name=component2) is False


def test_recording_config_frame_update_components() -> None:
    """Test frame_update_components can be configured."""
    components = {fake.word() for _ in range(2)}

    config = RecordingConfig(frame_update_components=components)

    assert config.frame_update_components == components

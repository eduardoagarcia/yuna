"""Configuration for game recording system."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RecordingConfig:
    """Controls what data is captured in game recordings.

    Responsibilities:
    - Filter components by inclusion/exclusion
    - Filter events by type
    - Enable/disable command recording
    - Enable/disable metadata recording
    - Optimize storage by skipping empty marker components

    Usage:
        config = RecordingConfig(
            included_components={"Position", "Health"},
            excluded_event_types={"PositionUpdated"},
            record_commands=False,
        )

        recorder = GameRecorder(
            frequency=1,
            mode=RecordingMode.DELTA_ONLY,
            config=config,
        )
    """

    included_components: set[str] | None = None
    excluded_components: set[str] = field(default_factory=set)
    included_event_types: set[str] | None = None
    excluded_event_types: set[str] = field(default_factory=set)
    record_commands: bool = True
    record_metadata: bool = True
    skip_empty_marker_components: bool = True
    frame_update_components: set[str] = field(default_factory=set)

    def should_include_component(self, component_name: str) -> bool:
        """Check if component should be recorded.

        Uses inclusion list if specified, otherwise exclusion list.

        Args:
            component_name: Name of component type to check

        Returns:
            True if component should be recorded
        """
        if self.included_components is not None:
            return component_name in self.included_components
        return component_name not in self.excluded_components

    def should_include_event(self, event_type: str) -> bool:
        """Check if event should be recorded.

        Uses inclusion list if specified, otherwise exclusion list.

        Args:
            event_type: Type of event to check

        Returns:
            True if event should be recorded
        """
        if self.included_event_types is not None:
            return event_type in self.included_event_types
        return event_type not in self.excluded_event_types

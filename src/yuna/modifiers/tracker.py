"""Tracker for active modifiers with expiration."""

from yuna.modifiers.expiration import TrackedModifier
from yuna.modifiers.modifier import Modifier
from yuna.types.identifiers import EntityID


class ModifierTracker:
    """Tracks active modifiers and handles expiration.

    Responsibilities:
    - Track modifiers with duration
    - Automatically expire modifiers after duration_ticks
    - Support permanent modifiers (duration_ticks=None)
    - Query active modifiers for entity/stat
    - Manually remove modifiers by ID
    - Enforce max_stacks limits

    Usage:
        tracker = ModifierTracker()
        tracker.track_modifier(modifier=speed_buff, current_tick=100)
        tracker.update(current_tick=150)
        expired = tracker.clear_expired()
        active = tracker.get_active_modifiers(entity_id="player", stat="speed")
    """

    def __init__(self) -> None:
        self._tracked: dict[tuple[EntityID, str], list[TrackedModifier]] = {}
        self._by_id: dict[str, TrackedModifier] = {}

    def track_modifier(self, modifier: Modifier, current_tick: int) -> None:
        """Start tracking a modifier.

        Args:
            modifier: Modifier to track
            current_tick: Current game tick
        """
        expires_tick = None
        if modifier.duration_ticks is not None:
            expires_tick = current_tick + modifier.duration_ticks

        tracked = TrackedModifier(
            modifier=modifier,
            applied_tick=current_tick,
            expires_tick=expires_tick,
        )

        key = (modifier.entity_id, modifier.stat)
        if key not in self._tracked:
            self._tracked[key] = []

        existing = self._tracked[key]
        if modifier.max_stacks is not None:
            same_source = [
                t
                for t in existing
                if t.modifier.source_id == modifier.source_id
                and t.modifier.stat == modifier.stat
            ]
            if len(same_source) >= modifier.max_stacks:
                oldest = min(same_source, key=lambda t: t.applied_tick)
                self._tracked[key].remove(oldest)
                if oldest.modifier.modifier_id:
                    self._by_id.pop(oldest.modifier.modifier_id, None)

        self._tracked[key].append(tracked)

        if modifier.modifier_id:
            self._by_id[modifier.modifier_id] = tracked

    def update(self, current_tick: int) -> list[Modifier]:
        """Update tracker and return expired modifiers.

        Args:
            current_tick: Current game tick

        Returns:
            List of modifiers that expired this tick
        """
        return self.clear_expired(current_tick=current_tick)

    def clear_expired(self, current_tick: int) -> list[Modifier]:
        """Remove expired modifiers and return them.

        Args:
            current_tick: Current game tick

        Returns:
            List of expired modifiers
        """
        expired: list[Modifier] = []

        for key in list(self._tracked.keys()):
            tracked_list = self._tracked[key]
            still_active = []

            for tracked in tracked_list:
                if tracked.is_expired(current_tick=current_tick):
                    expired.append(tracked.modifier)
                    if tracked.modifier.modifier_id:
                        self._by_id.pop(tracked.modifier.modifier_id, None)
                else:
                    still_active.append(tracked)

            if still_active:
                self._tracked[key] = still_active
            else:
                del self._tracked[key]

        return expired

    def get_active_modifiers(self, entity_id: EntityID, stat: str) -> list[Modifier]:
        """Get all active modifiers for entity/stat.

        Args:
            entity_id: Entity to query
            stat: Stat name to query

        Returns:
            List of active modifiers
        """
        key = (entity_id, stat)
        if key not in self._tracked:
            return []
        return [tracked.modifier for tracked in self._tracked[key]]

    def remove_modifier(self, modifier: Modifier | str) -> Modifier | None:
        """Manually remove a modifier by ID or object.

        Args:
            modifier: Modifier object or unique modifier ID string

        Returns:
            Removed modifier, or None if not found
        """
        if isinstance(modifier, str):
            modifier_id: str = modifier
        else:
            if modifier.modifier_id is None:
                return None
            modifier_id = modifier.modifier_id

        if modifier_id not in self._by_id:
            return None

        tracked = self._by_id.pop(modifier_id)
        key = (tracked.modifier.entity_id, tracked.modifier.stat)

        if key in self._tracked:
            self._tracked[key] = [
                t for t in self._tracked[key] if t.modifier.modifier_id != modifier_id
            ]
            if not self._tracked[key]:
                del self._tracked[key]

        return tracked.modifier

    def get_all_modifiers(self) -> list[Modifier]:
        """Get all active modifiers across all entities and stats.

        Returns:
            List of all tracked modifiers
        """
        all_modifiers: list[Modifier] = []
        for tracked_list in self._tracked.values():
            all_modifiers.extend(tracked.modifier for tracked in tracked_list)
        return all_modifiers

    def get_tracked_count(self) -> int:
        """Get total number of tracked modifiers.

        Returns:
            Number of active tracked modifiers
        """
        return sum(len(tracked_list) for tracked_list in self._tracked.values())

    def clear(self) -> None:
        """Remove all tracked modifiers."""
        self._tracked.clear()
        self._by_id.clear()

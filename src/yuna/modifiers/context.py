"""Modifier pipeline context."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yuna.modifiers.config import ModifierConfig
    from yuna.modifiers.modifier import Modifier
    from yuna.types.identifiers import EntityID


class ModifierContext:
    """Context for modifier pipeline processing.

    Carries state through pipeline stages.

    Attributes:
        modifiers: Queue of pending modifiers
        grouped: Modifiers grouped by (entity_id, stat)
        final_values: Final computed values per (entity_id, stat)
        config: Stat configuration
        world: Game world (for entity/component access)
        entity_id: Current entity being evaluated (for condition checking)
        current_tick: Current game tick (for time-based calculations)
    """

    def __init__(
        self,
        modifiers: list[Modifier],
        config: ModifierConfig,
        world: Any | None = None,
        current_tick: int = 0,
    ) -> None:
        self.modifiers = modifiers
        self.grouped: dict[tuple[EntityID, str], list[Modifier]] = {}
        self.final_values: dict[tuple[EntityID, str], float] = {}
        self.config = config
        self.world = world
        self.entity_id: EntityID | None = None
        self.current_tick = current_tick

"""Scene transition implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yuna.scene.scene import Scene


class SceneTransition(ABC):
    """Abstract base class for scene transitions."""

    @abstractmethod
    def execute(self, from_scene: Scene | None, to_scene: Scene) -> None:
        """Execute transition from one scene to another.

        Args:
            from_scene: Scene transitioning from (None if first scene)
            to_scene: Scene transitioning to
        """


class InstantTransition(SceneTransition):
    """Immediate scene switch with no transition effect."""

    def execute(self, from_scene: Scene | None, to_scene: Scene) -> None:
        """Execute instant transition."""


class FadeTransition(SceneTransition):
    """Fade out/in transition between scenes."""

    def __init__(self, duration: float) -> None:
        """Initialize fade transition.

        Args:
            duration: Total fade duration in seconds
        """
        self.duration = duration

    def execute(self, from_scene: Scene | None, to_scene: Scene) -> None:
        """Execute fade transition."""


class CrossfadeTransition(SceneTransition):
    """Blend between scenes with crossfade effect."""

    def __init__(self, duration: float) -> None:
        """Initialize crossfade transition.

        Args:
            duration: Crossfade duration in seconds
        """
        self.duration = duration

    def execute(self, from_scene: Scene | None, to_scene: Scene) -> None:
        """Execute crossfade transition."""

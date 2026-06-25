"""Scene manager for coordinating multiple scenes."""

from __future__ import annotations

from yuna.exceptions import ValidationError
from yuna.scene.scene import Scene
from yuna.scene.transition import InstantTransition, SceneTransition


class SceneNotFoundError(Exception):
    """Raised when scene not found in manager."""


class NoActiveSceneError(Exception):
    """Raised when operation requires active scene but none is set."""


class SceneManager:
    """Manages scene loading, unloading, and transitions.

    Responsibilities:
    - Register and store scenes
    - Manage active scene
    - Handle scene transitions
    - Support additive scene loading
    - Update all loaded scenes
    - Scene lifecycle management

    Usage:
        manager = SceneManager()
        manager.register_scene(scene=main_menu)
        manager.register_scene(scene=gameplay)
        manager.load_scene(scene_name="MainMenu")
        manager.update(delta_time=0.016)
        manager.load_scene(scene_name="Gameplay", transition=FadeTransition(1.0))
    """

    def __init__(self) -> None:
        self._scenes: dict[str, Scene] = {}
        self._active_scene: Scene | None = None
        self._loaded_scenes: list[Scene] = []

    def register_scene(self, scene: Scene) -> None:
        """Register scene with manager.

        Args:
            scene: Scene to register
        """
        self._scenes[scene.name] = scene

    def load_scene(
        self,
        scene_name: str,
        transition: SceneTransition | None = None,
    ) -> None:
        """Load scene as main active scene.

        Unloads all currently loaded scenes before loading new one.

        Args:
            scene_name: Name of scene to load
            transition: Optional transition effect (default: InstantTransition)

        Raises:
            SceneNotFoundError: If scene_name not registered
        """
        if scene_name not in self._scenes:
            raise SceneNotFoundError(f"Scene '{scene_name}' not registered")

        transition_effect = transition or InstantTransition()
        new_scene = self._scenes[scene_name]

        for loaded_scene in self._loaded_scenes[:]:
            loaded_scene.unload()
            self._loaded_scenes.remove(loaded_scene)

        transition_effect.execute(from_scene=self._active_scene, to_scene=new_scene)

        new_scene.load()
        self._active_scene = new_scene
        self._loaded_scenes.append(new_scene)

    def load_scene_additive(self, scene_name: str) -> None:
        """Load additional scene without unloading current scenes.

        Args:
            scene_name: Name of scene to load

        Raises:
            SceneNotFoundError: If scene_name not registered
        """
        if scene_name not in self._scenes:
            raise SceneNotFoundError(f"Scene '{scene_name}' not registered")

        scene = self._scenes[scene_name]
        if scene not in self._loaded_scenes:
            scene.load()
            self._loaded_scenes.append(scene)

    def unload_scene(self, scene_name: str) -> None:
        """Unload additive scene.

        Cannot unload the active scene.

        Args:
            scene_name: Name of scene to unload

        Raises:
            SceneNotFoundError: If scene_name not registered
            ValidationError: If trying to unload active scene
        """
        if scene_name not in self._scenes:
            raise SceneNotFoundError(f"Scene '{scene_name}' not registered")

        scene = self._scenes[scene_name]

        if scene == self._active_scene:
            raise ValidationError(
                field="scene_name",
                value=scene_name,
                reason="Cannot unload active scene. Use load_scene() instead",
            )

        if scene in self._loaded_scenes:
            scene.unload()
            self._loaded_scenes.remove(scene)

    def get_active_scene(self) -> Scene:
        """Get current main active scene.

        Returns:
            Active scene

        Raises:
            NoActiveSceneError: If no scene is active
        """
        if self._active_scene is None:
            raise NoActiveSceneError("No active scene")
        return self._active_scene

    def get_loaded_scenes(self) -> list[Scene]:
        """Get all currently loaded scenes.

        Returns:
            List of loaded scenes (active scene first)
        """
        return self._loaded_scenes.copy()

    def update(self, delta_time: float) -> None:
        """Update all loaded scenes.

        Args:
            delta_time: Time elapsed since last update in seconds
        """
        for scene in self._loaded_scenes:
            scene.update(delta_time=delta_time)

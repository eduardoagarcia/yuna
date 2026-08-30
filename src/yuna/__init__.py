"""Yuna — a fast, dependency-light ECS game engine for Python.

The most common entrypoints are re-exported here for convenience::

    from yuna import ECSWorld, Component, System

Every subsystem remains importable from its submodule (e.g.
``from yuna.physics.engine import PhysicsEngine``).
"""

from yuna.ecs.component import Component
from yuna.ecs.system import System
from yuna.ecs.world import ECSWorld
from yuna.events.bus import EventBus
from yuna.loop.game_loop import GameLoop
from yuna.loop.scheduler import SystemScheduler
from yuna.loop.time import TimeManager

__version__ = "1.1.1"

__all__ = [
    "Component",
    "ECSWorld",
    "EventBus",
    "GameLoop",
    "System",
    "SystemScheduler",
    "TimeManager",
    "__version__",
]

"""Platform Core Engine: scenario contracts, context container, registry, and menu navigation."""

from .context import ExecutionContext
from .base_scenario import BaseScenario
from .registry import registry, register_scenario
from .menu_manager import MenuManager

__all__ = [
    "ExecutionContext",
    "BaseScenario",
    "registry",
    "register_scenario",
    "MenuManager",
]

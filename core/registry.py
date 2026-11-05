"""Scenario registry and discovery engine.

Allows decoupled registration of test scenarios across domain modules.
"""

import importlib
import pkgutil
from typing import Dict, List, Type, Optional, Tuple
from core.base_scenario import BaseScenario
from reporting.logger import get_logger

logger = get_logger("registry")

CATEGORY_METADATA = {
    "account_management": {
        "name": "Account Management",
        "description": "Create, Enable, Disable, and Unlock Target Accounts",
        "order": 1,
    },
    "lifecycle_management": {
        "name": "Lifecycle State Management",
        "description": "Active, LOA, SKP, Termination, and Full Lifecycle Demo",
        "order": 2,
    },
    "access_management": {
        "name": "Access & Entitlement Management",
        "description": "Role Requests with Source Validation and Entitlement Checks",
        "order": 3,
    },
    "inspection": {
        "name": "Identity & Account Inspection",
        "description": "Identity Details, Correlated Accounts, and Raw Inbound Attributes",
        "order": 4,
    },
}


class ScenarioRegistry:
    """Central registry holding all available test scenarios."""

    def __init__(self):
        self._scenarios_by_id: Dict[str, BaseScenario] = {}
        self._scenarios_by_category: Dict[str, List[BaseScenario]] = {}
        self._legacy_map: Dict[int, str] = {
            1: "account.create",
            2: "account.enable",
            3: "account.disable",
            4: "access.role_request",
            5: "lifecycle.termination",
            6: "lifecycle.loa",
            7: "lifecycle.skp",
            8: "lifecycle.ear",
            9: "lifecycle.full_demo",
            10: "inspection.view_accounts",
        }

    def register(self, scenario_cls: Type[BaseScenario]) -> Type[BaseScenario]:
        """Register a scenario class."""
        instance = scenario_cls()
        sid = instance.scenario_id
        cat_id = instance.category_id

        self._scenarios_by_id[sid] = instance

        if cat_id not in self._scenarios_by_category:
            self._scenarios_by_category[cat_id] = []
        
        # Avoid duplicate registration
        self._scenarios_by_category[cat_id] = [
            s for s in self._scenarios_by_category[cat_id] if s.scenario_id != sid
        ]
        self._scenarios_by_category[cat_id].append(instance)
        self._scenarios_by_category[cat_id].sort(key=lambda s: s.order)

        logger.debug(f"Registered scenario '{instance.name}' ({sid}) in category '{cat_id}'")
        return scenario_cls

    def get_categories(self) -> List[Tuple[str, str, str]]:
        """Get sorted list of (category_id, display_name, description)."""
        categories = []
        for cat_id in self._scenarios_by_category.keys():
            meta = CATEGORY_METADATA.get(cat_id, {
                "name": cat_id.replace("_", " ").title(),
                "description": "",
                "order": 99,
            })
            categories.append((cat_id, meta["name"], meta["description"], meta.get("order", 99)))
        categories.sort(key=lambda c: c[3])
        return [(c[0], c[1], c[2]) for c in categories]

    def get_scenarios_for_category(self, category_id: str) -> List[BaseScenario]:
        """Get all scenarios registered under a specific category."""
        return self._scenarios_by_category.get(category_id, [])

    def get_scenario_by_id(self, scenario_id: str) -> Optional[BaseScenario]:
        """Look up a scenario by unique ID slug."""
        return self._scenarios_by_id.get(scenario_id)

    def get_scenario_by_legacy_number(self, num: int) -> Optional[BaseScenario]:
        """Map legacy scenario number (1-10) to scenario instance."""
        sid = self._legacy_map.get(num)
        return self.get_scenario_by_id(sid) if sid else None

    def auto_discover(self, base_package: str = "scenarios") -> None:
        """Dynamically discover and import all scenario modules in the scenarios package."""
        try:
            pkg = importlib.import_module(base_package)
            if hasattr(pkg, "__path__"):
                for _, modname, ispkg in pkgutil.walk_packages(pkg.__path__, prefix=f"{base_package}."):
                    try:
                        importlib.import_module(modname)
                    except Exception as e:
                        logger.warning(f"Could not load scenario module '{modname}': {e}")
        except ModuleNotFoundError:
            logger.debug(f"Base package '{base_package}' not found for auto-discovery.")


# Global registry singleton
registry = ScenarioRegistry()


def register_scenario(cls: Type[BaseScenario]) -> Type[BaseScenario]:
    """Decorator to register a scenario with the global registry."""
    return registry.register(cls)

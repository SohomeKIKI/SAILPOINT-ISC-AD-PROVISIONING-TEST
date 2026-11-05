"""Test scenarios package for SailPoint ISC AD Provisioning automation.

Maintains backward-compatible exports forwarding to the new domain-isolated modules in `scenarios/`.
"""

from scenarios.account_management import (
    run_create_account,
    run_enable_account,
    run_disable_account,
    run_unlock_account,
)
from scenarios.lifecycle_management import (
    run_active_lifecycle,
    run_leave_of_absence,
    run_skp,
    run_emergency_access_removal,
    run_termination,
    run_full_lifecycle_demo,
)
from scenarios.access_management import (
    run_role_request,
)
from scenarios.inspection import (
    ViewIdentityDetailsScenario,
    ViewCorrelatedAccountsScenario,
    ViewSourceAttributesScenario,
    ViewEventAttributesScenario,
)

__all__ = [
    "run_create_account",
    "run_enable_account",
    "run_disable_account",
    "run_unlock_account",
    "run_active_lifecycle",
    "run_leave_of_absence",
    "run_skp",
    "run_emergency_access_removal",
    "run_termination",
    "run_full_lifecycle_demo",
    "run_role_request",
    "ViewIdentityDetailsScenario",
    "ViewCorrelatedAccountsScenario",
    "ViewSourceAttributesScenario",
    "ViewEventAttributesScenario",
]

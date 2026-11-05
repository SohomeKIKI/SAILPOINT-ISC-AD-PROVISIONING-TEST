"""Domain-isolated scenarios package for SailPoint testing platform."""

from core.registry import registry

# Import domain modules to trigger registration
from .account_management import (
    CreateAccountScenario,
    EnableAccountScenario,
    DisableAccountScenario,
    UnlockAccountScenario,
    run_create_account,
    run_enable_account,
    run_disable_account,
    run_unlock_account,
)
from .lifecycle_management import (
    ActiveLifecycleScenario,
    LeaveOfAbsenceScenario,
    SabbaticalSKPScenario,
    EmergencyAccessRemovalScenario,
    EmploymentTerminationScenario,
    FullLifecycleDemoScenario,
    run_active_lifecycle,
    run_leave_of_absence,
    run_skp,
    run_emergency_access_removal,
    run_termination,
    run_full_lifecycle_demo,
)
from .access_management import (
    RoleRequestScenario,
    run_role_request,
)
from .inspection import (
    ViewIdentityDetailsScenario,
    ViewCorrelatedAccountsScenario,
    ViewSourceAttributesScenario,
    ViewEventAttributesScenario,
)

__all__ = [
    # Account Management
    "CreateAccountScenario",
    "EnableAccountScenario",
    "DisableAccountScenario",
    "UnlockAccountScenario",
    "run_create_account",
    "run_enable_account",
    "run_disable_account",
    "run_unlock_account",
    # Lifecycle Management
    "ActiveLifecycleScenario",
    "LeaveOfAbsenceScenario",
    "SabbaticalSKPScenario",
    "EmergencyAccessRemovalScenario",
    "EmploymentTerminationScenario",
    "FullLifecycleDemoScenario",
    "run_active_lifecycle",
    "run_leave_of_absence",
    "run_skp",
    "run_emergency_access_removal",
    "run_termination",
    "run_full_lifecycle_demo",
    # Access Management
    "RoleRequestScenario",
    "run_role_request",
    # Inspection
    "ViewIdentityDetailsScenario",
    "ViewCorrelatedAccountsScenario",
    "ViewSourceAttributesScenario",
    "ViewEventAttributesScenario",
]

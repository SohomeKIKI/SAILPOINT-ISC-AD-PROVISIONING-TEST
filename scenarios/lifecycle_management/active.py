"""Scenario: Active Lifecycle State.
Domain: Lifecycle State Management.
"""

from typing import Dict, Any, Optional
from config.constants import LIFECYCLE_STATES
from core.base_scenario import BaseScenario
from core.context import ExecutionContext
from core.registry import register_scenario
from sailpoint.lifecycle import apply_lifecycle_state
from validation.identity_validation import validate_identity_state
from validation.account_validation import validate_account_exists, validate_account_status
from validation.provisioning_validation import validate_provisioning_activity, check_downstream_provisioning
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("scenario.lifecycle.active")


@register_scenario
class ActiveLifecycleScenario(BaseScenario):
    """Test transition to Active lifecycle state."""

    scenario_id = "lifecycle.active"
    name = "Active (Onboarding / Rehire)"
    category_id = "lifecycle_management"
    category_name = "Lifecycle State Management"
    description = "Apply 'active' lifecycle state and verify AD account enablement"
    expected_ad_outcome = "Enable and provision standard Active Directory access"
    order = 1

    def execute(self, ctx: ExecutionContext) -> TestReportItem:
        return run_active_lifecycle(
            identity=ctx.identity,
            source=ctx.source,
            profile_id=ctx.effective_profile_id,
            interactive=ctx.interactive,
            force_confirmed=ctx.force_confirmed,
        )


def run_active_lifecycle(
    identity: Dict[str, Any],
    source: Dict[str, Any],
    profile_id: Optional[str] = None,
    interactive: bool = True,
    force_confirmed: bool = False,
) -> TestReportItem:
    """Execute Active lifecycle state scenario."""
    scenario_name = "Active Lifecycle State"
    identity_id = identity.get("id")
    identity_name = identity.get("displayName") or identity.get("name")
    source_id = source.get("id")
    source_name = source.get("name")
    effective_profile_id = profile_id or identity.get("identityProfileId")

    logger.info(f"=== Starting Scenario: {scenario_name} for '{identity_name}' on source '{source_name}' ===")

    report = TestReportItem(
        scenario=scenario_name,
        identity_id=identity_id,
        identity_name=identity_name,
        identity_email=identity.get("email"),
        identity_profile_id=effective_profile_id,
        identity_profile_name=identity.get("identityProfileName"),
        source_id=source_id,
        source_name=source_name,
        initial_lifecycle_state=identity.get("lifecycleState"),
        target_lifecycle_state=LIFECYCLE_STATES["ACTIVE"],
    )

    # 1. Apply 'active' lifecycle state
    state_result = apply_lifecycle_state(
        identity_id=identity_id,
        profile_id=effective_profile_id,
        target_state_key=LIFECYCLE_STATES["ACTIVE"],
    )
    report.api_operations.append({
        "operation": "set_lifecycle_state",
        "target_state": LIFECYCLE_STATES["ACTIVE"],
        "result": state_result,
    })

    account_activity_id = state_result.get("account_activity_id")

    # 2. Validation: Verify Provisioning Activity (wait for task completion)
    if account_activity_id:
        prov_check = validate_provisioning_activity(account_activity_id)
        report.validation_checks.append(prov_check)

    # 3. Validation: Verify Identity Lifecycle State matches 'active'
    id_check = validate_identity_state(identity_id, expected_state=LIFECYCLE_STATES["ACTIVE"])
    report.validation_checks.append(id_check)
    report.resulting_lifecycle_state = id_check.get("actual_state")

    # 4. Validation: Verify Account on Target Source is Enabled
    acc_check = validate_account_exists(identity_id, source_id, source_name)
    report.validation_checks.append(acc_check)

    account_status = None
    if acc_check.get("passed"):
        status_check = validate_account_status(identity_id, source_id, "Enabled", source_name)
        report.validation_checks.append(status_check)
        account_status = status_check.get("actual_status")

    # 5. Validation: Downstream Provisioning Evaluation
    downstream_check = check_downstream_provisioning(
        identity_id=identity_id,
        source_name=source_name,
        expected_ad_outcome="Enable and provision standard Active Directory access",
        account_status=account_status,
    )
    report.validation_checks.append(downstream_check)

    # Core criteria: Lifecycle state successfully applied and verified on identity
    core_passed = bool(state_result.get("success") and id_check.get("passed"))
    report.final_status = "SUCCESS" if core_passed else "FAILURE"
    if not state_result.get("success"):
        report.error_message = state_result.get("error")
    elif not id_check.get("passed"):
        report.error_message = id_check.get("details")

    logger.info(f"=== Completed Scenario: {scenario_name} | Outcome: {report.final_status} ===")
    return report

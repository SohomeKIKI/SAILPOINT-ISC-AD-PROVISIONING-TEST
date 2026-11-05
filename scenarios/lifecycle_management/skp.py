"""Scenario: Sabbatical (SKP).
Domain: Lifecycle State Management.
"""

from typing import Dict, Any, Optional
from config.constants import SCENARIOS, LIFECYCLE_STATES
from core.base_scenario import BaseScenario
from core.context import ExecutionContext
from core.registry import register_scenario
from sailpoint.lifecycle import apply_lifecycle_state
from validation.identity_validation import validate_identity_state
from validation.account_validation import validate_account_exists, validate_account_status
from validation.provisioning_validation import validate_provisioning_activity, check_downstream_provisioning
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("scenario.lifecycle.skp")


@register_scenario
class SabbaticalSKPScenario(BaseScenario):
    """Test transition to Sabbatical (SKP) lifecycle state."""

    scenario_id = "lifecycle.skp"
    name = "Sabbatical - SKP"
    category_id = "lifecycle_management"
    category_name = "Lifecycle State Management"
    description = "Apply 'skp' state, suspend target account and retain identity attributes"
    expected_ad_outcome = "Suspend the AD account according to tenant configuration; retain attributes"
    order = 3

    def execute(self, ctx: ExecutionContext) -> TestReportItem:
        return run_skp(
            identity=ctx.identity,
            source=ctx.source,
            profile_id=ctx.effective_profile_id,
            interactive=ctx.interactive,
            force_confirmed=ctx.force_confirmed,
        )


def run_skp(
    identity: Dict[str, Any],
    source: Dict[str, Any],
    profile_id: Optional[str] = None,
    interactive: bool = True,
    force_confirmed: bool = False,
) -> TestReportItem:
    """Execute Sabbatical (SKP) test scenario following the 8-step process."""
    scenario_name = SCENARIOS["SKP"]
    identity_id = identity.get("id")
    identity_name = identity.get("displayName") or identity.get("name")
    source_id = source.get("id")
    source_name = source.get("name")
    effective_profile_id = profile_id or identity.get("identityProfileId")

    logger.info(f"=== Starting Scenario: {scenario_name} for '{identity_name}' on source '{source_name}' ===")

    # Step 1 & 2: Receive identity and record current lifecycle state
    initial_state = identity.get("lifecycleState")

    report = TestReportItem(
        scenario=scenario_name,
        identity_id=identity_id,
        identity_name=identity_name,
        identity_email=identity.get("email"),
        identity_profile_id=effective_profile_id,
        identity_profile_name=identity.get("identityProfileName"),
        source_id=source_id,
        source_name=source_name,
        initial_lifecycle_state=initial_state,
        target_lifecycle_state=LIFECYCLE_STATES["SKP"],
    )

    # Step 3: Confirm identity eligibility
    if initial_state == "skp":
        logger.info(f"Notice: Identity '{identity_name}' is already in 'skp' state.")

    # Step 4: Ask tester to confirm the SKP operation
    if not force_confirmed and interactive:
        print("\n" + "-" * 75)
        print("  SABBATICAL (SKP) CONFIRMATION")
        print(f"  Target User   : {identity_name}")
        print(f"  Current State : {initial_state}")
        print(f"  Target Source : {source_name}")
        print("  AD Outcome    : Suspend AD account, retain attributes.")
        print("-" * 75)
        ans = input("Proceed with applying SKP lifecycle state? (y/n): ").strip().lower()
        if ans != "y":
            report.final_status = "FAILURE"
            report.error_message = "SKP scenario cancelled by tester."
            return report

    # Step 5: Apply configured SKP lifecycle state through ISC
    state_result = apply_lifecycle_state(
        identity_id=identity_id,
        profile_id=effective_profile_id,
        target_state_key=LIFECYCLE_STATES["SKP"],
    )
    report.api_operations.append({
        "operation": "set_lifecycle_state",
        "target_state": LIFECYCLE_STATES["SKP"],
        "result": state_result,
    })
    account_activity_id = state_result.get("account_activity_id")

    # Step 6: Check provisioning activity (wait for async task to complete)
    if account_activity_id:
        prov_check = validate_provisioning_activity(account_activity_id)
        report.validation_checks.append(prov_check)

    # Step 7: Check resulting identity state
    id_check = validate_identity_state(identity_id, expected_state=LIFECYCLE_STATES["SKP"])
    report.validation_checks.append(id_check)
    report.resulting_lifecycle_state = id_check.get("actual_state")

    # Validate target account on source (suspended/disabled)
    acc_check = validate_account_exists(identity_id, source_id, source_name)
    report.validation_checks.append(acc_check)

    account_status = None
    if acc_check.get("passed"):
        status_check = validate_account_status(identity_id, source_id, "Disabled", source_name)
        report.validation_checks.append(status_check)
        account_status = status_check.get("actual_status")

    downstream_check = check_downstream_provisioning(
        identity_id=identity_id,
        source_name=source_name,
        expected_ad_outcome="Suspend the AD account according to tenant configuration; retain attributes",
        account_status=account_status,
    )
    report.validation_checks.append(downstream_check)

    # Step 8: Record outcome in log
    core_passed = bool(state_result.get("success") and id_check.get("passed"))
    report.final_status = "SUCCESS" if core_passed else "FAILURE"
    if not state_result.get("success"):
        report.error_message = state_result.get("error")
    elif not id_check.get("passed"):
        report.error_message = id_check.get("details")

    logger.info(f"=== Completed Scenario: {scenario_name} | Outcome: {report.final_status} ===")
    return report

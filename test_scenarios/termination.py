"""Test Scenario: Employment Termination.
Safety: Requires explicit confirmation before applying.
Expected AD Outcome: Disable or remove the AD account, revoke all access, and initiate deprovisioning.
Resulting Lifecycle State: employmentTermination (or employementTermination / terminated).
"""

from typing import Dict, Any, Optional
from config.constants import SCENARIOS, LIFECYCLE_STATES
from sailpoint.lifecycle import apply_lifecycle_state
from validation.identity_validation import validate_identity_state
from validation.account_validation import validate_account_exists, validate_account_status
from validation.provisioning_validation import validate_provisioning_activity, check_downstream_provisioning
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("scenario.termination")


def run_termination(
    identity: Dict[str, Any],
    source: Dict[str, Any],
    profile_id: Optional[str] = None,
    interactive: bool = True,
    force_confirmed: bool = False,
) -> TestReportItem:
    """Execute Employment Termination test scenario with mandatory safety confirmation."""
    scenario_name = SCENARIOS["TERMINATION"]
    identity_id = identity.get("id")
    identity_name = identity.get("displayName") or identity.get("name")
    source_id = source.get("id")
    source_name = source.get("name")
    effective_profile_id = profile_id or identity.get("identityProfileId")

    logger.info(f"=== Starting Scenario: {scenario_name} for '{identity_name}' ===")

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
        target_lifecycle_state=LIFECYCLE_STATES["TERMINATION"],
    )

    # Safety Confirmation Check
    if not force_confirmed and interactive:
        print("\n" + "!" * 75)
        print("  CRITICAL OPERATION CONFIRMATION: EMPLOYMENT TERMINATION")
        print(f"  Target User   : {identity_name} ({identity.get('email')})")
        print(f"  Target Source : {source_name}")
        print("  Downstream AD : Disable/remove account, revoke all access, and deprovision.")
        print("!" * 75)
        confirm = input("Type 'TERMINATE' to confirm execution (or anything else to cancel): ").strip()
        if confirm != "TERMINATE":
            print("Termination cancelled by tester.")
            report.final_status = "FAILURE"
            report.error_message = "Operation aborted by tester during safety confirmation."
            return report

    # 1. Apply Termination Lifecycle State
    state_result = apply_lifecycle_state(
        identity_id=identity_id,
        profile_id=effective_profile_id,
        target_state_key=LIFECYCLE_STATES["TERMINATION"],
    )
    report.api_operations.append({
        "operation": "set_lifecycle_state",
        "target_state": LIFECYCLE_STATES["TERMINATION"],
        "result": state_result,
    })
    account_activity_id = state_result.get("account_activity_id")

    # 2. Validation: Verify Provisioning Activity (wait for task completion)
    if account_activity_id:
        prov_check = validate_provisioning_activity(account_activity_id)
        report.validation_checks.append(prov_check)

    # 3. Validation: Verify Identity Lifecycle State matches termination
    id_check = validate_identity_state(identity_id, expected_state=LIFECYCLE_STATES["TERMINATION"])
    report.validation_checks.append(id_check)
    report.resulting_lifecycle_state = id_check.get("actual_state")

    # 4. Validation: Verify Account on Target Source is Disabled or Deprovisioned
    acc_check = validate_account_exists(identity_id, source_id, source_name)
    report.validation_checks.append(acc_check)

    account_status = None
    if acc_check.get("passed"):
        status_check = validate_account_status(identity_id, source_id, "Disabled", source_name)
        report.validation_checks.append(status_check)
        account_status = status_check.get("actual_status")
    else:
        # If account was deprovisioned/deleted from target, that also satisfies termination
        report.validation_checks.append({
            "check": "Account Deprovisioning Verification",
            "passed": True,
            "details": "Account no longer present on source (deprovisioned as expected).",
        })

    # 5. Validation: Downstream Provisioning Evaluation
    downstream_check = check_downstream_provisioning(
        identity_id=identity_id,
        source_name=source_name,
        expected_ad_outcome="Disable or remove the AD account and revoke all access",
        account_status=account_status,
    )
    report.validation_checks.append(downstream_check)

    # Core criteria: Termination lifecycle state successfully applied and verified on identity
    core_passed = bool(state_result.get("success") and id_check.get("passed"))
    report.final_status = "SUCCESS" if core_passed else "FAILURE"
    if not state_result.get("success"):
        report.error_message = state_result.get("error")
    elif not id_check.get("passed"):
        report.error_message = id_check.get("details")

    logger.info(f"=== Completed Scenario: {scenario_name} | Outcome: {report.final_status} ===")
    return report


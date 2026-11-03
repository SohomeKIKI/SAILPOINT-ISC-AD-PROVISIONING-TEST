"""Test Scenario: Emergency Access Removal (EAR).
Safety: High-impact security event. Requires explicit confirmation and non-production check.
Expected AD Outcome: Immediately disable the AD account and revoke critical access; preserve identity for review.
Resulting Lifecycle State: ear.
"""

from typing import Dict, Any, Optional
from config.constants import SCENARIOS, LIFECYCLE_STATES
from sailpoint.lifecycle import apply_lifecycle_state
from validation.identity_validation import validate_identity_state
from validation.account_validation import validate_account_exists, validate_account_status
from validation.provisioning_validation import validate_provisioning_activity, check_downstream_provisioning
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("scenario.ear")


def run_emergency_access_removal(
    identity: Dict[str, Any],
    source: Dict[str, Any],
    profile_id: Optional[str] = None,
    interactive: bool = True,
    force_confirmed: bool = False,
) -> TestReportItem:
    """Execute Emergency Access Removal (EAR) test scenario with mandatory safety prompts."""
    scenario_name = SCENARIOS["EAR"]
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
        target_lifecycle_state=LIFECYCLE_STATES["EAR"],
    )

    # Mandatory Safety Prompt
    if not force_confirmed and interactive:
        print("\n" + "#" * 75)
        print("  SECURITY ALERT: EMERGENCY ACCESS REMOVAL (EAR) INITIATION")
        print("  NOTICE: EAR is a high-impact operation designed for security emergencies.")
        print("  Handover rule: EAR must only be tested in non-production sandbox environments.")
        print(f"  Target User   : {identity_name} ({identity.get('email')})")
        print(f"  Target Source : {source_name}")
        print("  Action        : Instantly disable account & revoke critical permissions.")
        print("#" * 75)
        confirm = input("Type 'EAR-CONFIRM' to authorize emergency access removal (or 'c' to cancel): ").strip()
        if confirm != "EAR-CONFIRM":
            print("EAR operation cancelled by tester.")
            report.final_status = "FAILURE"
            report.error_message = "EAR cancelled by tester during emergency confirmation prompt."
            return report

    # 1. Apply 'ear' lifecycle state
    state_result = apply_lifecycle_state(
        identity_id=identity_id,
        profile_id=effective_profile_id,
        target_state_key=LIFECYCLE_STATES["EAR"],
    )
    report.api_operations.append({
        "operation": "set_lifecycle_state",
        "target_state": LIFECYCLE_STATES["EAR"],
        "result": state_result,
    })
    account_activity_id = state_result.get("account_activity_id")

    # 2. Validation: Verify Provisioning Activity (wait for task completion)
    if account_activity_id:
        prov_check = validate_provisioning_activity(account_activity_id)
        report.validation_checks.append(prov_check)

    # 3. Validation: Verify Identity Lifecycle State matches 'ear'
    id_check = validate_identity_state(identity_id, expected_state=LIFECYCLE_STATES["EAR"])
    report.validation_checks.append(id_check)
    report.resulting_lifecycle_state = id_check.get("actual_state")

    # 4. Validation: Verify Account on Target Source is Disabled Immediately
    acc_check = validate_account_exists(identity_id, source_id, source_name)
    report.validation_checks.append(acc_check)

    account_status = None
    if acc_check.get("passed"):
        status_check = validate_account_status(identity_id, source_id, "Disabled", source_name)
        report.validation_checks.append(status_check)
        account_status = status_check.get("actual_status")

    # 5. Validation: Downstream Provisioning Evaluation
    downstream_check = check_downstream_provisioning(
        identity_id=identity_id,
        source_name=source_name,
        expected_ad_outcome="Immediately disable the AD account and revoke critical access",
        account_status=account_status,
    )
    report.validation_checks.append(downstream_check)

    # Core criteria: EAR lifecycle state successfully applied and verified on identity
    core_passed = bool(state_result.get("success") and id_check.get("passed"))
    report.final_status = "SUCCESS" if core_passed else "FAILURE"
    if not state_result.get("success"):
        report.error_message = state_result.get("error")
    elif not id_check.get("passed"):
        report.error_message = id_check.get("details")

    logger.info(f"=== Completed Scenario: {scenario_name} | Outcome: {report.final_status} ===")
    return report


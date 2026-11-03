"""Test Scenario: Enable Account.
Expected AD Outcome: Enable an existing AD account.
Resulting Lifecycle State: active.
"""

from typing import Dict, Any, Optional
from config.constants import SCENARIOS, LIFECYCLE_STATES
from sailpoint.lifecycle import apply_lifecycle_state
from sailpoint.accounts import get_account_on_source, enable_account
from validation.identity_validation import validate_identity_state
from validation.account_validation import validate_account_exists, validate_account_status
from validation.provisioning_validation import validate_provisioning_activity, check_downstream_provisioning
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("scenario.enable_account")


def run_enable_account(
    identity: Dict[str, Any],
    source: Dict[str, Any],
    profile_id: Optional[str] = None,
    interactive: bool = True,
    force_confirmed: bool = False,
) -> TestReportItem:
    """Execute Enable Account test scenario."""
    scenario_name = SCENARIOS["ENABLE_ACCOUNT"]
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

    # 1. Apply 'active' lifecycle state if not already active
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

    # 2. If account exists on source, invoke explicit Enable Account API
    account = get_account_on_source(identity_id, source_id)
    if account and account.get("id"):
        enable_res = enable_account(account.get("id"))
        report.api_operations.append({
            "operation": "enable_account",
            "account_id": account.get("id"),
            "result": enable_res,
        })

    # 3. Validation: Verify Provisioning Activity (wait for task completion)
    if account_activity_id:
        prov_check = validate_provisioning_activity(account_activity_id)
        report.validation_checks.append(prov_check)

    # 4. Validation: Verify Identity Lifecycle State
    id_check = validate_identity_state(identity_id, expected_state=LIFECYCLE_STATES["ACTIVE"])
    report.validation_checks.append(id_check)
    report.resulting_lifecycle_state = id_check.get("actual_state")

    # 5. Validation: Verify Account Status
    acc_check = validate_account_exists(identity_id, source_id, source_name)
    report.validation_checks.append(acc_check)

    account_status = None
    if acc_check.get("passed"):
        status_check = validate_account_status(identity_id, source_id, "Enabled", source_name)
        report.validation_checks.append(status_check)
        account_status = status_check.get("actual_status")

    # 6. Validation: Downstream Provisioning
    downstream_check = check_downstream_provisioning(
        identity_id=identity_id,
        source_name=source_name,
        expected_ad_outcome="Enable an existing AD account",
        account_status=account_status,
    )
    report.validation_checks.append(downstream_check)

    # Determine final outcome
    core_passed = bool(state_result.get("success") and id_check.get("passed"))
    report.final_status = "SUCCESS" if core_passed else "FAILURE"
    if not state_result.get("success"):
        report.error_message = state_result.get("error")
    elif not id_check.get("passed"):
        report.error_message = id_check.get("details")

    logger.info(f"=== Completed Scenario: {scenario_name} | Outcome: {report.final_status} ===")
    return report


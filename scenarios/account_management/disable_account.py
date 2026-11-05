"""Scenario: Disable Account.
Domain: Account Management.
"""

from typing import Dict, Any, Optional
from config.constants import SCENARIOS, LIFECYCLE_STATES
from core.base_scenario import BaseScenario
from core.context import ExecutionContext
from core.registry import register_scenario
from sailpoint.lifecycle import apply_lifecycle_state
from sailpoint.accounts import get_account_on_source, disable_account
from validation.identity_validation import validate_identity_state
from validation.account_validation import validate_account_exists, validate_account_status
from validation.provisioning_validation import validate_provisioning_activity, check_downstream_provisioning
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("scenario.account.disable")


@register_scenario
class DisableAccountScenario(BaseScenario):
    """Test disabling a target account on the source."""

    scenario_id = "account.disable"
    name = "Disable Account"
    category_id = "account_management"
    category_name = "Account Management"
    description = "Suspend target account on source and verify disabled status"
    expected_ad_outcome = "Disable the AD account"
    order = 3

    def execute(self, ctx: ExecutionContext) -> TestReportItem:
        return run_disable_account(
            identity=ctx.identity,
            source=ctx.source,
            profile_id=ctx.effective_profile_id,
            interactive=ctx.interactive,
            force_confirmed=ctx.force_confirmed,
        )


def run_disable_account(
    identity: Dict[str, Any],
    source: Dict[str, Any],
    profile_id: Optional[str] = None,
    target_state: str = LIFECYCLE_STATES["LOA"],
    interactive: bool = True,
    force_confirmed: bool = False,
) -> TestReportItem:
    """Execute Disable Account test scenario."""
    scenario_name = SCENARIOS["DISABLE_ACCOUNT"]
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
        target_lifecycle_state=target_state,
    )

    # 1. Apply configured disable lifecycle state (loa)
    state_result = apply_lifecycle_state(
        identity_id=identity_id,
        profile_id=effective_profile_id,
        target_state_key=target_state,
    )
    report.api_operations.append({
        "operation": "set_lifecycle_state",
        "target_state": target_state,
        "result": state_result,
    })

    account_activity_id = state_result.get("account_activity_id")

    # 2. Directly send disable account operation if account exists
    account = get_account_on_source(identity_id, source_id)
    if account:
        acc_id = account.get("id")
        disable_res = disable_account(acc_id)
        report.api_operations.append({
            "operation": "disable_account",
            "account_id": acc_id,
            "result": disable_res,
        })

    # 3. Validation: Verify Provisioning Activity (wait for task completion)
    if account_activity_id:
        prov_check = validate_provisioning_activity(account_activity_id)
        report.validation_checks.append(prov_check)

    # 4. Validation: Verify Identity Lifecycle State
    id_check = validate_identity_state(identity_id, expected_state=target_state)
    report.validation_checks.append(id_check)
    report.resulting_lifecycle_state = id_check.get("actual_state")

    # 5. Validation: Verify Account Status is Disabled
    acc_check = validate_account_exists(identity_id, source_id, source_name)
    report.validation_checks.append(acc_check)

    account_status = None
    if acc_check.get("passed"):
        status_check = validate_account_status(identity_id, source_id, "Disabled", source_name)
        report.validation_checks.append(status_check)
        account_status = status_check.get("actual_status")

    # 6. Validation: Downstream Provisioning
    downstream_check = check_downstream_provisioning(
        identity_id=identity_id,
        source_name=source_name,
        expected_ad_outcome="Disable the AD account",
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


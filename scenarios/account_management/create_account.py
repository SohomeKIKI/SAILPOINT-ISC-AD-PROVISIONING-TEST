"""Scenario: Create Target Account.
Domain: Account Management.
"""

from typing import Dict, Any, Optional
from config.constants import SCENARIOS, LIFECYCLE_STATES
from core.base_scenario import BaseScenario
from core.context import ExecutionContext
from core.registry import register_scenario
from sailpoint.lifecycle import apply_lifecycle_state
from sailpoint.accounts import get_account_on_source, create_account
from validation.identity_validation import validate_identity_state
from validation.account_validation import validate_account_exists, validate_account_status
from validation.provisioning_validation import validate_provisioning_activity, check_downstream_provisioning
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("scenario.account.create")


@register_scenario
class CreateAccountScenario(BaseScenario):
    """Test creating and enabling an account on the target source."""

    scenario_id = "account.create"
    name = "Create Target Account"
    category_id = "account_management"
    category_name = "Account Management"
    description = "Provision a new account on target AD source and verify enable status"
    expected_ad_outcome = "Create and enable a new AD account on the target source"
    order = 1

    def execute(self, ctx: ExecutionContext) -> TestReportItem:
        return run_create_account(
            identity=ctx.identity,
            source=ctx.source,
            profile_id=ctx.effective_profile_id,
            interactive=ctx.interactive,
            force_confirmed=ctx.force_confirmed,
        )


def run_create_account(
    identity: Dict[str, Any],
    source: Dict[str, Any],
    profile_id: Optional[str] = None,
    interactive: bool = True,
    force_confirmed: bool = False,
) -> TestReportItem:
    """Execute Create Account test scenario."""
    scenario_name = SCENARIOS["CREATE_ACCOUNT"]
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

    # 1. Apply 'active' lifecycle state to trigger onboarding/creation policy
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

    # 2. Check if direct account creation is needed if no account exists yet on target source
    existing_account = get_account_on_source(identity_id, source_id)
    if not existing_account:
        account_attrs = {
            "sAMAccountName": (identity.get("email") or identity_name).split("@")[0].replace(" ", ".").lower(),
            "displayName": identity_name,
            "mail": identity.get("email"),
        }
        create_res = create_account(source_id, account_attrs)
        report.api_operations.append({
            "operation": "create_account",
            "attributes": account_attrs,
            "result": create_res,
        })

    # 3. Validation: Verify Provisioning Activity (wait for task completion)
    if account_activity_id:
        prov_check = validate_provisioning_activity(account_activity_id)
        report.validation_checks.append(prov_check)

    # 4. Validation: Verify Identity Lifecycle State
    id_check = validate_identity_state(identity_id, expected_state=LIFECYCLE_STATES["ACTIVE"])
    report.validation_checks.append(id_check)
    report.resulting_lifecycle_state = id_check.get("actual_state")

    # 5. Validation: Verify Account on Target Source
    acc_exist_check = validate_account_exists(identity_id, source_id, source_name)
    report.validation_checks.append(acc_exist_check)

    account_status = None
    if acc_exist_check.get("passed"):
        acc_status_check = validate_account_status(identity_id, source_id, "Enabled", source_name)
        report.validation_checks.append(acc_status_check)
        account_status = acc_status_check.get("actual_status")

    # 6. Validation: Downstream Provisioning Evaluation
    downstream_check = check_downstream_provisioning(
        identity_id=identity_id,
        source_name=source_name,
        expected_ad_outcome="Create and enable a new AD account",
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

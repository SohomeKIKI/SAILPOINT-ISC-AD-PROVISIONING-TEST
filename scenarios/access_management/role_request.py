"""Scenario: Role Request with Source Alignment Validation.
Domain: Access & Entitlement Management.
"""

from typing import Dict, Any, Optional
from config.constants import SCENARIOS
from core.base_scenario import BaseScenario
from core.context import ExecutionContext
from core.registry import register_scenario
from sailpoint.roles import search_roles, get_role_details, validate_role_source
from sailpoint.access_requests import submit_role_request, poll_access_request_status
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("scenario.access.role_request")


@register_scenario
class RoleRequestScenario(BaseScenario):
    """Test requesting a role with strict target source alignment check."""

    scenario_id = "access.role_request"
    name = "Role Request (Source Validated)"
    category_id = "access_management"
    category_name = "Access & Entitlement Management"
    description = "Search roles, verify AD source alignment, submit request and poll status"
    expected_ad_outcome = "Grant entitlement/group membership on target AD account"
    order = 1

    def execute(self, ctx: ExecutionContext) -> TestReportItem:
        role_query = ctx.custom_params.get("role_query")
        return run_role_request(
            identity=ctx.identity,
            source=ctx.source,
            profile_id=ctx.effective_profile_id,
            role_name_query=role_query,
            interactive=ctx.interactive,
            force_confirmed=ctx.force_confirmed,
        )


def run_role_request(
    identity: Dict[str, Any],
    source: Dict[str, Any],
    profile_id: Optional[str] = None,
    role_name_query: Optional[str] = None,
    interactive: bool = True,
    force_confirmed: bool = False,
) -> TestReportItem:
    """Execute Role Request test scenario with complete source alignment verification."""
    scenario_name = SCENARIOS["ROLE_REQUEST"]
    identity_id = identity.get("id")
    identity_name = identity.get("displayName") or identity.get("name")
    source_id = source.get("id")
    source_name = source.get("name")

    logger.info(f"=== Starting Scenario: {scenario_name} for '{identity_name}' on source '{source_name}' ===")

    report = TestReportItem(
        scenario=scenario_name,
        identity_id=identity_id,
        identity_name=identity_name,
        identity_email=identity.get("email"),
        identity_profile_id=profile_id or identity.get("identityProfileId"),
        identity_profile_name=identity.get("identityProfileName"),
        source_id=source_id,
        source_name=source_name,
        initial_lifecycle_state=identity.get("lifecycleState"),
        target_lifecycle_state=identity.get("lifecycleState"),
    )

    selected_role: Optional[Dict[str, Any]] = None

    if interactive and not role_name_query:
        print("\n" + "=" * 75)
        print("  STEP 7.1: ROLE SELECTION & SOURCE ALIGNMENT CHECK")
        print(f"  Target User   : {identity_name}")
        print(f"  Target Source : {source_name} ({source_id})")
        print("=" * 75)

        while not selected_role:
            query = input("Enter Role name or keyword to search (or 'q' to cancel): ").strip()
            if query.lower() in ("q", "quit", "exit"):
                report.final_status = "FAILURE"
                report.error_message = "Role request cancelled by tester."
                return report

            roles = search_roles(query, limit=10)
            if not roles:
                print(f"No roles found matching '{query}'. Please try another search term.")
                continue

            print(f"\nFound {len(roles)} matching role(s):")
            print(f"{'#':<3} {'Role Name':<35} {'Enabled':<10} {'ID'}")
            print("-" * 75)
            for idx, r in enumerate(roles, 1):
                print(f"{idx:<3} {r.get('name', 'N/A')[:33]:<35} {str(r.get('enabled', False)):<10} {r.get('id')}")
            print("-" * 75)

            if len(roles) == 1:
                confirm = input(f"Select role '{roles[0].get('name')}'? (y/n): ").strip().lower()
                if confirm == "y":
                    selected_role = roles[0]
            else:
                sel = input(f"Choose role number (1-{len(roles)}), or 's' to search again: ").strip().lower()
                if sel == "s":
                    continue
                try:
                    choice_idx = int(sel) - 1
                    if 0 <= choice_idx < len(roles):
                        selected_role = roles[choice_idx]
                except ValueError:
                    print("Invalid selection. Try again.")
    else:
        search_term = role_name_query or "User"
        roles = search_roles(search_term, limit=5)
        if roles:
            selected_role = roles[0]
        else:
            report.final_status = "FAILURE"
            report.error_message = f"No roles found for query: {search_term}"
            return report

    role_id = selected_role.get("id")
    role_name = selected_role.get("name")
    logger.info(f"Selected role: '{role_name}' ({role_id})")

    # Step 7.2: Verify role sources and inspect associated access profiles
    print(f"\nStep 7.2: Inspecting Access Profiles and Sources for Role '{role_name}'...")
    role_details = get_role_details(role_id)
    report.api_operations.append({
        "operation": "get_role_details",
        "role_id": role_id,
        "details": role_details,
    })

    validation_info = validate_role_source(role_id, source_id)
    report.validation_checks.append({
        "check": "Role Source Alignment",
        "passed": validation_info.get("match", False),
        "details": validation_info.get("message"),
    })

    if not validation_info.get("match"):
        warning_msg = validation_info.get("message", "Role / Source mismatch detected.")
        logger.warning(warning_msg)
        print("\n" + "!" * 75)
        print("  WARNING: ROLE / SOURCE MISMATCH DETECTED")
        print(f"  {warning_msg}")
        print("!" * 75)
        if interactive and not force_confirmed:
            proceed = input("Do you wish to proceed with submitting the access request anyway? (y/n): ").strip().lower()
            if proceed != "y":
                report.final_status = "FAILURE"
                report.error_message = "Tester aborted role request due to source mismatch."
                return report

    # Step 7.3: Submit Access Request
    print(f"\nStep 7.3: Submitting Access Request for Role '{role_name}' to '{identity_name}'...")
    req_result = submit_role_request(
        identity_id=identity_id,
        role_id=role_id,
        comment=f"Automated AD test on source '{source_name}'",
    )
    report.api_operations.append({
        "operation": "submit_access_request",
        "role_id": role_id,
        "role_name": role_name,
        "result": req_result,
    })

    if not req_result.get("success"):
        report.final_status = "FAILURE"
        report.error_message = f"Access request submission failed: {req_result.get('error')}"
        report.validation_checks.append({
            "check": "Access Request Submission",
            "passed": False,
            "details": report.error_message,
        })
        return report

    request_id = req_result.get("request_id")
    report.validation_checks.append({
        "check": "Access Request Submission",
        "passed": True,
        "details": f"Request submitted successfully (ID: {request_id})",
    })

    # Step 7.4: Poll Access Request Status
    print(f"Step 7.4: Polling status of Access Request '{request_id}'...")
    poll_result = poll_access_request_status(identity_id=identity_id, max_wait_seconds=30)
    report.validation_checks.append({
        "check": "Access Request Status",
        "passed": poll_result.get("passed", False),
        "details": poll_result.get("details", "Poll completed"),
        "status": poll_result.get("status"),
    })

    report.final_status = "SUCCESS" if poll_result.get("passed") else "IN_PROGRESS"
    logger.info(f"=== Completed Scenario: {scenario_name} | Outcome: {report.final_status} ===")
    return report

"""Test Scenario: Role Request.
Implements the complete interactive sub-flow from Section 3.4 of the project handover.
Expected AD Outcome: Grant the requested role/entitlement on the target source.
Resulting Lifecycle State: No state change.
"""

from typing import Dict, Any, Optional
from config.constants import SCENARIOS
from sailpoint.roles import search_roles, get_role_details, validate_role_source
from sailpoint.access_requests import submit_role_request, poll_access_request_status
from validation.provisioning_validation import check_downstream_provisioning
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("scenario.role_request")


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
        identity_profile_id=identity.get("identityProfileId"),
        identity_profile_name=identity.get("identityProfileName"),
        source_id=source_id,
        source_name=source_name,
        initial_lifecycle_state=identity.get("lifecycleState"),
        target_lifecycle_state=identity.get("lifecycleState"),  # No lifecycle change
    )

    selected_role: Optional[Dict[str, Any]] = None

    # Step 7d.1 & 7d.2: Prompt for role name and find role via Search Roles API
    while not selected_role:
        if not role_name_query and interactive:
            print("\n" + "-" * 70)
            print("  ROLE REQUEST SUB-FLOW (Step 7d.1)")
            print("-" * 70)
            user_input = input("Enter Role Name or keyword to search (or 'q' to cancel): ").strip()
            if user_input.lower() in ("q", "quit", "exit"):
                report.final_status = "ERROR"
                report.error_message = "Role request cancelled by tester."
                return report
            role_name_query = user_input
        elif not role_name_query:
            role_name_query = "Analyst"  # Default test search term

        # Find role
        matched_roles = search_roles(role_name_query)

        # Step 7d.3: If no role matches, offer to retry or exit
        if not matched_roles:
            print(f"No roles found matching query: '{role_name_query}'.")
            if interactive:
                retry = input("Would you like to try another role name? (y/n): ").strip().lower()
                if retry != "y":
                    report.final_status = "FAILURE"
                    report.error_message = f"No roles found matching '{role_name_query}'."
                    return report
                role_name_query = None
                continue
            else:
                report.final_status = "FAILURE"
                report.error_message = f"No roles found matching query '{role_name_query}'."
                return report

        # Step 7d.4: If several roles match, list them for tester selection
        if len(matched_roles) == 1 or not interactive:
            selected_role = matched_roles[0]
            print(f"Selected role: '{selected_role.get('name')}' (ID: {selected_role.get('id')})")
        else:
            print(f"\nMultiple roles matched query '{role_name_query}':")
            for idx, r in enumerate(matched_roles, 1):
                print(f"  [{idx}] {r.get('name')} (ID: {r.get('id')})")
            choice = input(f"Select role [1-{len(matched_roles)}] or 'r' to retry: ").strip()
            if choice.lower() == "r":
                role_name_query = None
                continue
            try:
                sel_idx = int(choice) - 1
                if 0 <= sel_idx < len(matched_roles):
                    selected_role = matched_roles[sel_idx]
                else:
                    print("Invalid selection. Try again.")
                    continue
            except ValueError:
                print("Invalid input. Try again.")
                continue

    role_id = selected_role.get("id")
    role_name = selected_role.get("name")

    # Step 7d.5 & 7d.6: Retrieve role details, associated source(s), and compare with Step 6 source
    validation_info = validate_role_source(role_id, source_id)
    report.validation_checks.append({
        "check": "Role Source Alignment",
        "passed": validation_info.get("match", False),
        "details": validation_info.get("message"),
    })

    # Step 7d.7: If sources differ, warn the tester and offer to continue
    if not validation_info.get("match"):
        print("\n" + "!" * 70)
        print("  WARNING: ROLE / SOURCE MISMATCH DETECTED (Step 7d.7)")
        print(f"  {validation_info.get('message')}")
        print("!" * 70)
        if interactive:
            cont = input("Do you wish to proceed with submitting the access request anyway? (y/n): ").strip().lower()
            if cont != "y":
                report.final_status = "FAILURE"
                report.error_message = "Tester aborted role request due to source mismatch."
                return report

    # Step 7d.8: Submit the Access Request API call
    print(f"\nSubmitting Access Request for Role '{role_name}' to '{identity_name}'...")
    submit_res = submit_role_request(
        identity_id=identity_id,
        role_id=role_id,
        comment=f"Automated test on source '{source_name}'",
    )
    report.api_operations.append({
        "operation": "submit_access_request",
        "role_id": role_id,
        "role_name": role_name,
        "result": submit_res,
    })

    request_id = submit_res.get("request_id")
    report.role_info = {
        "role_name": role_name,
        "role_id": role_id,
        "access_request_id": request_id,
        "role_source_name": [s.get("name") for s in validation_info.get("role_sources", [])] or [source_name],
        "source_match": validation_info.get("match", False),
    }

    # Step 7d.9: Record Access Request ID and poll its status
    if submit_res.get("success"):
        print(f"Access Request submitted! Request ID: {request_id or 'Submitted'}")
        if request_id:
            poll_result = poll_access_request_status(request_id, max_attempts=4, delay_seconds=3)
            report.validation_checks.append({
                "check": "Access Request Status Polling",
                "passed": poll_result.get("completed", False) or poll_result.get("state") in ("PENDING", "IN_PROGRESS", "APPROVED"),
                "details": poll_result.get("message"),
            })
        else:
            report.validation_checks.append({
                "check": "Access Request Submission",
                "passed": True,
                "details": "Request accepted by ISC access request engine.",
            })
    else:
        report.validation_checks.append({
            "check": "Access Request Submission",
            "passed": False,
            "details": submit_res.get("error"),
        })

    # Step 7d.10: Record role request outcome and downstream evaluation
    downstream_check = check_downstream_provisioning(
        identity_id=identity_id,
        source_name=source_name,
        expected_ad_outcome=f"Grant role '{role_name}' on target source",
        account_status=None,
    )
    report.validation_checks.append(downstream_check)

    report.final_status = "SUCCESS" if submit_res.get("success") else "FAILURE"
    if not submit_res.get("success"):
        report.error_message = submit_res.get("error")

    logger.info(f"=== Completed Scenario: {scenario_name} | Outcome: {report.final_status} ===")
    return report


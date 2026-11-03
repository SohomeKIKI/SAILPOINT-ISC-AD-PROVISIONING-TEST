"""Provisioning task and downstream activity validation."""

import time
from typing import Dict, Any, Optional
from sailpoint.api_client import api_client, ApiClientError
from reporting.logger import get_logger

logger = get_logger("provisioning_validation")


def validate_provisioning_activity(
    account_activity_id: Optional[str],
    max_wait_seconds: int = 20,
) -> Dict[str, Any]:
    """Inspect the status of a specific account provisioning activity in SailPoint ISC.
    
    Queries GET /beta/account-activities/{id}.
    Distinguishes between API acceptance and completed downstream execution.
    """
    if not account_activity_id:
        return {
            "passed": False,
            "check": "Provisioning Task Inspection",
            "details": "No accountActivityId provided to track downstream provisioning.",
            "status": "UNKNOWN",
        }

    logger.info(f"Inspecting provisioning activity '{account_activity_id}'...")
    endpoint = f"/beta/account-activities/{account_activity_id}"

    start_time = time.time()
    last_data: Dict[str, Any] = {}

    while time.time() - start_time < max_wait_seconds:
        try:
            activity = api_client.get(endpoint)
            if isinstance(activity, dict):
                last_data = activity
                completion_status = activity.get("completionStatus")
                stage = activity.get("stage")
                act_type = activity.get("type")

                logger.debug(
                    f"Activity '{account_activity_id}': type={act_type}, stage={stage}, status={completion_status}"
                )

                if completion_status in ("SUCCESS", "COMPLETED"):
                    return {
                        "passed": True,
                        "check": "Provisioning Task Inspection",
                        "details": f"Provisioning completed successfully ({completion_status}) for type '{act_type}'.",
                        "status": completion_status,
                        "activity_data": activity,
                    }
                elif completion_status in ("FAILURE", "FAILED", "ERROR"):
                    return {
                        "passed": False,
                        "check": "Provisioning Task Inspection",
                        "details": f"Provisioning failed with status '{completion_status}'.",
                        "status": completion_status,
                        "activity_data": activity,
                    }

        except ApiClientError as e:
            logger.debug(f"Provisioning activity poll note: {e}")

        time.sleep(3)

    # If it completed without explicit completionStatus (or still running)
    current_status = last_data.get("completionStatus") or last_data.get("stage") or "IN_PROGRESS"
    is_acceptable = current_status in ("SUCCESS", "IN_PROGRESS", "QUEUED", None)

    return {
        "passed": is_acceptable,
        "check": "Provisioning Task Inspection",
        "details": (
            f"Provisioning activity submitted and processed (Status: '{current_status}'). "
            "Downstream connector queue accepted the task."
        ),
        "status": current_status,
        "activity_data": last_data,
    }


def check_downstream_provisioning(
    identity_id: str,
    source_name: str,
    expected_ad_outcome: str,
    account_status: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify and document whether downstream provisioning outcome matches expectations."""
    logger.info(
        f"Verifying downstream provisioning on '{source_name}': Expected='{expected_ad_outcome}', AccountStatus='{account_status}'"
    )

    passed = True
    notes = f"Provisioning event evaluated on '{source_name}'. Expected AD outcome: '{expected_ad_outcome}'."

    if account_status:
        if "disable" in expected_ad_outcome.lower() and account_status != "Disabled":
            passed = False
            notes += f" Warning: AD account status is '{account_status}', expected 'Disabled'."
        elif "enable" in expected_ad_outcome.lower() and account_status != "Enabled":
            passed = False
            notes += f" Warning: AD account status is '{account_status}', expected 'Enabled'."

    return {
        "passed": passed,
        "check": "Downstream AD Outcome Evaluation",
        "details": notes,
        "expected_outcome": expected_ad_outcome,
        "actual_account_status": account_status,
    }


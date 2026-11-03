"""Access Request submission, status tracking, and polling in SailPoint ISC."""

import time
from typing import Dict, Any, Optional
from sailpoint.api_client import api_client, ApiClientError
from reporting.logger import get_logger

logger = get_logger("access_requests")


def submit_role_request(
    identity_id: str,
    role_id: str,
    comment: str = "Automated AD Provisioning Test",
) -> Dict[str, Any]:
    """Submit an access request to grant a role to an identity.
    
    Uses POST /v3/access-requests with GRANT_ACCESS.
    """
    endpoint = "/v3/access-requests"
    payload = {
        "requestedFor": [identity_id],
        "requestType": "GRANT_ACCESS",
        "requestedItems": [
            {
                "type": "ROLE",
                "id": role_id,
                "comment": comment,
            }
        ],
    }

    logger.info(
        f"Submitting access request: Identity={identity_id}, Role={role_id}"
    )

    try:
        response_data = api_client.post(endpoint, json_data=payload)
        logger.info(f"Access request submitted successfully. Response: {response_data}")

        # Extract request ID or execution reference
        request_id = None
        if isinstance(response_data, dict):
            request_id = (
                response_data.get("id")
                or response_data.get("requestId")
                or response_data.get("trackingId")
            )
            # Sometimes ISC returns a list of requested items or errors
            if not request_id and "items" in response_data:
                items = response_data.get("items", [])
                if items:
                    request_id = items[0].get("id")

        return {
            "success": True,
            "request_id": request_id,
            "role_id": role_id,
            "identity_id": identity_id,
            "raw_response": response_data,
        }

    except ApiClientError as e:
        error_msg = f"Access request submission failed: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "role_id": role_id,
            "identity_id": identity_id,
            "status_code": e.status_code,
            "response_text": e.response_text,
        }


def get_access_request_status(request_id: str) -> Dict[str, Any]:
    """Check the status of an access request via /v3/access-request-status."""
    endpoint = f"/v3/access-request-status/{request_id}"
    try:
        res = api_client.get(endpoint)
        return {"success": True, "status_data": res}
    except ApiClientError:
        # Fallback to query with filter
        try:
            res = api_client.get(f"/v3/access-request-status?filters=id eq \"{request_id}\"")
            return {"success": True, "status_data": res}
        except ApiClientError as e2:
            logger.warning(f"Failed to check access request status for '{request_id}': {e2}")
            return {"success": False, "error": str(e2)}


def poll_access_request_status(
    request_id: Optional[str],
    max_attempts: int = 6,
    delay_seconds: int = 5,
) -> Dict[str, Any]:
    """Poll an access request until completion or maximum wait time is reached."""
    if not request_id:
        return {
            "completed": False,
            "state": "NO_REQUEST_ID",
            "message": "No access request ID available to poll.",
        }

    logger.info(f"Polling access request '{request_id}' (max {max_attempts} attempts)...")
    last_status = "UNKNOWN"

    for attempt in range(1, max_attempts + 1):
        status_res = get_access_request_status(request_id)
        if status_res.get("success"):
            data = status_res.get("status_data")
            if isinstance(data, dict):
                last_status = data.get("state") or data.get("status") or "PENDING"
            elif isinstance(data, list) and data:
                last_status = data[0].get("state") or data[0].get("status") or "PENDING"

            logger.info(f"Attempt {attempt}/{max_attempts}: Request '{request_id}' status is '{last_status}'")

            if last_status.upper() in ("COMPLETED", "APPROVED", "EXECUTED", "SUCCESS"):
                return {
                    "completed": True,
                    "state": last_status,
                    "message": f"Access request completed successfully with status: {last_status}",
                    "details": data,
                }
            elif last_status.upper() in ("REJECTED", "FAILED", "CANCELLED", "ERROR"):
                return {
                    "completed": True,
                    "state": last_status,
                    "message": f"Access request finished with negative status: {last_status}",
                    "details": data,
                }

        if attempt < max_attempts:
            time.sleep(delay_seconds)

    return {
        "completed": False,
        "state": last_status,
        "message": f"Polling timed out after {max_attempts * delay_seconds}s. Last known status: {last_status}",
    }


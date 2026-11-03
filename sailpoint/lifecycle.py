"""Lifecycle state transitions and management in SailPoint ISC."""

from typing import Dict, Any, Optional
from sailpoint.api_client import api_client, ApiClientError
from sailpoint.identity import get_identity_by_id
from sailpoint.identity_profiles import find_lifecycle_state_by_key, get_lifecycle_states
from reporting.logger import get_logger

logger = get_logger("lifecycle")


def get_current_lifecycle_state(identity_id: str) -> Optional[str]:
    """Retrieve the current lifecycle state of an identity."""
    identity = get_identity_by_id(identity_id)
    if identity:
        return identity.get("lifecycleState")
    return None


def apply_lifecycle_state(
    identity_id: str,
    profile_id: str,
    target_state_key: str,
) -> Dict[str, Any]:
    """Apply a new lifecycle state to a user in SailPoint ISC.
    
    1. Looks up the configured lifecycle states for the user's profile.
    2. Resolves the target technical name / alias to the exact lifecycleStateId.
    3. Calls POST /v3/identities/{identity_id}/set-lifecycle-state.
    4. Captures the resulting accountActivityId.
    5. Returns execution details for verification and reporting.
    """
    initial_user = get_identity_by_id(identity_id)
    initial_state = initial_user.get("lifecycleState") if initial_user else "unknown"

    logger.info(
        f"Applying lifecycle state '{target_state_key}' to identity {identity_id} (current state: '{initial_state}')"
    )

    # Resolve state ID
    matched_state = find_lifecycle_state_by_key(profile_id, target_state_key)
    if not matched_state:
        available_states = [s.get("technicalName") for s in get_lifecycle_states(profile_id)]
        error_msg = (
            f"Lifecycle state '{target_state_key}' is not configured on profile '{profile_id}'. "
            f"Available states in tenant: {available_states}"
        )
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "initial_state": initial_state,
            "target_state": target_state_key,
        }

    lifecycle_state_id = matched_state.get("id")
    resolved_technical_name = matched_state.get("technicalName")
    resolved_display_name = matched_state.get("name")

    payload = {"lifecycleStateId": lifecycle_state_id}
    endpoint = f"/v3/identities/{identity_id}/set-lifecycle-state"

    try:
        response_data = api_client.post(endpoint, json_data=payload)
        account_activity_id = response_data.get("accountActivityId")

        logger.info(
            f"Successfully submitted lifecycle state change to '{resolved_technical_name}'. "
            f"AccountActivityId: {account_activity_id}"
        )

        return {
            "success": True,
            "account_activity_id": account_activity_id,
            "initial_state": initial_state,
            "target_state": target_state_key,
            "applied_technical_name": resolved_technical_name,
            "applied_display_name": resolved_display_name,
            "lifecycle_state_id": lifecycle_state_id,
            "raw_response": response_data,
        }

    except ApiClientError as e:
        error_msg = f"Failed to set lifecycle state: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "initial_state": initial_state,
            "target_state": target_state_key,
            "status_code": e.status_code,
            "response_text": e.response_text,
        }


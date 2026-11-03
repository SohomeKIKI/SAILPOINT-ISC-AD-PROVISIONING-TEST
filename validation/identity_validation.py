"""Identity validation functions: existence, attributes, and lifecycle state."""

import time
from typing import Dict, Any, Optional
from sailpoint.identity import get_identity_by_id
from reporting.logger import get_logger

logger = get_logger("identity_validation")


def validate_identity_state(
    identity_id: str,
    expected_state: str,
    max_wait_seconds: int = 25,
    poll_interval: int = 2,
) -> Dict[str, Any]:
    """Verify that an identity's lifecycle state matches the expected state.
    
    Includes polling with exponential retry to accommodate SailPoint's asynchronous
    identity refresh and background task processing.
    """
    exp_clean = expected_state.strip().lower()

    # Define equivalent state clusters
    state_aliases = {
        "employmenttermination": ["employmenttermination", "employementtermination", "terminated", "termination"],
        "loa": ["loa", "leaveofabsence"],
        "skp": ["skp"],
        "ear": ["ear"],
        "active": ["active"],
    }

    # Find canonical group
    expected_group = [exp_clean]
    for key, group in state_aliases.items():
        if exp_clean in group:
            expected_group = group
            break

    start_time = time.time()
    last_identity = None
    actual_state = "unknown"
    is_matched = False

    while True:
        last_identity = get_identity_by_id(identity_id)
        if not last_identity:
            return {
                "passed": False,
                "check": "Identity Existence",
                "details": f"Identity with ID '{identity_id}' was not found in SailPoint ISC.",
                "actual_state": None,
                "expected_state": expected_state,
            }

        actual_state = (last_identity.get("lifecycleState") or "").strip().lower()
        is_matched = actual_state in expected_group or actual_state == exp_clean

        if is_matched:
            break

        elapsed = time.time() - start_time
        if elapsed >= max_wait_seconds:
            break

        logger.debug(
            f"Waiting for identity {identity_id} state transition to '{expected_state}' (current: '{actual_state}')..."
        )
        time.sleep(poll_interval)

    logger.info(
        f"Validation [Lifecycle State]: Expected='{expected_state}', Actual='{actual_state}', Match={is_matched}"
    )

    return {
        "passed": is_matched,
        "check": "Lifecycle State Verification",
        "details": (
            f"State matches expected '{expected_state}' (actual: '{actual_state}')"
            if is_matched
            else f"State mismatch: expected '{expected_state}', but identity is in '{actual_state}'"
        ),
        "actual_state": actual_state,
        "expected_state": expected_state,
        "identity_name": last_identity.get("displayName") if last_identity else "Unknown",
    }


def validate_identity_attributes(
    identity_id: str,
    required_fields: Optional[list] = None,
) -> Dict[str, Any]:
    """Verify that the identity possesses standard required attributes."""
    if required_fields is None:
        required_fields = ["name", "email", "department", "lifecycleState", "identityProfileId"]

    identity = get_identity_by_id(identity_id)
    if not identity:
        return {
            "passed": False,
            "check": "Identity Attributes Verification",
            "details": f"Identity '{identity_id}' not found.",
            "missing_fields": required_fields,
        }

    missing = [f for f in required_fields if not identity.get(f)]
    passed = len(missing) == 0

    return {
        "passed": passed,
        "check": "Identity Attributes Verification",
        "details": (
            f"All {len(required_fields)} required attributes are present."
            if passed
            else f"Missing required attributes: {missing}"
        ),
        "missing_fields": missing,
        "attributes": {k: identity.get(k) for k in required_fields},
    }

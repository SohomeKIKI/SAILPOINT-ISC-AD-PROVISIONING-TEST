"""Identity Profile retrieval and lifecycle state mapping for SailPoint ISC."""

from typing import List, Dict, Any, Optional
from sailpoint.api_client import api_client, ApiClientError
from reporting.logger import get_logger

logger = get_logger("identity_profiles")


def get_identity_profiles(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve all available Identity Profiles configured in the tenant."""
    try:
        profiles = api_client.get(f"/v3/identity-profiles?limit={limit}")
        if isinstance(profiles, list):
            logger.info(f"Retrieved {len(profiles)} identity profiles from tenant.")
            return profiles
        return []
    except ApiClientError as e:
        logger.error(f"Failed to retrieve identity profiles: {e}")
        return []


def get_identity_profile(profile_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve details of a specific identity profile by ID."""
    try:
        profile = api_client.get(f"/v3/identity-profiles/{profile_id}")
        return profile if isinstance(profile, dict) else None
    except ApiClientError as e:
        logger.error(f"Failed to retrieve identity profile '{profile_id}': {e}")
        return None


def get_lifecycle_states(profile_id: str) -> List[Dict[str, Any]]:
    """Retrieve all configured lifecycle states for a given identity profile.
    
    Each lifecycle state object contains:
    - id: Unique UUID for the lifecycle state within this profile
    - name: Display name (e.g. 'Active', 'Leave of Absence', 'SKP', 'EAR')
    - technicalName: Internal state key (e.g. 'active', 'loa', 'skp', 'ear', 'terminated')
    """
    try:
        states = api_client.get(f"/v3/identity-profiles/{profile_id}/lifecycle-states")
        if isinstance(states, list):
            logger.info(f"Retrieved {len(states)} lifecycle states for profile '{profile_id}'.")
            return states
        return []
    except ApiClientError as e:
        logger.error(f"Failed to retrieve lifecycle states for profile '{profile_id}': {e}")
        return []


def find_lifecycle_state_by_key(profile_id: str, state_key: str) -> Optional[Dict[str, Any]]:
    """Find a lifecycle state matching a requested technical key or alias within a profile."""
    states = get_lifecycle_states(profile_id)
    key_lower = state_key.strip().lower()

    # Direct match on technicalName or name
    for s in states:
        tech_name = s.get("technicalName", "").lower()
        disp_name = s.get("name", "").lower()
        if tech_name == key_lower or disp_name == key_lower:
            return s

    # Handle common aliases (e.g. 'employmentTermination' vs 'terminated' vs 'employementTermination')
    termination_keys = {"employmenttermination", "employementtermination", "terminated", "termination"}
    if key_lower in termination_keys:
        for s in states:
            if s.get("technicalName", "").lower() in termination_keys or s.get("name", "").lower() in termination_keys:
                return s

    loa_keys = {"loa", "leaveofabsence", "leave of absence"}
    if key_lower in loa_keys:
        for s in states:
            if s.get("technicalName", "").lower() in loa_keys or s.get("name", "").lower() in loa_keys:
                return s

    return None


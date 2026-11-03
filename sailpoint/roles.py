"""Role search, inspection, and source association in SailPoint ISC."""

from typing import List, Dict, Any, Optional
from sailpoint.api_client import api_client, ApiClientError
from reporting.logger import get_logger

logger = get_logger("roles")


def search_roles(role_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for roles by name using filter query or Search API.
    
    Returns all roles matching or containing the given role_name.
    """
    clean_name = role_name.strip()
    logger.info(f"Searching for roles matching: '{clean_name}'")

    # Method 1: Try /v3/roles with contains filter
    try:
        params = {"filters": f'name co "{clean_name}"', "limit": limit}
        roles = api_client.get("/v3/roles", params=params)
        if isinstance(roles, list) and roles:
            logger.info(f"Found {len(roles)} matching roles via filter.")
            return roles
    except ApiClientError as e:
        logger.debug(f"Role filter query returned: {e}")

    # Method 2: Try /v3/search with index 'roles'
    try:
        payload = {
            "indices": ["roles"],
            "query": {"query": f'name:*{clean_name}*'},
        }
        search_results = api_client.post(f"/v3/search?limit={limit}", json_data=payload)
        if isinstance(search_results, list) and search_results:
            logger.info(f"Found {len(search_results)} matching roles via search API.")
            return search_results
    except ApiClientError as e:
        logger.debug(f"Role search API query returned: {e}")

    # Method 3: Fallback retrieve top roles and do client-side filter
    try:
        all_roles = api_client.get(f"/v3/roles?limit=50")
        if isinstance(all_roles, list):
            matched = [
                r for r in all_roles
                if clean_name.lower() in (r.get("name") or "").lower()
            ]
            return matched
    except ApiClientError as e:
        logger.error(f"Failed to retrieve roles: {e}")

    return []


def get_role_details(role_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full details of a specific role by ID."""
    try:
        role = api_client.get(f"/v3/roles/{role_id}")
        return role if isinstance(role, dict) else None
    except ApiClientError as e:
        logger.error(f"Failed to retrieve role '{role_id}': {e}")
        return None


def get_role_associated_sources(role_id: str) -> List[Dict[str, Any]]:
    """Retrieve all provisioning target sources associated with a role.
    
    Inspects the role's Access Profiles and resolves their underlying sources.
    """
    role = get_role_details(role_id)
    if not role:
        return []

    sources = []
    seen_ids = set()

    # Inspect access profiles
    access_profiles = role.get("accessProfiles") or []
    for ap_ref in access_profiles:
        ap_id = ap_ref.get("id")
        if not ap_id:
            continue
        try:
            ap_data = api_client.get(f"/v3/access-profiles/{ap_id}")
            src = ap_data.get("source") or {}
            src_id = src.get("id")
            if src_id and src_id not in seen_ids:
                seen_ids.add(src_id)
                sources.append({
                    "id": src_id,
                    "name": src.get("name", "Unknown"),
                    "type": src.get("type", "Unknown"),
                    "access_profile_id": ap_id,
                    "access_profile_name": ap_data.get("name", "Unknown"),
                })
        except ApiClientError as e:
            logger.debug(f"Could not resolve source for access profile '{ap_id}': {e}")

    # Also check if role has a direct source field
    if not sources and "source" in role:
        src = role.get("source") or {}
        if src.get("id"):
            sources.append({
                "id": src.get("id"),
                "name": src.get("name", "Unknown"),
                "type": src.get("type", "Unknown"),
            })

    logger.info(f"Role '{role.get('name')}' is associated with {len(sources)} source(s): {[s['name'] for s in sources]}")
    return sources


def validate_role_source(role_id: str, target_source_id: str) -> Dict[str, Any]:
    """Compare role's associated source(s) against the tester's selected test source.
    
    Returns match details and warnings if there is a mismatch.
    """
    role = get_role_details(role_id)
    if not role:
        return {"valid": False, "match": False, "message": f"Role '{role_id}' not found."}

    role_sources = get_role_associated_sources(role_id)
    matching_sources = [s for s in role_sources if s.get("id") == target_source_id]

    if matching_sources:
        return {
            "valid": True,
            "match": True,
            "role_name": role.get("name"),
            "role_id": role_id,
            "matched_source": matching_sources[0],
            "all_role_sources": role_sources,
            "message": f"Source matched! Role provisions to target source '{matching_sources[0].get('name')}'.",
        }
    else:
        role_src_names = [s.get("name") for s in role_sources] or ["None directly mapped"]
        return {
            "valid": True,
            "match": False,
            "role_name": role.get("name"),
            "role_id": role_id,
            "role_sources": role_sources,
            "message": (
                f"SOURCE MISMATCH WARNING: Role '{role.get('name')}' is associated with source(s) {role_src_names}, "
                f"which does not match your selected test source (ID: {target_source_id})."
            ),
        }


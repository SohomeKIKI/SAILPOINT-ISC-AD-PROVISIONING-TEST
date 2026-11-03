"""Source retrieval and AD source identification in SailPoint ISC."""

from typing import List, Dict, Any, Optional
from sailpoint.api_client import api_client, ApiClientError
from reporting.logger import get_logger

logger = get_logger("sources")


def get_sources(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieve available sources from SailPoint ISC."""
    try:
        sources = api_client.get(f"/v3/sources?limit={limit}")
        if isinstance(sources, list):
            logger.info(f"Retrieved {len(sources)} sources from tenant.")
            return sources
        return []
    except ApiClientError as e:
        logger.error(f"Failed to retrieve sources: {e}")
        return []


def get_source_by_id(source_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full details of a specific source by its unique ID."""
    try:
        source = api_client.get(f"/v3/sources/{source_id}")
        return source if isinstance(source, dict) else None
    except ApiClientError as e:
        logger.error(f"Failed to retrieve source '{source_id}': {e}")
        return None


def get_ad_sources() -> List[Dict[str, Any]]:
    """Filter and return only Active Directory sources.
    
    Distinguishes target AD provisioning targets from authoritative Delimited File sources.
    """
    all_sources = get_sources(limit=250)
    ad_sources = []
    for s in all_sources:
        s_type = (s.get("type") or "").lower()
        s_name = (s.get("name") or "").lower()
        if "active directory" in s_type or "ad" in s_type or "active directory" in s_name:
            ad_sources.append(s)

    logger.info(f"Found {len(ad_sources)} Active Directory sources in tenant.")
    return ad_sources


def get_delimited_file_sources() -> List[Dict[str, Any]]:
    """Filter and return Delimited File sources (used for test identity onboarding)."""
    all_sources = get_sources(limit=250)
    delimited = []
    for s in all_sources:
        s_type = (s.get("type") or "").lower()
        if "delimited" in s_type or "csv" in s_type:
            delimited.append(s)
    return delimited


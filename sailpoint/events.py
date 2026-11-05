"""SailPoint Identity Security Cloud (ISC) Event and Audit log service."""

from typing import List, Dict, Any, Optional
from sailpoint.api_client import api_client, ApiClientError
from reporting.logger import get_logger

logger = get_logger("events")


def extract_event_source(event: Dict[str, Any]) -> str:
    """Extract clean target or associated source name from an audit event."""
    attrs = event.get("attributes") or {}

    # Check direct sourceName attribute
    src_name = attrs.get("sourceName")
    if src_name and str(src_name).strip().lower() not in ("null", "none"):
        # Strip trailing connector IDs if formatted like 'Source_Name [source-12345]'
        clean = str(src_name).split("[")[0].strip()
        if clean:
            return clean

    # Check generic source attribute
    src = attrs.get("source") or event.get("source")
    if src and isinstance(src, str) and src.strip().lower() not in ("null", "none"):
        return src.strip()
    elif src and isinstance(src, dict):
        return src.get("name") or "Unknown Source"

    # Check if target name matches a source
    target = event.get("target") or {}
    t_name = target.get("name") or ""
    if "[source]" in t_name.lower():
        return t_name.replace("[source]", "").strip()

    # Fallback to event interface or Identity Level
    interface = attrs.get("interface")
    if interface and str(interface).strip().lower() not in ("null", "none"):
        return f"{interface}"

    return "Identity Level"


def fetch_identity_events(
    identity_id: str,
    identity_name: str,
    limit: int = 10,
    source_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve audit events targeting this identity, with optional source filtering.
    
    Args:
        identity_id: SailPoint UID of the identity
        identity_name: Display name or technical name of the identity
        limit: Maximum number of events to fetch (e.g. 10 or 250)
        source_filter: Optional source name to filter by (or None for all sources)
    """
    logger.info(
        f"Fetching events for identity '{identity_name}' (limit={limit}, source_filter='{source_filter}')..."
    )

    clean_name = identity_name.strip()
    base_query = f'target.id:{identity_id} OR target.name:*{clean_name}*'

    # Determine fetch limit: fetch slightly more if filtering by source client-side
    fetch_limit = min(limit * 3, 250) if (source_filter and source_filter.lower() != "all") else limit

    payload = {
        "indices": ["events"],
        "query": {"query": base_query},
        "sort": ["-created"],
    }

    raw_events: List[Dict[str, Any]] = []
    try:
        res = api_client.post(f"/v3/search?limit={fetch_limit}", json_data=payload)
        if isinstance(res, list):
            raw_events = res
    except ApiClientError as e:
        logger.debug(f"Sorted search failed ({e}), retrying without sort parameter...")
        try:
            payload.pop("sort", None)
            res = api_client.post(f"/v3/search?limit={fetch_limit}", json_data=payload)
            if isinstance(res, list):
                raw_events = res
        except ApiClientError as e2:
            logger.error(f"Event search API error: {e2}")
            return []

    # If no source filter or 'all', return requested limit
    if not source_filter or source_filter.strip().lower() in ("all", "all sources"):
        return raw_events[:limit]

    # Filter by specific source (case-insensitive substring match)
    filter_norm = source_filter.strip().lower()
    filtered: List[Dict[str, Any]] = []

    for ev in raw_events:
        src = extract_event_source(ev).lower()
        attrs = ev.get("attributes") or {}
        raw_src = str(attrs.get("sourceName") or attrs.get("source") or "").lower()
        target_name = str((ev.get("target") or {}).get("name") or "").lower()

        if filter_norm in src or filter_norm in raw_src or filter_norm in target_name:
            filtered.append(ev)

    logger.info(f"Filtered {len(filtered)} event(s) matching source '{source_filter}' out of {len(raw_events)} raw events.")
    return filtered[:limit]


def get_correlated_sources_for_identity(
    identity_id: str,
    current_source: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    """Discover all sources associated with this identity (via correlated accounts and current target)."""
    sources_dict: Dict[str, Dict[str, str]] = {}

    # 1. Add currently selected test source if provided
    if current_source and current_source.get("id"):
        src_id = current_source.get("id")
        src_name = current_source.get("name", "Unknown Source")
        sources_dict[src_id] = {
            "id": src_id,
            "name": src_name,
            "type": current_source.get("type", "Provisioning Target"),
        }

    # 2. Query correlated accounts for identity
    try:
        from sailpoint.accounts import get_accounts_for_identity
        accounts = get_accounts_for_identity(identity_id)
        for acc in accounts:
            s_id = acc.get("sourceId")
            s_name = acc.get("sourceName")
            if s_id and s_id not in sources_dict:
                sources_dict[s_id] = {
                    "id": s_id,
                    "name": s_name or "Unknown Source",
                    "type": "Correlated Account Source",
                }
    except Exception as e:
        logger.debug(f"Could not retrieve accounts for source discovery: {e}")

    # Fallback default sources if none detected
    if not sources_dict:
        sources_dict["ad"] = {"id": "AD_Demo_Source", "name": "AD_Demo_Source", "type": "Active Directory"}

    return list(sources_dict.values())


def format_events_table(events: List[Dict[str, Any]], title: str) -> str:
    """Format a list of events into a clean, readable text table."""
    lines = [
        "",
        "=" * 85,
        f"  {title.upper()} ({len(events)} Events)",
        "=" * 85,
        f"{'#':<3} {'Event Name':<32} {'Source':<20} {'Status':<10} {'Timestamp'}",
        "-" * 85,
    ]

    if not events:
        lines.append("  No audit events found matching the specified criteria.\n")
        lines.append("=" * 85)
        return "\n".join(lines)

    for idx, ev in enumerate(events, 1):
        name = str(ev.get("name") or ev.get("action") or "Unknown Event")[:30]
        source = extract_event_source(ev)[:18]
        status = str(ev.get("status") or "N/A")[:8]
        created = str(ev.get("created") or "N/A")[:19].replace("T", " ")
        lines.append(f"{idx:<3} {name:<32} {source:<20} [{status:<8}] {created}")

    lines.append("=" * 85)
    return "\n".join(lines)


def format_single_event_card(ev: Dict[str, Any]) -> str:
    """Format single event attributes into a detailed card."""
    lines = [
        "",
        "=" * 80,
        f"  EVENT DETAILS: {ev.get('name') or ev.get('action')}",
        "=" * 80,
        f"  * Event ID       : {ev.get('id')}",
        f"  * Action / Type  : {ev.get('action')} ({ev.get('type')})",
        f"  * Technical Name : {ev.get('technicalName') or 'N/A'}",
        f"  * Status         : {ev.get('status')}",
        f"  * Created (UTC)  : {ev.get('created')}",
    ]

    actor = ev.get("actor") or {}
    target = ev.get("target") or {}
    lines.append(f"  * Actor          : {actor.get('name', 'System')} ({actor.get('id', 'N/A')})")
    lines.append(f"  * Target         : {target.get('name', 'N/A')} ({target.get('id', 'N/A')})")
    lines.append(f"  * Source System  : {extract_event_source(ev)}")

    tracking = ev.get("trackingNumber")
    if tracking:
        lines.append(f"  * Tracking Number: {tracking}")

    attrs = ev.get("attributes") or {}
    if attrs:
        lines.append("  * Event Attributes & Diffs:")
        for k, v in sorted(attrs.items()):
            lines.append(f"      - {k:<28}: {v}")

    lines.append("=" * 80 + "\n")
    return "\n".join(lines)

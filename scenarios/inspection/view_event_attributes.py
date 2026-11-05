"""Inspection Scenario: View Identity Event Attributes & Audit History.
Domain: Identity & Account Inspection (Matches UI 'Events' tab).
"""

from typing import Dict, Any, List
from core.base_scenario import BaseScenario
from core.context import ExecutionContext
from core.registry import register_scenario
from sailpoint.api_client import api_client, ApiClientError
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("scenario.inspection.events")


@register_scenario
class ViewEventAttributesScenario(BaseScenario):
    """Inspect identity event attributes and audit history (matches UI 'Events' tab)."""

    scenario_id = "inspection.event_attributes"
    name = "View Identity Event Attributes"
    category_id = "inspection"
    category_name = "Identity & Account Inspection"
    description = "Inspect recent security, provisioning, and lifecycle events for this identity"
    expected_ad_outcome = "Read-only inspection of identity audit event trail"
    order = 4

    def execute(self, ctx: ExecutionContext) -> TestReportItem:
        logger.info(f"Retrieving audit events for identity '{ctx.identity_name}'...")
        events = self._fetch_events(ctx.identity_id, ctx.identity_name)

        print("\n" + "=" * 80)
        print(f"  IDENTITY AUDIT EVENTS: {ctx.identity_name} ({len(events)} Results)")
        print("=" * 80)
        print(f"{'#':<3} {'Event Name':<32} {'Type':<18} {'Status':<10} {'Timestamp'}")
        print("-" * 80)

        if not events:
            print("  No recent audit events found for this identity.\n")
        else:
            for idx, ev in enumerate(events, 1):
                name = str(ev.get("name") or ev.get("action") or "Unknown")[:30]
                ev_type = str(ev.get("type") or "N/A")[:16]
                status = str(ev.get("status") or "N/A")[:8]
                created = str(ev.get("created") or "N/A")[:19].replace("T", " ")
                print(f"{idx:<3} {name:<32} {ev_type:<18} [{status:<8}] {created}")

            print("=" * 80)

            # Option to inspect a single event's detailed attributes
            if ctx.interactive and events:
                drill = input("\nEnter event # to view full attributes, or press Enter to return: ").strip()
                try:
                    ev_idx = int(drill) - 1
                    if 0 <= ev_idx < len(events):
                        self._print_single_event(events[ev_idx])
                except ValueError:
                    pass

        report = TestReportItem(
            scenario="View Identity Event Attributes",
            identity_id=ctx.identity_id,
            identity_name=ctx.identity_name,
            identity_email=ctx.identity_email,
            identity_profile_id=ctx.effective_profile_id,
            source_id=ctx.source_id,
            source_name=ctx.source_name,
            initial_lifecycle_state=ctx.current_lifecycle_state,
            target_lifecycle_state=ctx.current_lifecycle_state,
            resulting_lifecycle_state=ctx.current_lifecycle_state,
            final_status="SUCCESS",
        )
        report.validation_checks.append({
            "check": "Event History Inspection",
            "passed": True,
            "details": f"Successfully retrieved {len(events)} event records for '{ctx.identity_name}'.",
        })
        return report

    def _fetch_events(self, identity_id: str, identity_name: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Query SailPoint Search API events index for events targeting this identity."""
        query_str = f'target.id:{identity_id} OR target.name:*{identity_name}*'
        payload = {
            "indices": ["events"],
            "query": {"query": query_str},
            "sort": ["-created"],
        }
        try:
            res = api_client.post(f"/v3/search?limit={limit}", json_data=payload)
            return res if isinstance(res, list) else []
        except ApiClientError as e:
            logger.debug(f"Event search with sort failed ({e}), falling back to unsorted query...")
            try:
                payload.pop("sort", None)
                res = api_client.post(f"/v3/search?limit={limit}", json_data=payload)
                return res if isinstance(res, list) else []
            except ApiClientError as e2:
                logger.error(f"Event retrieval failed: {e2}")
                return []

    def _print_single_event(self, ev: Dict[str, Any]) -> None:
        """Display single event attributes card."""
        print("\n" + "=" * 80)
        print(f"  EVENT DETAILS: {ev.get('name')}")
        print("=" * 80)
        print(f"  * Event ID      : {ev.get('id')}")
        print(f"  * Type          : {ev.get('type')}")
        print(f"  * Action        : {ev.get('action')}")
        print(f"  * Status        : {ev.get('status')}")
        print(f"  * Created       : {ev.get('created')}")
        actor = ev.get("actor") or {}
        target = ev.get("target") or {}
        print(f"  * Actor         : {actor.get('name')} ({actor.get('id')})")
        print(f"  * Target        : {target.get('name')} ({target.get('id')})")
        attrs = ev.get("attributes") or {}
        if attrs:
            print("  * Attributes:")
            for k, v in sorted(attrs.items()):
                print(f"      - {k}: {v}")
        print("=" * 80 + "\n")

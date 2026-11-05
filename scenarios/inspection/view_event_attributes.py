"""Inspection Scenario: View Identity Event Attributes & Audit History.
Domain: Identity & Account Inspection (Matches UI 'Events' tab).
Provides 3 retrieval modes: Last 10 events, Source-filtered events, or All historical events.
"""

from typing import Dict, Any, List, Optional
from core.base_scenario import BaseScenario
from core.context import ExecutionContext
from core.registry import register_scenario
from sailpoint.events import (
    fetch_identity_events,
    extract_event_source,
    get_correlated_sources_for_identity,
    format_events_table,
    format_single_event_card,
)
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
        logger.info(f"Starting event inspection workflow for identity '{ctx.identity_name}'...")

        mode_name = "Last 10 Events"
        source_filter: Optional[str] = None
        limit = 10

        if ctx.interactive:
            choice, source_filter, limit, mode_name = self._prompt_event_options(ctx)
            if choice == "0":
                logger.info("Event inspection cancelled by tester.")
                report = self._build_report(ctx, [], "Inspection Cancelled", "CANCELLED")
                return report

        events = fetch_identity_events(
            identity_id=ctx.identity_id,
            identity_name=ctx.identity_name,
            limit=limit,
            source_filter=source_filter,
        )

        title = f"{mode_name}: {ctx.identity_name}"
        if source_filter:
            title += f" [Source: {source_filter}]"

        print(format_events_table(events, title))

        # Interactive drill-down or pagination
        if ctx.interactive and events:
            self._handle_drilldown_loop(events)

        report = self._build_report(ctx, events, mode_name, "SUCCESS", source_filter=source_filter)
        return report

    def _prompt_event_options(self, ctx: ExecutionContext):
        """Prompt user with the 3 event fetching options."""
        while True:
            print("\n" + "=" * 80)
            print(f"  IDENTITY AUDIT EVENT INSPECTION: {ctx.identity_name}")
            print(f"  Target Source: {ctx.source_name} | State: {ctx.current_lifecycle_state}")
            print("=" * 80)
            print("  Choose an Event Retrieval Option:")
            print("  [1] Show Last 10 Events (Recent Snapshot across all sources)")
            print("  [2] Filter Events by Source (All Sources vs Specific Source)")
            print("  [3] Show All Events (Complete Audit History)")
            print("  ------------------------------------------------------------------------------")
            print("  [0] Back to Inspection Menu")
            print("=" * 80)

            choice = input("Select option [0-3]: ").strip().lower()

            if choice in ("0", "b", "back", "q"):
                return "0", None, 10, "Cancelled"

            elif choice == "1":
                return "1", None, 10, "Last 10 Events"

            elif choice == "2":
                src_filter, src_limit = self._prompt_source_filtering(ctx)
                mode_desc = f"Source Filtered ({src_filter or 'All Sources'})"
                return "2", src_filter, src_limit, mode_desc

            elif choice == "3":
                return "3", None, 250, "All Historical Events"

            else:
                print("Invalid selection. Please choose 1, 2, 3, or 0.")

    def _prompt_source_filtering(self, ctx: ExecutionContext):
        """Sub-flow for Option 2: Choose specific source or all sources, plus limit."""
        discovered_sources = get_correlated_sources_for_identity(ctx.identity_id, ctx.source)

        print("\n" + "-" * 80)
        print("  FILTER AUDIT EVENTS BY SOURCE:")
        print("  [A] All Sources (Include Identity, System & All Correlated Sources)")
        for idx, src in enumerate(discovered_sources, 1):
            src_type = f" ({src.get('type')})" if src.get('type') else ""
            print(f"  [{idx}] {src.get('name')}{src_type}")
        print("  [O] Other / Enter custom source name manually")
        print("-" * 80)

        selected_source_name: Optional[str] = None
        while selected_source_name is None:
            sel = input(f"Choose source [A / 1-{len(discovered_sources)} / O]: ").strip()
            if sel.lower() in ("a", "all", ""):
                selected_source_name = "All"
                break
            elif sel.lower() == "o":
                custom = input("Enter source name or substring to filter: ").strip()
                if custom:
                    selected_source_name = custom
                    break
            else:
                try:
                    num = int(sel) - 1
                    if 0 <= num < len(discovered_sources):
                        selected_source_name = discovered_sources[num].get("name")
                        break
                except ValueError:
                    pass
            print("Invalid source selection. Try again.")

        # Prompt for scope
        print(f"\nSelect event scope for '{selected_source_name}':")
        print("  [1] Last 10 Events")
        print("  [2] All Events")
        scope_choice = input("Choose scope [1-2] [Default: 1]: ").strip()
        limit = 250 if scope_choice == "2" else 10

        actual_filter = None if selected_source_name.lower() in ("all", "all sources") else selected_source_name
        return actual_filter, limit

    def _handle_drilldown_loop(self, events: List[Dict[str, Any]]) -> None:
        """Allow user to inspect full attributes of any event in the list."""
        while True:
            drill = input("\nEnter event # [1-{}] to view full attributes, or press Enter to return: ".format(len(events))).strip()
            if not drill:
                break
            try:
                ev_idx = int(drill) - 1
                if 0 <= ev_idx < len(events):
                    print(format_single_event_card(events[ev_idx]))
                else:
                    print("Invalid event number.")
            except ValueError:
                break

    def _build_report(
        self,
        ctx: ExecutionContext,
        events: List[Dict[str, Any]],
        mode_name: str,
        status: str,
        source_filter: Optional[str] = None,
    ) -> TestReportItem:
        """Build TestReportItem documenting the event inspection."""
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
            final_status=status,
        )

        filter_desc = f" Source: '{source_filter}'" if source_filter else " (All Sources)"
        report.validation_checks.append({
            "check": "Audit Event Log Query",
            "passed": status == "SUCCESS",
            "details": f"Retrieved {len(events)} event(s) using mode '{mode_name}'{filter_desc}.",
        })

        report.api_operations.append({
            "operation": "fetch_identity_events",
            "mode": mode_name,
            "source_filter": source_filter or "ALL",
            "events_retrieved": len(events),
        })

        return report

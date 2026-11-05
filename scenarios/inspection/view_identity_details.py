"""Inspection Scenario: View Identity Details & Attributes.
Domain: Identity & Account Inspection (Matches UI Image 1).
"""

from typing import Dict, Any
from core.base_scenario import BaseScenario
from core.context import ExecutionContext
from core.registry import register_scenario
from sailpoint.identity import format_identity_details_view
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("scenario.inspection.identity")


@register_scenario
class ViewIdentityDetailsScenario(BaseScenario):
    """Inspect complete Identity Details and raw attributes (Image 1 view)."""

    scenario_id = "inspection.identity_details"
    name = "View Identity Details & Attributes"
    category_id = "inspection"
    category_name = "Identity & Account Inspection"
    description = "Displays complete Identity Details, state, profile, and attributes bag"
    expected_ad_outcome = "Read-only inspection of identity model"
    order = 1

    def execute(self, ctx: ExecutionContext) -> TestReportItem:
        logger.info(f"Displaying Identity Details for '{ctx.identity_name}'...")
        card_text = format_identity_details_view(ctx.identity)
        print("\n" + card_text + "\n")

        report = TestReportItem(
            scenario="View Identity Details",
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
            "check": "Identity Details Inspection",
            "passed": True,
            "details": f"Successfully retrieved and displayed Identity record for '{ctx.identity_name}'.",
        })
        return report

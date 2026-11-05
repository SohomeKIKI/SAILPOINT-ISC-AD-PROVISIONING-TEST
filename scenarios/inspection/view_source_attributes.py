"""Inspection Scenario: View Raw Source Account Attributes.
Domain: Identity & Account Inspection (Matches UI Image 3).
"""

from typing import Dict, Any
from core.base_scenario import BaseScenario
from core.context import ExecutionContext
from core.registry import register_scenario
from sailpoint.accounts import get_account_on_source, get_account_by_id
from sailpoint.identity import format_account_detail_card
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("scenario.inspection.source_attrs")


@register_scenario
class ViewSourceAttributesScenario(BaseScenario):
    """Directly inspect raw source attributes on target source (Image 3 view)."""

    scenario_id = "inspection.source_attributes"
    name = "View Target Source Attributes"
    category_id = "inspection"
    category_name = "Identity & Account Inspection"
    description = "Displays the exact raw inbound feed attributes on the selected source"
    expected_ad_outcome = "Read-only inspection of source account schema attributes"
    order = 3

    def execute(self, ctx: ExecutionContext) -> TestReportItem:
        logger.info(f"Retrieving source account for '{ctx.identity_name}' on '{ctx.source_name}'...")
        acc = get_account_on_source(ctx.identity_id, ctx.source_id)

        report = TestReportItem(
            scenario="View Target Source Attributes",
            identity_id=ctx.identity_id,
            identity_name=ctx.identity_name,
            identity_email=ctx.identity_email,
            identity_profile_id=ctx.effective_profile_id,
            source_id=ctx.source_id,
            source_name=ctx.source_name,
            initial_lifecycle_state=ctx.current_lifecycle_state,
            target_lifecycle_state=ctx.current_lifecycle_state,
            resulting_lifecycle_state=ctx.current_lifecycle_state,
        )

        if not acc:
            msg = f"No account found for '{ctx.identity_name}' on source '{ctx.source_name}'."
            print(f"\n[Notice] {msg}\n")
            report.final_status = "FAILURE"
            report.error_message = msg
            report.validation_checks.append({
                "check": "Source Account Attributes Inspection",
                "passed": False,
                "details": msg,
            })
            return report

        full_acc = get_account_by_id(acc.get("id")) or acc
        card = format_account_detail_card(full_acc)
        print("\n" + card + "\n")

        report.final_status = "SUCCESS"
        report.validation_checks.append({
            "check": "Source Account Attributes Inspection",
            "passed": True,
            "details": f"Successfully displayed raw attributes for account on '{ctx.source_name}'.",
        })
        return report

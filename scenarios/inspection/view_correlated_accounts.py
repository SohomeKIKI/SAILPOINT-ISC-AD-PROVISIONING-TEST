"""Inspection Scenario: View Correlated Accounts Table & Drill-Down.
Domain: Identity & Account Inspection (Matches UI Images 2 & 3).
"""

from typing import Dict, Any
from core.base_scenario import BaseScenario
from core.context import ExecutionContext
from core.registry import register_scenario
from sailpoint.accounts import get_detailed_accounts_for_identity
from sailpoint.identity import display_account_drilldown, format_accounts_table_view
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("scenario.inspection.accounts")


@register_scenario
class ViewCorrelatedAccountsScenario(BaseScenario):
    """Inspect all accounts correlated to this identity across sources (Images 2 & 3)."""

    scenario_id = "inspection.view_accounts"
    name = "View Correlated Accounts & Attributes"
    category_id = "inspection"
    category_name = "Identity & Account Inspection"
    description = "Table of all correlated accounts with interactive drill-down into source attributes"
    expected_ad_outcome = "Read-only inspection of target and authoritative accounts"
    order = 2

    def execute(self, ctx: ExecutionContext) -> TestReportItem:
        logger.info(f"Retrieving correlated accounts for '{ctx.identity_name}'...")
        accounts = get_detailed_accounts_for_identity(ctx.identity_id)

        display_account_drilldown(
            accounts=accounts,
            identity_name=ctx.identity_name,
            interactive=ctx.interactive,
        )

        report = TestReportItem(
            scenario="View Correlated Accounts",
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
            "check": "Correlated Accounts Inspection",
            "passed": True,
            "details": f"Found and displayed {len(accounts)} correlated account(s) for '{ctx.identity_name}'.",
        })
        return report

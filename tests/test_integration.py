"""Unit and integration smoke tests for SailPoint ISC automation framework."""

import unittest
from config.settings import settings
from config.constants import LIFECYCLE_STATES, SCENARIOS
from authentication.auth_client import auth_client
from sailpoint.identity import (
    search_identities,
    get_identity_by_id,
    format_identity_card,
    format_identity_details_view,
    format_accounts_table_view,
    format_account_detail_card,
)
from sailpoint.accounts import get_account_by_id, get_detailed_accounts_for_identity
from sailpoint.identity_profiles import get_identity_profiles, get_lifecycle_states
from sailpoint.sources import get_sources, get_ad_sources
from sailpoint.roles import search_roles
from validation.identity_validation import validate_identity_state
from validation.account_validation import validate_account_status
from reporting.report_generator import ReportGenerator, TestReportItem


class TestSailPointADAutomation(unittest.TestCase):
    """Smoke test suite validating module integration with tenant APIs."""

    def test_01_authentication(self):
        """Milestone 1: Successfully obtain SailPoint OAuth access token."""
        token = auth_client.get_token()
        self.assertIsNotNone(token)
        self.assertTrue(len(token) > 20)
        self.assertTrue(auth_client.is_token_valid())

    def test_02_identity_search(self):
        """Milestone 2: Retrieve existing identities from ISC."""
        identities = search_identities("Yuki", limit=5)
        self.assertIsInstance(identities, list)
        self.assertGreater(len(identities), 0)
        user = identities[0]
        self.assertIn("id", user)
        self.assertIn("name", user)
        self.assertIn("email", user)
        self.assertIn("lifecycleState", user)

    def test_03_identity_details_and_card(self):
        """Milestones 3 & 4: Retrieve single identity details and verify formatted card."""
        identities = search_identities("Yuki", limit=1)
        self.assertTrue(len(identities) > 0)
        uid = identities[0]["id"]
        user_det = get_identity_by_id(uid)
        self.assertIsNotNone(user_det)
        card = format_identity_card(user_det)
        self.assertIn("IDENTITY DETAILS", card)
        self.assertIn(user_det["name"], card)

    def test_04_identity_profiles_and_sources(self):
        """Milestone 5: Retrieve available identity profiles and sources."""
        profiles = get_identity_profiles(limit=5)
        self.assertIsInstance(profiles, list)
        self.assertGreater(len(profiles), 0)

        sources = get_sources(limit=5)
        self.assertIsInstance(sources, list)
        self.assertGreater(len(sources), 0)

        ad_sources = get_ad_sources()
        self.assertIsInstance(ad_sources, list)

    def test_05_lifecycle_states(self):
        """Milestone 6: Retrieve and validate configured lifecycle states."""
        # Find Truist profile
        profiles = get_identity_profiles(limit=50)
        truist_prof = next((p for p in profiles if "Truist" in p.get("name", "")), profiles[0])
        states = get_lifecycle_states(truist_prof["id"])
        self.assertIsInstance(states, list)
        self.assertGreater(len(states), 0)
        tech_names = [s.get("technicalName") for s in states]
        self.assertIn("active", tech_names)

    def test_06_role_search(self):
        """Milestone 8: Search roles in tenant."""
        roles = search_roles("Analyst", limit=5)
        self.assertIsInstance(roles, list)

    def test_07_validation_and_reporting(self):
        """Milestones 10 & 11: Test validation checks and report generator output."""
        rg = ReportGenerator()
        item = TestReportItem(
            scenario=SCENARIOS["ENABLE_ACCOUNT"],
            identity_id="test-id-123",
            identity_name="Test User",
            identity_email="test.user@example.com",
            source_id="source-123",
            source_name="AD_Demo_Source",
            initial_lifecycle_state="loa",
            target_lifecycle_state="active",
            resulting_lifecycle_state="active",
            final_status="SUCCESS",
        )
        rg.add_record(item)
        json_file = rg.generate_json_report()
        md_file = rg.generate_markdown_summary()
        excel_file = rg.generate_excel_report()
        self.assertTrue(json_file.exists())
        self.assertTrue(md_file.exists())
        self.assertTrue(excel_file.exists())
        self.assertEqual(excel_file.suffix, ".xlsx")

        # Verify all 5 sheets exist in the Excel workbook
        import openpyxl
        wb = openpyxl.load_workbook(excel_file)
        self.assertEqual(
            wb.sheetnames,
            ["Executive Summary", "Scenario Master Log", "Step-by-Step Audit", "Verification Matrix", "Account Inventory"]
        )

    def test_08_account_details_and_views(self):
        """Milestone 12: Test detailed account retrieval and UI view formatters."""
        identities = search_identities("Ava Ellis", limit=1)
        self.assertTrue(len(identities) > 0)
        user = identities[0]

        # Test View 1: Identity Details View
        id_view = format_identity_details_view(user)
        self.assertIn("IDENTITY: Ava Ellis", id_view)
        self.assertIn("Identity Attributes:", id_view)

        # Test View 2: Correlated Accounts List
        accs = get_detailed_accounts_for_identity(user["id"])
        self.assertIsInstance(accs, list)
        self.assertGreater(len(accs), 0)

        tbl_view = format_accounts_table_view(accs, identity_name=user["displayName"])
        self.assertIn("CORRELATED ACCOUNTS", tbl_view)
        self.assertIn("AD_Demo_Source", tbl_view)

        # Test View 3: Single Account Drill-down Card
        acc_view = format_account_detail_card(accs[0])
        self.assertIn("SOURCE ACCOUNT:", acc_view)
        self.assertIn("Raw Source Attributes", acc_view)

    def test_09_modular_registry_and_categories(self):
        """Milestone 13: Test dynamic modular scenario registry and categories."""
        import scenarios
        from core.registry import registry

        # Verify all 4 categories exist
        categories = registry.get_categories()
        category_ids = [c[0] for c in categories]
        self.assertIn("account_management", category_ids)
        self.assertIn("lifecycle_management", category_ids)
        self.assertIn("access_management", category_ids)
        self.assertIn("inspection", category_ids)

        # Verify scenarios are registered under each category
        acc_scenarios = registry.get_scenarios_for_category("account_management")
        lc_scenarios = registry.get_scenarios_for_category("lifecycle_management")
        acc_sc_ids = [s.scenario_id for s in acc_scenarios]
        lc_sc_ids = [s.scenario_id for s in lc_scenarios]

        self.assertIn("account.create", acc_sc_ids)
        self.assertIn("account.enable", acc_sc_ids)
        self.assertIn("account.disable", acc_sc_ids)
        self.assertIn("account.unlock", acc_sc_ids)

        self.assertIn("lifecycle.active", lc_sc_ids)
        self.assertIn("lifecycle.loa", lc_sc_ids)
        self.assertIn("lifecycle.skp", lc_sc_ids)
        self.assertIn("lifecycle.ear", lc_sc_ids)
        self.assertIn("lifecycle.termination", lc_sc_ids)
        self.assertIn("lifecycle.full_demo", lc_sc_ids)

        # Verify legacy number lookups
        self.assertEqual(registry.get_scenario_by_legacy_number(1).scenario_id, "account.create")
        self.assertEqual(registry.get_scenario_by_legacy_number(6).scenario_id, "lifecycle.loa")
        self.assertEqual(registry.get_scenario_by_legacy_number(10).scenario_id, "inspection.view_accounts")

    def test_10_execution_context_and_menu_manager(self):
        """Milestone 14: Test ExecutionContext and MenuManager structure."""
        from core.context import ExecutionContext
        from core.menu_manager import MenuManager
        from core.registry import registry

        dummy_identity = {
            "id": "test-id",
            "name": "yuki.nagato",
            "displayName": "Yuki Nagato",
            "email": "yuki@example.com",
            "lifecycleState": "active",
        }
        dummy_source = {"id": "src-ad", "name": "AD_Demo_Source"}

        ctx = ExecutionContext(
            identity=dummy_identity,
            source=dummy_source,
            profile_id="prof-123",
            interactive=False,
            force_confirmed=True,
        )

        self.assertEqual(ctx.identity_name, "Yuki Nagato")
        self.assertEqual(ctx.identity_id, "test-id")
        self.assertEqual(ctx.source_name, "AD_Demo_Source")
        self.assertEqual(ctx.current_lifecycle_state, "active")

        menu = MenuManager(ctx)
        self.assertIsNotNone(menu.ctx)

    def test_11_event_fetching_options(self):
        """Milestone 15: Test event fetching service with 3 options and formatting."""
        from sailpoint.events import (
            fetch_identity_events,
            extract_event_source,
            get_correlated_sources_for_identity,
            format_events_table,
            format_single_event_card,
        )
        from scenarios.inspection.view_event_attributes import ViewEventAttributesScenario
        from core.context import ExecutionContext

        identities = search_identities("Yuki", limit=1)
        self.assertTrue(len(identities) > 0)
        user = identities[0]

        # Option 1: Last 10 events
        ev10 = fetch_identity_events(user["id"], user.get("displayName") or user.get("name"), limit=10)
        self.assertIsInstance(ev10, list)
        self.assertLessEqual(len(ev10), 10)

        # Option 2: Filter by source
        ev_filtered = fetch_identity_events(
            user["id"], user.get("displayName") or user.get("name"), limit=10, source_filter="AD_Demo_Source"
        )
        self.assertIsInstance(ev_filtered, list)

        # Option 3: All events
        ev_all = fetch_identity_events(user["id"], user.get("displayName") or user.get("name"), limit=250)
        self.assertIsInstance(ev_all, list)

        # Helper formatting checks
        tbl = format_events_table(ev10, "Test Table")
        self.assertIn("TEST TABLE", tbl)

        if ev10:
            card = format_single_event_card(ev10[0])
            self.assertIn("EVENT DETAILS", card)
            src_extracted = extract_event_source(ev10[0])
            self.assertIsInstance(src_extracted, str)

        # Test scenario execution in non-interactive mode
        ctx = ExecutionContext(
            identity=user,
            source={"id": "src-1", "name": "AD_Demo_Source"},
            profile_id="prof-1",
            interactive=False,
        )
        scen = ViewEventAttributesScenario()
        rep = scen.execute(ctx)
        self.assertEqual(rep.final_status, "SUCCESS")
        self.assertGreater(len(rep.validation_checks), 0)


if __name__ == "__main__":
    unittest.main()


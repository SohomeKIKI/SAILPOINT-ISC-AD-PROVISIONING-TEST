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
        self.assertTrue(json_file.exists())
        self.assertTrue(md_file.exists())

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


if __name__ == "__main__":
    unittest.main()


"""Main application entry point.
Coordinates the interactive 9-step AD Provisioning test flow in SailPoint Identity Security Cloud (ISC).
"""

import sys
import argparse
from typing import Optional, Dict, Any, List
from config.settings import settings
from config.constants import SCENARIOS, LIFECYCLE_METADATA
from reporting.logger import setup_logger, get_logger
from reporting.report_generator import ReportGenerator
from authentication.auth_client import auth_client, AuthenticationError
from sailpoint.identity import (
    search_identities,
    get_all_identities,
    get_identity_by_id,
    format_identity_card,
    format_identity_details_view,
    format_accounts_table_view,
    format_account_detail_card,
    display_account_drilldown,
)
from sailpoint.accounts import get_detailed_accounts_for_identity
from sailpoint.identity_profiles import (
    get_identity_profiles,
    get_lifecycle_states,
    get_identity_profile,
)
from sailpoint.sources import get_sources, get_ad_sources
import scenarios
from core.context import ExecutionContext
from core.registry import registry
from core.menu_manager import MenuManager

# Initialize application logger
setup_logger(name="sailpoint_ad_automation", log_file="execution.log")
logger = get_logger("main")


def print_banner() -> None:
    """Display application header banner."""
    print("=" * 80)
    print("      SAILPOINT IDENTITY SECURITY CLOUD (ISC) - AD PROVISIONING AUTOMATION")
    print("                       Interactive Test Framework                         ")
    print("=" * 80)
    print(f"Tenant URL : {settings.base_url}")
    print(f"Client ID  : {settings.client_id[:8]}...[REDACTED]")
    print("=" * 80 + "\n")


def authenticate_flow() -> bool:
    """Authentication: Authenticate with SailPoint ISC using PAT credentials."""
    print("[AUTH] Authenticating with SailPoint Identity Security Cloud...")
    try:
        token = auth_client.get_token()
        print(f"  -> Authentication SUCCESS. OAuth access token acquired.\n")
        return True
    except AuthenticationError as e:
        print(f"\n[ERROR] Authentication failed: {e}")
        logger.error(f"Main authentication failed: {e}")
        return False
    except ValueError as e:
        print(f"\n[ERROR] Configuration error: {e}")
        return False


def select_identity_flow(
    initial_query: Optional[str] = None,
    auto_view_accounts: bool = False,
) -> Optional[Dict[str, Any]]:
    """Step 1 & 2: Search, display, and select an identity."""
    print("[Step 1/9] Prompt for User (Search by Name, Email, or ID)")
    print("--------------------------------------------------------------------------------")

    identities: List[Dict[str, Any]] = []

    if initial_query:
        identities = search_identities(initial_query)

    while not identities:
        print("Options: Enter a user's name, email, or ID to search, or press [ENTER] to list test users:")
        query = input("  Search query > ").strip()
        if not query:
            print("  Retrieving loaded test identities from tenant...")
            identities = get_all_identities(limit=30)
            if not identities:
                print("  No identities found. Please enter a specific search query.")
                continue
        else:
            identities = search_identities(query)
            if not identities:
                print(f"  No identities matched query '{query}'. Try another search.")
                continue

    # Display list of matching identities
    print(f"\nFound {len(identities)} identity(ies):")
    print(f"{'#':<3} {'Display Name':<24} {'Email':<30} {'State':<12} {'Profile'}")
    print("-" * 85)
    for idx, user in enumerate(identities, 1):
        email_str = (user.get("email") or "N/A")[:29]
        disp_name = (user.get("displayName") or user.get("name") or "Unknown")[:23]
        state_str = (user.get("lifecycleState") or "N/A")[:11]
        prof_str = (user.get("identityProfileName") or "N/A")[:15]
        print(f"{idx:<3} {disp_name:<24} {email_str:<30} {state_str:<12} {prof_str}")
    print("-" * 85)

    selected_user: Optional[Dict[str, Any]] = None
    while not selected_user:
        if len(identities) == 1:
            choice = input(f"Select identity [1] '{identities[0].get('displayName')}'? (y/n): ").strip().lower()
            if choice == "y" or choice == "":
                selected_user = identities[0]
            else:
                return select_identity_flow()
        else:
            choice = input(f"Select user number [1-{len(identities)}] or 's' to search again: ").strip()
            if choice.lower() == "s":
                return select_identity_flow()
            try:
                sel_idx = int(choice) - 1
                if 0 <= sel_idx < len(identities):
                    selected_user = identities[sel_idx]
                else:
                    print("Invalid selection number.")
            except ValueError:
                print("Please enter a valid number or 's'.")

    # Step 2: Display identity details
    print("[Step 2/9] Retrieve User Details (Get Identity API)")
    print(format_identity_card(selected_user) + "\n")

    if auto_view_accounts:
        print("\n" + format_identity_details_view(selected_user) + "\n")
        accs = get_detailed_accounts_for_identity(selected_user.get("id"))
        display_account_drilldown(accs, identity_name=selected_user.get("displayName"), interactive=True)

    return selected_user


def select_identity_profile_flow(selected_user: Dict[str, Any]) -> str:
    """Step 3: Select or confirm the Identity Profile."""
    print("[Step 3/9] Prompt for Identity Profile")
    print("--------------------------------------------------------------------------------")
    user_prof_id = selected_user.get("identityProfileId")
    user_prof_name = selected_user.get("identityProfileName")

    if user_prof_id and user_prof_name and user_prof_name != "N/A":
        print(f"  Identity is linked to Profile: '{user_prof_name}' (ID: {user_prof_id})")
        confirm = input(f"  Use this Identity Profile? [Y/n]: ").strip().lower()
        if confirm in ("", "y", "yes", "1"):
            print(f"  Using profile: '{user_prof_name}'\n")
            return user_prof_id

    # If not confirmed or missing, list available profiles
    profiles = get_identity_profiles(limit=20)
    print("\nAvailable Identity Profiles:")
    for idx, p in enumerate(profiles, 1):
        print(f"  [{idx}] {p.get('name')} (ID: {p.get('id')})")
    
    while True:
        choice = input(f"Select Profile [1-{len(profiles)}]: ").strip()
        try:
            sel_idx = int(choice) - 1
            if 0 <= sel_idx < len(profiles):
                sel_prof = profiles[sel_idx]
                print(f"  Selected Profile: '{sel_prof.get('name')}'\n")
                return sel_prof.get("id")
        except ValueError:
            pass
        print("Invalid selection. Try again.")


def display_lifecycle_states_flow(profile_id: str) -> List[Dict[str, Any]]:
    """Step 4: Retrieve and display the profile's configured lifecycle states."""
    print("[Step 4/9] Prompt for / Retrieve Lifecycle States for Profile")
    print("--------------------------------------------------------------------------------")
    states = get_lifecycle_states(profile_id)
    if not states:
        print("  Warning: No lifecycle states returned for profile. Using standard defaults.")
        return []

    print(f"Found {len(states)} configured lifecycle states:")
    print(f"{'#':<3} {'Display Name':<20} {'Technical Name':<25} {'Expected AD Outcome'}")
    print("-" * 80)
    for idx, s in enumerate(states, 1):
        tech_name = s.get("technicalName", "")
        meta = LIFECYCLE_METADATA.get(tech_name, {})
        outcome = meta.get("expected_ad_status", "Configured in Tenant")
        print(f"{idx:<3} {s.get('name', ''):<20} {tech_name:<25} {outcome}")
    print("-" * 80 + "\n")
    return states


def select_target_source_flow(selected_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Step 6: Select the target AD provisioning source or identity source."""
    print("[Step 6/9] Prompt for Source to Test (AD Provisioning Source)")
    print("--------------------------------------------------------------------------------")

    user_src_id = selected_user.get("sourceId") if selected_user else None
    user_src_name = selected_user.get("sourceName") if selected_user else None

    if user_src_id and user_src_name and user_src_name != "N/A":
        print(f"  Identity's primary source: '{user_src_name}' (ID: {user_src_id})")
        pref = input("  Test using this source? [Y/n]: ").strip().lower()
        if pref in ("", "y", "yes", "1"):
            print(f"  Selected Source: '{user_src_name}'\n")
            return {"id": user_src_id, "name": user_src_name, "type": "IdentityPrimarySource"}

    ad_sources = get_ad_sources()
    all_sources = ad_sources if ad_sources else get_sources(limit=25)

    if ad_sources:
        print(f"\nActive Directory Sources available ({len(ad_sources)}):")
        for idx, s in enumerate(ad_sources[:20], 1):
            print(f"  [{idx}] {s.get('name')} (Type: {s.get('type')}, ID: {s.get('id')})")
    else:
        print("\nListing tenant sources:")
        for idx, s in enumerate(all_sources[:15], 1):
            print(f"  [{idx}] {s.get('name')} (Type: {s.get('type')}, ID: {s.get('id')})")

    while True:
        default_prompt = " [Default: 1]" if all_sources else ""
        choice = input(f"Select Target Source [1-{min(len(all_sources), 20)}]{default_prompt}: ").strip()
        if choice == "" and all_sources:
            selected = all_sources[0]
            print(f"  Selected Source: '{selected.get('name')}' (ID: {selected.get('id')})\n")
            return selected
        try:
            sel_idx = int(choice) - 1
            if 0 <= sel_idx < len(all_sources):
                selected = all_sources[sel_idx]
                print(f"  Selected Source: '{selected.get('name')}' (ID: {selected.get('id')})\n")
                return selected
        except ValueError:
            pass
        print("Invalid selection. Try again.")


def run_scenario_flow(
    user: Dict[str, Any],
    profile_id: str,
    source: Dict[str, Any],
    scenario_choice: Optional[int] = None,
    report_gen: Optional[ReportGenerator] = None,
) -> None:
    """Steps 7, 8, & 9: Select and execute an AD Provisioning scenario, then validate."""
    ctx = ExecutionContext(
        identity=user,
        source=source,
        profile_id=profile_id,
        report_generator=report_gen,
        interactive=True,
    )

    if scenario_choice is not None:
        # CLI direct execution mode (e.g. --scenario 1)
        scenario = registry.get_scenario_by_legacy_number(scenario_choice)
        if not scenario:
            print(f"[ERROR] Unknown scenario number: {scenario_choice}")
            return
        print(f"\n[Step 7/9] Direct Execution of Scenario: '{scenario.name}'")
        print(f"[Step 8/9] Executing '{scenario.name}' via SailPoint ISC REST APIs...")
        report_item = scenario.execute(ctx)
        if report_item and report_gen:
            report_gen.add_record(report_item)
        if report_item:
            print(f"\n[Step 9/9] Verify Provisioning Outcome & Record Execution Result")
            print(f"Scenario '{report_item.scenario}' Result: [{report_item.final_status}]")
            for check in report_item.validation_checks:
                mark = "PASS" if check.get("passed") else "FAIL"
                print(f"  - [{mark}] {check.get('check')}: {check.get('details')}")
        return

    # Interactive categorized menu mode
    menu_manager = MenuManager(ctx)
    menu_manager.run_main_menu()


def main():
    """Main execution entry point."""
    parser = argparse.ArgumentParser(
        description="API-Driven Automation of AD Provisioning Tests in SailPoint ISC."
    )
    parser.add_argument("--user", help="Search query for initial identity (name, email, or ID)")
    parser.add_argument("--scenario", type=int, help="Scenario number to execute directly (1-9)")
    parser.add_argument(
        "--view-accounts",
        action="store_true",
        help="Inspect correlated accounts and source attributes for the specified user.",
    )
    args = parser.parse_args()

    print_banner()

    # Step 0: Authentication
    if not authenticate_flow():
        sys.exit(1)

    report_generator = ReportGenerator()

    try:
        while True:
            # Step 1 & 2: Identity Selection
            selected_user = select_identity_flow(
                initial_query=args.user,
                auto_view_accounts=args.view_accounts,
            )
            if not selected_user:
                print("No identity selected. Exiting.")
                break

            if args.view_accounts and args.scenario is None:
                break

            # Step 3: Identity Profile Selection
            profile_id = select_identity_profile_flow(selected_user)

            # Step 4 & 5: Retrieve and display Lifecycle States
            display_lifecycle_states_flow(profile_id)

            # Step 6: Select Target AD Source
            target_source = select_target_source_flow(selected_user)

            # Step 7, 8, 9: Scenario execution & validation
            run_scenario_flow(
                user=selected_user,
                profile_id=profile_id,
                source=target_source,
                scenario_choice=args.scenario,
                report_gen=report_generator,
            )

            if args.scenario is not None:
                break

            session_cont = input("\nTest another identity or finish session? (t to test another / [F]inish): ").strip().lower()
            if session_cont != "t":
                break
    except (KeyboardInterrupt, EOFError):
        print("\nSession interrupted or input ended.")

    # Final reporting
    if report_generator.records:
        report_generator.print_console_summary()
        excel_path = report_generator.generate_excel_report()
        json_path = report_generator.generate_json_report()
        md_path = report_generator.generate_markdown_summary()
        print(f"Audit reports generated:")
        print(f"  Excel (Executive) : {excel_path}")
        print(f"  Markdown Summary  : {md_path}")
        print(f"  JSON (Audit Raw)  : {json_path}")
        print(f"  Logs              : {settings.logs_dir / 'execution.log'}")
    else:
        print("No test scenarios were executed in this session.")

    print("\nSession finished successfully. Exiting.")


if __name__ == "__main__":
    main()

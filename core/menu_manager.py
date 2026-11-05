"""Hierarchical, dynamic menu manager for interactive test execution."""

from typing import Optional, Dict, Any
from core.context import ExecutionContext
from core.registry import registry
from reporting.report_generator import ReportGenerator, TestReportItem
from reporting.logger import get_logger

logger = get_logger("menu_manager")


class MenuManager:
    """Manages the interactive hierarchical CLI navigation and scenario dispatch."""

    def __init__(self, ctx: ExecutionContext):
        self.ctx = ctx

    def run_main_menu(self) -> None:
        """Main loop displaying top-level categories and handling drill-down."""
        while True:
            # Refresh live identity details at the start of each menu cycle
            self.ctx.refresh_identity()

            print("\n" + "=" * 80)
            print(f"  [Step 7/9] TEST SCENARIO CATEGORY SELECTION")
            print(f"  Target User   : {self.ctx.identity_name} ({self.ctx.identity_id})")
            print(f"  Current State : {self.ctx.current_lifecycle_state}")
            print(f"  Target Source : {self.ctx.source_name}")
            print("=" * 80)

            categories = registry.get_categories()
            if not categories:
                print("No test scenario categories currently registered.\n")
                break

            for idx, (cat_id, cat_name, cat_desc) in enumerate(categories, 1):
                desc_str = f" - {cat_desc}" if cat_desc else ""
                print(f"  [{idx}] {cat_name:<32}{desc_str}")

            print("  ------------------------------------------------------------------------------")
            print("  [0] Back to Identity Selection / Finish Session")
            print("=" * 80)

            raw_choice = input(f"Select Category [1-{len(categories)}] or 0 to finish: ").strip().lower()

            if raw_choice in ("0", "b", "back", "q", "exit"):
                break

            try:
                sel_idx = int(raw_choice) - 1
                if 0 <= sel_idx < len(categories):
                    cat_id, cat_name, _ = categories[sel_idx]
                    self._run_category_sub_menu(cat_id, cat_name)
                else:
                    print("Invalid category number. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

    def _run_category_sub_menu(self, category_id: str, category_name: str) -> None:
        """Sub-menu displaying scenarios registered under the selected category."""
        while True:
            self.ctx.refresh_identity()
            scenarios = registry.get_scenarios_for_category(category_id)

            print("\n" + "=" * 80)
            print(f"  >>> CATEGORY: {category_name.upper()}")
            print(f"  Target User: {self.ctx.identity_name} | State: {self.ctx.current_lifecycle_state}")
            print("=" * 80)

            if not scenarios:
                print(f"No scenarios currently registered under '{category_name}'.")
                input("\nPress [ENTER] to return to categories...")
                break

            for idx, sc in enumerate(scenarios, 1):
                desc = f" ({sc.description})" if sc.description else ""
                print(f"  {idx:>2}. {sc.name:<32}{desc}")

            print("  ------------------------------------------------------------------------------")
            print("   0. Back to Category Menu")
            print("=" * 80)

            choice = input(f"Choose scenario [1-{len(scenarios)}] or 0 to return: ").strip().lower()

            if choice in ("0", "b", "back", "q"):
                break

            try:
                sel_idx = int(choice) - 1
                if 0 <= sel_idx < len(scenarios):
                    selected_scenario = scenarios[sel_idx]
                    self._execute_scenario(selected_scenario)
                else:
                    print("Invalid scenario selection.")
            except ValueError:
                print("Please enter a valid number.")

    def _execute_scenario(self, scenario) -> Optional[TestReportItem]:
        """Execute a selected scenario, display Step 9 outcome, and record report."""
        if not scenario.confirm_execution(self.ctx):
            return None

        print(f"\n[Step 8/9] Executing '{scenario.name}' via SailPoint ISC REST APIs...")
        report_item = scenario.execute(self.ctx)

        if report_item and self.ctx.report_generator:
            self.ctx.report_generator.add_record(report_item)

        # Step 9: Print scenario outcome and validation details
        if report_item:
            print(f"\n[Step 9/9] Verify Provisioning Outcome & Record Execution Result")
            print(f"Scenario '{report_item.scenario}' Result: [{report_item.final_status}]")
            for check in report_item.validation_checks:
                mark = "PASS" if check.get("passed") else "FAIL"
                print(f"  - [{mark}] {check.get('check')}: {check.get('details')}")

        input("\nPress [ENTER] to continue...")
        return report_item

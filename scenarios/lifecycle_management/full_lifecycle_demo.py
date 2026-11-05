"""Scenario: Full Lifecycle Transitions Demo Sequence.
Domain: Lifecycle State Management.
"""

from typing import Dict, Any, Optional
from core.base_scenario import BaseScenario
from core.context import ExecutionContext
from core.registry import register_scenario
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger
from sailpoint.identity import get_identity_by_id

from .active import run_active_lifecycle
from .skp import run_skp
from .leave_of_absence import run_leave_of_absence
from .emergency_access_removal import run_emergency_access_removal
from .termination import run_termination

logger = get_logger("scenario.lifecycle.full_demo")


@register_scenario
class FullLifecycleDemoScenario(BaseScenario):
    """Run sequential demonstration across all lifecycle states."""

    scenario_id = "lifecycle.full_demo"
    name = "Full Lifecycle Demonstration"
    category_id = "lifecycle_management"
    category_name = "Lifecycle State Management"
    description = "Sequential execution across all states: Active -> SKP -> LOA -> EAR -> Termination"
    expected_ad_outcome = "Validate AD outcomes sequentially across all configured states"
    order = 6

    def execute(self, ctx: ExecutionContext) -> TestReportItem:
        return run_full_lifecycle_demo(
            identity=ctx.identity,
            source=ctx.source,
            profile_id=ctx.effective_profile_id,
            interactive=ctx.interactive,
            force_confirmed=ctx.force_confirmed,
            report_gen=ctx.report_generator,
        )


def run_full_lifecycle_demo(
    identity: Dict[str, Any],
    source: Dict[str, Any],
    profile_id: Optional[str] = None,
    interactive: bool = True,
    force_confirmed: bool = False,
    report_gen: Optional[Any] = None,
) -> TestReportItem:
    """Execute complete lifecycle transition demonstration sequence."""
    scenario_name = "Full Lifecycle Demonstration"
    identity_id = identity.get("id")
    identity_name = identity.get("displayName") or identity.get("name")
    source_id = source.get("id")
    source_name = source.get("name")
    effective_profile_id = profile_id or identity.get("identityProfileId")

    logger.info(f"=== Starting Full Lifecycle Demonstration for '{identity_name}' on '{source_name}' ===")

    print("\n" + "=" * 80)
    print(f"  STARTING FULL LIFECYCLE TRANSITION SEQUENCE")
    print(f"  Target User: {identity_name} | Target Source: {source_name}")
    print("  Sequence   : Active -> SKP -> LOA -> EAR -> Termination")
    print("=" * 80 + "\n")

    composite_report = TestReportItem(
        scenario=scenario_name,
        identity_id=identity_id,
        identity_name=identity_name,
        identity_email=identity.get("email"),
        identity_profile_id=effective_profile_id,
        identity_profile_name=identity.get("identityProfileName"),
        source_id=source_id,
        source_name=source_name,
        initial_lifecycle_state=identity.get("lifecycleState"),
        target_lifecycle_state="terminated",
    )

    sequence = [
        ("Active", run_active_lifecycle),
        ("SKP", run_skp),
        ("LOA", run_leave_of_absence),
        ("EAR", run_emergency_access_removal),
        ("Termination", run_termination),
    ]

    all_passed = True
    for step_name, runner_fn in sequence:
        curr_user = get_identity_by_id(identity_id) or identity
        print(f">>> Executing step [{step_name}]...")
        sub_item = runner_fn(
            curr_user,
            source,
            effective_profile_id,
            interactive=False,
            force_confirmed=True,
        )
        if report_gen:
            report_gen.add_record(sub_item)

        composite_report.api_operations.extend(sub_item.api_operations)
        composite_report.validation_checks.extend(sub_item.validation_checks)

        passed = sub_item.final_status == "SUCCESS"
        mark = "PASS" if passed else "FAIL"
        print(f"    * Step [{step_name}] result: [{mark}]\n")
        if not passed:
            all_passed = False

    composite_report.final_status = "SUCCESS" if all_passed else "FAILURE"
    composite_report.resulting_lifecycle_state = "terminated"
    logger.info(f"=== Completed Full Lifecycle Demonstration | Outcome: {composite_report.final_status} ===")
    return composite_report

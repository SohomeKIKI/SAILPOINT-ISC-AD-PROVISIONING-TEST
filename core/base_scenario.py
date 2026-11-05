"""Abstract base class for all test scenarios in the SailPoint testing platform."""

from abc import ABC, abstractmethod
from typing import Optional
from core.context import ExecutionContext
from reporting.report_generator import TestReportItem
from reporting.logger import get_logger

logger = get_logger("base_scenario")


class BaseScenario(ABC):
    """Abstract base class defining the contract for any test scenario."""

    scenario_id: str
    name: str
    category_id: str
    category_name: str
    description: str = ""
    expected_ad_outcome: str = ""
    order: int = 100
    requires_confirmation: bool = False
    confirmation_keyword: Optional[str] = None

    def confirm_execution(self, ctx: ExecutionContext) -> bool:
        """Handle mandatory confirmation prompt for destructive or high-impact actions."""
        if not self.requires_confirmation or ctx.force_confirmed or not ctx.interactive:
            return True

        print("\n" + "=" * 75)
        print(f"  SAFETY CONFIRMATION REQUIRED: {self.name.upper()}")
        print(f"  Target User     : {ctx.identity_name}")
        print(f"  Target Source   : {ctx.source_name}")
        print(f"  Expected Outcome: {self.expected_ad_outcome}")
        print("=" * 75)

        if self.confirmation_keyword:
            prompt_msg = f"Type '{self.confirmation_keyword}' to proceed, or press Enter to cancel: "
            val = input(prompt_msg).strip()
            if val != self.confirmation_keyword:
                print("Operation cancelled: Confirmation keyword did not match.\n")
                return False
            return True
        else:
            prompt_msg = f"Proceed with executing '{self.name}'? (y/N): "
            ans = input(prompt_msg).strip().lower()
            return ans in ("y", "yes")

    @abstractmethod
    def execute(self, ctx: ExecutionContext) -> TestReportItem:
        """Execute the test scenario and return a populated TestReportItem."""
        pass


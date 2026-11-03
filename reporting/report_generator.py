"""Generates structured execution reports in JSON, Markdown, and console formats."""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from config.settings import settings
from reporting.logger import get_logger

logger = get_logger("reporting")


@dataclass
class TestReportItem:
    """Represents a single scenario execution outcome for auditing."""

    scenario: str
    identity_id: str
    identity_name: str
    identity_email: Optional[str] = None
    identity_profile_id: Optional[str] = None
    identity_profile_name: Optional[str] = None
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    initial_lifecycle_state: Optional[str] = None
    target_lifecycle_state: Optional[str] = None
    resulting_lifecycle_state: Optional[str] = None
    role_info: Optional[Dict[str, Any]] = None
    api_operations: List[Dict[str, Any]] = field(default_factory=list)
    validation_checks: List[Dict[str, Any]] = field(default_factory=list)
    final_status: str = "PENDING"  # SUCCESS, FAILURE, ERROR
    error_message: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ReportGenerator:
    """Manages test execution records and generates exportable audit reports."""

    def __init__(self):
        self.records: List[TestReportItem] = []
        self.session_start = datetime.now()

    def add_record(self, record: TestReportItem) -> None:
        """Add a test record to the current session."""
        self.records.append(record)
        logger.info(
            f"Test record added: Scenario='{record.scenario}', "
            f"User='{record.identity_name}', Status={record.final_status}"
        )

    def generate_json_report(self) -> Path:
        """Export session execution records to a timestamped JSON file."""
        timestamp_str = self.session_start.strftime("%Y-%m-%d_%H%M%S")
        filename = f"test_report_{timestamp_str}.json"
        target_path = Path(settings.reports_dir) / filename

        report_payload = {
            "title": "SailPoint ISC AD Provisioning Automation Test Report",
            "session_start": self.session_start.strftime("%Y-%m-%d %H:%M:%S"),
            "session_end": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": len(self.records),
            "passed": sum(1 for r in self.records if r.final_status == "SUCCESS"),
            "failed": sum(1 for r in self.records if r.final_status == "FAILURE"),
            "errors": sum(1 for r in self.records if r.final_status == "ERROR"),
            "records": [r.to_dict() for r in self.records],
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2)

        logger.info(f"JSON test report generated: {target_path}")
        return target_path

    def generate_markdown_summary(self) -> Path:
        """Generate a human-readable Markdown summary report."""
        timestamp_str = self.session_start.strftime("%Y-%m-%d_%H%M%S")
        filename = f"test_summary_{timestamp_str}.md"
        target_path = Path(settings.reports_dir) / filename

        passed = sum(1 for r in self.records if r.final_status == "SUCCESS")
        failed = sum(1 for r in self.records if r.final_status == "FAILURE")
        errors = sum(1 for r in self.records if r.final_status == "ERROR")

        lines = [
            "# SailPoint ISC AD Provisioning Test Execution Summary",
            f"**Session Date**: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Overall Results",
            f"- **Total Tests Executed**: {len(self.records)}",
            f"- **Passed (SUCCESS)**: {passed}",
            f"- **Failed (FAILURE)**: {failed}",
            f"- **Errors (ERROR)**: {errors}",
            "",
            "## Executed Scenarios",
            "| # | Scenario | Identity | Profile | Source | Lifecycle Transition | Final Status |",
            "|---|---|---|---|---|---|---|",
        ]

        for i, rec in enumerate(self.records, 1):
            transition = f"{rec.initial_lifecycle_state or 'N/A'} -> {rec.resulting_lifecycle_state or rec.target_lifecycle_state or 'N/A'}"
            status_badge = f"**{rec.final_status}**"
            lines.append(
                f"| {i} | {rec.scenario} | {rec.identity_name} | {rec.identity_profile_name or 'N/A'} | "
                f"{rec.source_name or 'N/A'} | {transition} | {status_badge} |"
            )

        lines.append("")
        lines.append("## Detailed Scenario Verifications")
        for i, rec in enumerate(self.records, 1):
            lines.append(f"### {i}. {rec.scenario} - {rec.identity_name}")
            lines.append(f"- **Identity ID**: `{rec.identity_id}`")
            lines.append(f"- **Email**: `{rec.identity_email or 'N/A'}`")
            lines.append(f"- **Source**: {rec.source_name or 'N/A'} (`{rec.source_id or 'N/A'}`)")
            if rec.role_info:
                lines.append(
                    f"- **Role Info**: Name='{rec.role_info.get('role_name')}', "
                    f"ID=`{rec.role_info.get('role_id')}`, "
                    f"AccessRequestID=`{rec.role_info.get('access_request_id')}`, "
                    f"RoleSource='{rec.role_info.get('role_source_name')}'"
                )
            lines.append(f"- **Status**: `{rec.final_status}`")
            if rec.error_message:
                lines.append(f"- **Error / Warning**: {rec.error_message}")
            if rec.validation_checks:
                lines.append("- **Validation Checks**:")
                for check in rec.validation_checks:
                    c_status = "PASS" if check.get("passed") else "FAIL"
                    lines.append(f"  - [{c_status}] {check.get('check')}: {check.get('details')}")
            lines.append("")

        with open(target_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Markdown test report generated: {target_path}")
        return target_path

    def print_console_summary(self) -> None:
        """Print a formatted summary table to stdout."""
        print("\n" + "=" * 80)
        print("               SAILPOINT ISC AD PROVISIONING TEST SUMMARY")
        print("=" * 80)
        print(f"Total Scenarios Executed: {len(self.records)}")
        print(f"  Passed : {sum(1 for r in self.records if r.final_status == 'SUCCESS')}")
        print(f"  Failed : {sum(1 for r in self.records if r.final_status == 'FAILURE')}")
        print(f"  Errors : {sum(1 for r in self.records if r.final_status == 'ERROR')}")
        print("-" * 80)
        print(f"{'#':<3} {'Scenario':<22} {'Identity':<20} {'Status':<10} {'Details'}")
        print("-" * 80)
        for i, rec in enumerate(self.records, 1):
            detail = rec.error_message if rec.error_message else "Checks passed"
            print(f"{i:<3} {rec.scenario[:21]:<22} {rec.identity_name[:19]:<20} {rec.final_status:<10} {detail[:25]}")
        print("=" * 80 + "\n")


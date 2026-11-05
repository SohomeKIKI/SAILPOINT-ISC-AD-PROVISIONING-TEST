"""Builds an enterprise-grade Architecture, System Design, and Component Reference PDF.

Target Audience: Associate Directors, Enterprise IAM Architects, QA Leads.
Generated Document: docs/ARCHITECTURE_SYSTEM_DESIGN.pdf and ARCHITECTURE_SYSTEM_DESIGN.pdf
"""

import sys
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page count."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Omit header and footer on cover page (Page 1)
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#475569"))

        # Running Header
        header_text = "SailPoint ISC - AD Provisioning Automation | System Architecture & Technical Design"
        self.drawString(36, 11 * inch - 28, header_text)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(36, 11 * inch - 32, 8.5 * inch - 36, 11 * inch - 32)

        # Running Footer
        footer_left = "INTERNAL USE ONLY - ENTERPRISE IAM QUALITY ASSURANCE SPECIFICATION"
        footer_right = f"Page {self._pageNumber} of {page_count}"
        self.drawString(36, 25, footer_left)
        self.drawRightString(8.5 * inch - 36, 25, footer_right)
        self.line(36, 35, 8.5 * inch - 36, 35)

        self.restoreState()


def create_architecture_pdf(output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=42,
    )

    styles = getSampleStyleSheet()

    # Corporate Colors
    NAVY_DARK = colors.HexColor("#0F2942")
    SLATE_NAVY = colors.HexColor("#1E3A8A")
    SLATE_DARK = colors.HexColor("#1E293B")
    TEXT_MAIN = colors.HexColor("#0F172A")
    TEXT_MUTED = colors.HexColor("#475569")
    BG_LIGHT = colors.HexColor("#F8FAFC")
    BG_CARD = colors.HexColor("#F1F5F9")
    BORDER_COLOR = colors.HexColor("#CBD5E1")
    ACCENT_GREEN = colors.HexColor("#166534")

    # Typography Styles
    title_style = ParagraphStyle(
        "CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.white,
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#E2E8F0"),
        alignment=1,
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=NAVY_DARK,
        spaceBefore=12,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "SectionH2",
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=SLATE_NAVY,
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=TEXT_MAIN,
        spaceAfter=4,
    )
    body_bold = ParagraphStyle(
        "BodyDarkBold",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11.5,
        textColor=TEXT_MAIN,
    )
    mono_style = ParagraphStyle(
        "CodeMono",
        fontName="Courier",
        fontSize=7.5,
        leading=9.5,
        textColor=SLATE_DARK,
    )
    th_style = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1,
    )
    tc_style = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=TEXT_MAIN,
    )
    tc_bold = ParagraphStyle(
        "TableCellBold",
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=TEXT_MAIN,
    )
    tc_mono = ParagraphStyle(
        "TableCellMono",
        fontName="Courier",
        fontSize=7.5,
        leading=9.5,
        textColor=SLATE_DARK,
    )

    story = []

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 20))

    banner_data = [
        [Paragraph("ENTERPRISE IAM QUALITY ASSURANCE & PROVISIONING GOVERNANCE", ParagraphStyle("OrgHeader", fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor("#93C5FD"), alignment=1))],
        [Spacer(1, 6)],
        [Paragraph("SAILPOINT IDENTITY SECURITY CLOUD (ISC)<br/>ACTIVE DIRECTORY PROVISIONING AUTOMATION", title_style)],
        [Spacer(1, 8)],
        [Paragraph("System Architecture, Technical Design Specification, & Exhaustive Component Reference", subtitle_style)],
        [Spacer(1, 10)],
    ]
    banner_table = Table(banner_data, colWidths=[7.5 * inch])
    banner_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY_DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(banner_table)

    story.append(Spacer(1, 18))

    # Executive Metadata Card
    meta_data = [
        [Paragraph("Document Title", tc_bold), Paragraph("System Architecture & Component Reference Manual", tc_style), Paragraph("Framework Version", tc_bold), Paragraph("v2.0 (Enterprise Modular Architecture)", tc_style)],
        [Paragraph("Target Environment", tc_bold), Paragraph("SailPoint ISC Tenant (EU-Partner28)", tc_style), Paragraph("Target Directory", tc_bold), Paragraph("Active Directory (AD_Demo_Source)", tc_style)],
        [Paragraph("Target Audience", tc_bold), Paragraph("Associate Directors, IAM Architects, QA Engineers", tc_style), Paragraph("Authoritative Source", tc_bold), Paragraph("Delimited_Employees (HR Feed)", tc_style)],
        [Paragraph("Publication Date", tc_bold), Paragraph(datetime.now().strftime("%B %d, %Y"), tc_style), Paragraph("Classification", tc_bold), Paragraph("INTERNAL USE ONLY - IAM AUDIT ARTIFACT", tc_bold)],
    ]
    meta_table = Table(meta_data, colWidths=[1.4 * inch, 2.35 * inch, 1.4 * inch, 2.35 * inch])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 16))

    # Executive Overview Box
    exec_summary_html = (
        "<b>EXECUTIVE MANDATE & SYSTEM OVERVIEW:</b><br/>"
        "This architectural specification defines the technical design, domain structure, verification mechanics, "
        "and component hierarchy of the <b>SailPoint ISC Active Directory (AD) Provisioning Automation Framework</b>. "
        "The system standardizes end-to-end testing of identity lifecycle states, account provisioning, and access request "
        "governance without manual UI overhead. It executes programmatic REST API interactions against SailPoint ISC, "
        "enforces a 4-tier technical verification pipeline against downstream target directories, and produces executive "
        "analytical audit workbooks for leadership compliance review."
    )
    exec_table = Table([[Paragraph(exec_summary_html, body_style)]], colWidths=[7.5 * inch])
    exec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#3B82F6")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(exec_table)

    story.append(Spacer(1, 14))

    # Core Value Pillars Table
    story.append(Paragraph("KEY ARCHITECTURAL PILLARS", h2_style))
    pillars_data = [
        [Paragraph("Pillar", th_style), Paragraph("Design Principle", th_style), Paragraph("Operational Impact", th_style)],
        [
            Paragraph("Zero UI Overhead", tc_bold),
            Paragraph("100% API-driven execution via official SailPoint ISC v3 and Beta REST endpoints with OAuth2 token caching.", tc_style),
            Paragraph("Replaces hours of manual browser clicks with deterministic, repeatable, scripted testing cycles.", tc_style),
        ],
        [
            Paragraph("Pluggable Core Engine", tc_bold),
            Paragraph("Open-Closed design decoupling ExecutionContext, BaseScenario, and ScenarioRegistry with dynamic discovery.", tc_style),
            Paragraph("Zero blast-radius. New tenant scenarios or use cases drop in without modifying runner or CLI code.", tc_style),
        ],
        [
            Paragraph("Multi-Tier Verification", tc_bold),
            Paragraph("4-tier validation pipeline: Task Polling -> Live Identity State -> Account Status -> Policy Outcome.", tc_style),
            Paragraph("Guarantees that downstream Active Directory accounts actually reflect upstream identity governance policies.", tc_style),
        ],
        [
            Paragraph("Institutional Reporting", tc_bold),
            Paragraph("Automated generation of 5-tab analytical Excel workbooks, executive Markdown summaries, and JSON audit logs.", tc_style),
            Paragraph("Delivers zero-emoji, formal corporate artifacts ready for Associate Director and regulatory audit review.", tc_style),
        ],
    ]
    pillars_table = Table(pillars_data, colWidths=[1.4 * inch, 3.1 * inch, 3.0 * inch])
    pillars_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SLATE_NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
    ]))
    story.append(pillars_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 1: SYSTEM CONTEXT & ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("1. HIGH-LEVEL SYSTEM ARCHITECTURE & INTEGRATION CONTEXT", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY_DARK, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "The framework functions as an automated test and verification layer positioned between enterprise quality engineers "
        "and SailPoint Identity Security Cloud (ISC). It coordinates with the tenant's REST APIs, orchestrates lifecycle transitions, "
        "monitors backend task execution queues, and asserts downstream directory state.",
        body_style
    ))

    # Architecture Context Diagram (Table format)
    ctx_diagram_data = [
        [Paragraph("Layer", th_style), Paragraph("Component", th_style), Paragraph("Protocol / Interface", th_style), Paragraph("Core Responsibilities", th_style)],
        [
            Paragraph("Presentation", tc_bold),
            Paragraph("Interactive CLI & MenuManager", tc_style),
            Paragraph("CLI Console (stdin/stdout)", tc_mono),
            Paragraph("2-Tier categorized navigation, identity search prompts, parameter inputs, and execution verification.", tc_style),
        ],
        [
            Paragraph("Core Engine", tc_bold),
            Paragraph("core/ Execution Runtime", tc_style),
            Paragraph("Python In-Memory Context", tc_mono),
            Paragraph("ExecutionContext runtime model, BaseScenario abstraction, dynamic auto-discovery registry, and dispatch.", tc_style),
        ],
        [
            Paragraph("Domain Logic", tc_bold),
            Paragraph("scenarios/ Modules", tc_style),
            Paragraph("Modular Scenario Classes", tc_mono),
            Paragraph("Domain-isolated implementations for Account Management, Lifecycle States, Role Requests, and Inspection.", tc_style),
        ],
        [
            Paragraph("API Client", tc_bold),
            Paragraph("sailpoint/ API Services", tc_style),
            Paragraph("HTTPS REST / OAuth 2.0 Bearer", tc_mono),
            Paragraph("Token acquisition, automatic refresh, retry logic with exponential backoff, rate limiting, and log redaction.", tc_style),
        ],
        [
            Paragraph("Identity Cloud", tc_bold),
            Paragraph("SailPoint ISC Tenant", tc_style),
            Paragraph("v3 & Beta REST Endpoints", tc_mono),
            Paragraph("Identity repository, lifecycle engine, provisioning task scheduler, and search indexing.", tc_style),
        ],
        [
            Paragraph("Target Directory", tc_bold),
            Paragraph("Active Directory Source", tc_style),
            Paragraph("VA / SCIM / RPC Connector", tc_mono),
            Paragraph("Downstream account provisioning, account enablement/disablement, userAccountControl, and group membership.", tc_style),
        ],
        [
            Paragraph("Audit & Reports", tc_bold),
            Paragraph("reporting/ Subsystem", tc_style),
            Paragraph("Excel (openpyxl) / JSON / MD", tc_mono),
            Paragraph("Generates 5-tab analytical Excel workbooks, Markdown executive summaries, and sanitized execution logs.", tc_style),
        ],
    ]
    ctx_table = Table(ctx_diagram_data, colWidths=[1.1 * inch, 1.8 * inch, 1.8 * inch, 2.8 * inch])
    ctx_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_DARK),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
    ]))
    story.append(ctx_table)

    story.append(Spacer(1, 12))

    # =========================================================================
    # SECTION 2: THE 9-STEP END-TO-END WORKFLOW
    # =========================================================================
    story.append(Paragraph("2. END-TO-END 9-STEP TESTING WORKFLOW", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY_DARK, spaceBefore=2, spaceAfter=8))

    flow_data = [
        [Paragraph("Step", th_style), Paragraph("Workflow Phase", th_style), Paragraph("Target API Endpoint", th_style), Paragraph("Operational Function", th_style)],
        [Paragraph("Step 0", tc_bold), Paragraph("OAuth2 Authentication", tc_style), Paragraph("POST /oauth/token", tc_mono), Paragraph("Acquires Bearer token using client_id and client_secret from .env; caches in memory.", tc_style)],
        [Paragraph("Step 1", tc_bold), Paragraph("Prompt for User", tc_style), Paragraph("POST /v3/search", tc_mono), Paragraph("Prompts tester for Name, Email, or ID; lists matching test identities loaded in tenant.", tc_style)],
        [Paragraph("Step 2", tc_bold), Paragraph("Retrieve User Details", tc_style), Paragraph("GET /beta/identities/{id}", tc_mono), Paragraph("Displays clean Identity Card with profile, email, state, and primary source.", tc_style)],
        [Paragraph("Step 3", tc_bold), Paragraph("Confirm Identity Profile", tc_style), Paragraph("GET /v3/identity-profiles", tc_mono), Paragraph("Defaults to user's assigned profile (e.g. Truist Employee Profile) or allows selection.", tc_style)],
        [Paragraph("Step 4 & 5", tc_bold), Paragraph("Inspect Lifecycle States", tc_style), Paragraph("GET .../lifecycle-states", tc_mono), Paragraph("Dynamically queries profile's configured states (preHire, active, skp, ear, loa, terminated).", tc_style)],
        [Paragraph("Step 6", tc_bold), Paragraph("Select Target Source", tc_style), Paragraph("GET /v3/sources", tc_mono), Paragraph("Defaults to AD_Demo_Source; displays available Active Directory connectors.", tc_style)],
        [Paragraph("Step 7", tc_bold), Paragraph("Choose Test Scenario", tc_style), Paragraph("Interactive MenuManager", tc_mono), Paragraph("Displays 2-tier categorized menu across Account, Lifecycle, Access, and Inspection.", tc_style)],
        [Paragraph("Step 8", tc_bold), Paragraph("Execute Scenario", tc_style), Paragraph("POST /v3/provisioning /set-state", tc_mono), Paragraph("Triggers state change, direct account enable/disable/create, or role request.", tc_style)],
        [Paragraph("Step 9", tc_bold), Paragraph("4-Tier Validation & Audit", tc_style), Paragraph("GET /beta/account-activities", tc_mono), Paragraph("Polls task completion, validates live identity state, asserts AD account status, and logs report.", tc_style)],
    ]
    flow_table = Table(flow_data, colWidths=[0.8 * inch, 1.8 * inch, 2.0 * inch, 2.9 * inch])
    flow_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SLATE_NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
    ]))
    story.append(flow_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 3: EXTENSIBLE MODULAR CORE ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("3. EXTENSIBLE 2-TIER MODULAR CORE ARCHITECTURE", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY_DARK, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "To satisfy enterprise scalability across multiple client tenants, heterogeneous Active Directory environments, "
        "and evolving governance use cases, the framework decouples execution runtime from individual test scenarios. "
        "The architecture adheres strictly to the <b>Open-Closed Principle</b> (open for extension, closed for modification).",
        body_style
    ))

    core_comp_data = [
        [Paragraph("Core Class / File", th_style), Paragraph("Architectural Pattern", th_style), Paragraph("Technical Role & Extensibility Mechanism", th_style)],
        [
            Paragraph("BaseScenario<br/>(core/base_scenario.py)", tc_mono),
            Paragraph("Abstract Template Method", tc_bold),
            Paragraph("Abstract base class defining required scenario attributes (scenario_id, name, category_id, order) and lifecycle hooks (confirm_execution, execute). Ensures consistent signature and behavior.", tc_style),
        ],
        [
            Paragraph("ExecutionContext<br/>(core/context.py)", tc_mono),
            Paragraph("Context Object / Facade", tc_bold),
            Paragraph("Encapsulates mutable session state (identity, source, profile_id, report_generator, interactive, force_confirmed). Provides refresh_identity() helper to eliminate stale data caching.", tc_style),
        ],
        [
            Paragraph("ScenarioRegistry<br/>(core/registry.py)", tc_mono),
            Paragraph("Service Locator / Registry", tc_bold),
            Paragraph("Dynamic central catalog. Scenarios register via @register_scenario decorator. Organizes scenarios by category, sorts by execution order, and maps legacy CLI numbers (1-10) for backward compatibility.", tc_style),
        ],
        [
            Paragraph("MenuManager<br/>(core/menu_manager.py)", tc_mono),
            Paragraph("2-Tier Hierarchical Controller", tc_bold),
            Paragraph("Renders dynamic top-level category menu and sub-menus. Handles interactive selection, confirmation prompts, Step 8 execution dispatch, and Step 9 validation rendering.", tc_style),
        ],
    ]
    core_comp_table = Table(core_comp_data, colWidths=[2.0 * inch, 1.8 * inch, 3.7 * inch])
    core_comp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_DARK),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
    ]))
    story.append(core_comp_table)

    story.append(Spacer(1, 10))

    # Blueprint Callout
    story.append(Paragraph("BLUEPRINT: HOW TO ADD ANY FUTURE TEST SCENARIO (ZERO BLAST-RADIUS)", h2_style))
    blueprint_code = (
        "from core.base_scenario import BaseScenario<br/>"
        "from core.context import ExecutionContext<br/>"
        "from core.registry import register_scenario<br/>"
        "from reporting.report_generator import TestReportItem<br/><br/>"
        "<b>@register_scenario</b><br/>"
        "class ParentalLeaveScenario(BaseScenario):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;scenario_id = 'lifecycle.parental_leave'<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;name = 'Parental Leave - Suspension'<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;category_id = 'lifecycle_management'<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;expected_ad_outcome = 'Suspend AD account and disable access'<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;order = 7<br/><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;def execute(self, ctx: ExecutionContext) -> TestReportItem:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# Custom test logic here...<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;return report"
    )
    bp_table = Table([[Paragraph(blueprint_code, mono_style)]], colWidths=[7.5 * inch])
    bp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#64748B")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(bp_table)

    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 4: DOMAIN SCENARIO CATEGORIZATION
    # =========================================================================
    story.append(Paragraph("4. DOMAIN TEST SCENARIOS TAXONOMY", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY_DARK, spaceBefore=2, spaceAfter=8))

    tax_data = [
        [Paragraph("Category", th_style), Paragraph("Scenario ID", th_style), Paragraph("Display Name", th_style), Paragraph("Expected Active Directory Outcome", th_style)],
        [
            Paragraph("Account Management", tc_bold),
            Paragraph("account.create", tc_mono),
            Paragraph("Create Target Account", tc_style),
            Paragraph("Creates and enables a new AD account on the target source via /v3/accounts.", tc_style),
        ],
        [
            Paragraph("Account Management", tc_bold),
            Paragraph("account.enable", tc_mono),
            Paragraph("Enable Account", tc_style),
            Paragraph("Explicitly enables target AD account via /v3/accounts/{id}/enable.", tc_style),
        ],
        [
            Paragraph("Account Management", tc_bold),
            Paragraph("account.disable", tc_mono),
            Paragraph("Disable Account", tc_style),
            Paragraph("Explicitly disables target AD account via /v3/accounts/{id}/disable.", tc_style),
        ],
        [
            Paragraph("Account Management", tc_bold),
            Paragraph("account.unlock", tc_mono),
            Paragraph("Unlock Account", tc_style),
            Paragraph("Clears lockout flag (userAccountControl) via /v3/accounts/{id}/unlock.", tc_style),
        ],
        [
            Paragraph("Lifecycle Management", tc_bold),
            Paragraph("lifecycle.active", tc_mono),
            Paragraph("Active (Onboarding / Rehire)", tc_style),
            Paragraph("Applies active state; triggers onboarding policy and enables standard AD access.", tc_style),
        ],
        [
            Paragraph("Lifecycle Management", tc_bold),
            Paragraph("lifecycle.loa", tc_mono),
            Paragraph("Leave of Absence - LOA", tc_style),
            Paragraph("Applies loa state; disables AD account and suspends access while retaining attributes.", tc_style),
        ],
        [
            Paragraph("Lifecycle Management", tc_bold),
            Paragraph("lifecycle.skp", tc_mono),
            Paragraph("Sabbatical - SKP", tc_style),
            Paragraph("Standardized project abbreviation SKP. Suspends AD access per tenant policy.", tc_style),
        ],
        [
            Paragraph("Lifecycle Management", tc_bold),
            Paragraph("lifecycle.ear", tc_mono),
            Paragraph("Emergency Access Removal (EAR)", tc_style),
            Paragraph("High-impact security transition requiring confirmation; immediately revokes critical access.", tc_style),
        ],
        [
            Paragraph("Lifecycle Management", tc_bold),
            Paragraph("lifecycle.termination", tc_mono),
            Paragraph("Employment Termination", tc_style),
            Paragraph("Requires explicit 'TERMINATE' prompt; revokes all entitlements and disables/removes AD account.", tc_style),
        ],
        [
            Paragraph("Lifecycle Management", tc_bold),
            Paragraph("lifecycle.full_demo", tc_mono),
            Paragraph("Full Lifecycle Demonstration", tc_style),
            Paragraph("Sequential end-to-end execution: Active -> SKP -> LOA -> EAR -> Termination.", tc_style),
        ],
        [
            Paragraph("Access Management", tc_bold),
            Paragraph("access.role_request", tc_mono),
            Paragraph("Role Request (Source Validated)", tc_style),
            Paragraph("Inspects role's access profiles; validates target source match before submission.", tc_style),
        ],
        [
            Paragraph("Inspection", tc_bold),
            Paragraph("inspection.identity_details", tc_mono),
            Paragraph("View Identity Details & Attributes", tc_style),
            Paragraph("Read-only inspection of identity model, email, profile, and attributes (Image 1 view).", tc_style),
        ],
        [
            Paragraph("Inspection", tc_bold),
            Paragraph("inspection.view_accounts", tc_mono),
            Paragraph("View Correlated Accounts & Attributes", tc_style),
            Paragraph("Summary table of all correlated accounts (AD, Delimited, IdentityNow) (Image 2 view).", tc_style),
        ],
        [
            Paragraph("Inspection", tc_bold),
            Paragraph("inspection.source_attributes", tc_mono),
            Paragraph("View Target Source Attributes", tc_style),
            Paragraph("Direct drill-down into target AD account's raw schema attributes (Image 3 view).", tc_style),
        ],
        [
            Paragraph("Inspection", tc_bold),
            Paragraph("inspection.event_attributes", tc_mono),
            Paragraph("View Identity Event Attributes", tc_style),
            Paragraph("Audit trail with 3 options: Last 10 events, source-filtered events, or complete history.", tc_style),
        ],
    ]
    tax_table = Table(tax_data, colWidths=[1.4 * inch, 1.4 * inch, 1.8 * inch, 2.9 * inch])
    tax_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SLATE_NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
    ]))
    story.append(tax_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 5: COMPLETE FILE-BY-FILE COMPONENT REFERENCE
    # =========================================================================
    story.append(Paragraph("5. EXHAUSTIVE FILE-BY-FILE COMPONENT REFERENCE", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY_DARK, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "This section documents every file in the codebase, detailing its purpose, architectural responsibility, "
        "and integration points within the framework.",
        body_style
    ))

    # File Reference Table
    files_ref_data = [
        [Paragraph("Package / File Path", th_style), Paragraph("Primary Responsibility & Operational Purpose", th_style), Paragraph("Why It Is Used", th_style)],
        # Root
        [Paragraph("main.py", tc_mono), Paragraph("Main CLI coordinator orchestrating the 9-step workflow from authentication to final audit report generation.", tc_style), Paragraph("Central user interface and script entry point.", tc_style)],
        [Paragraph("requirements.txt", tc_mono), Paragraph("Defines production package dependencies (requests, python-dotenv, openpyxl).", tc_style), Paragraph("Enables single-command dependency installation via pip.", tc_style)],
        [Paragraph(".env.example", tc_mono), Paragraph("Template documenting required environment variables (SAILPOINT_BASE_URL, CLIENT_ID, CLIENT_SECRET).", tc_style), Paragraph("Allows secure credential configuration without exposing secrets.", tc_style)],
        [Paragraph(".gitignore", tc_mono), Paragraph("Exclusion rules protecting secrets (.env), caches (__pycache__), and logs/reports from Git.", tc_style), Paragraph("Prevents accidental leaks of PAT tokens or corporate audit logs.", tc_style)],
        # Core
        [Paragraph("core/base_scenario.py", tc_mono), Paragraph("Abstract base class BaseScenario enforcing standard attributes and execution methods.", tc_style), Paragraph("Guarantees uniform contract for all test scenarios.", tc_style)],
        [Paragraph("core/context.py", tc_mono), Paragraph("ExecutionContext runtime model maintaining identity, source, profile, and reporter references.", tc_style), Paragraph("Avoids parameter proliferation across scenario methods.", tc_style)],
        [Paragraph("core/registry.py", tc_mono), Paragraph("ScenarioRegistry and @register_scenario decorator providing dynamic discovery.", tc_style), Paragraph("Decouples scenario registration from runner code.", tc_style)],
        [Paragraph("core/menu_manager.py", tc_mono), Paragraph("MenuManager managing 2-tier hierarchical CLI navigation and scenario dispatch.", tc_style), Paragraph("Replaces flat lists with organized category navigation.", tc_style)],
        # Scenarios - Account
        [Paragraph("scenarios/account_management/<br/>create_account.py", tc_mono), Paragraph("Tests account creation via /v3/accounts if not existing, applies active state.", tc_style), Paragraph("Validates initial AD onboarding provisioning.", tc_style)],
        [Paragraph("scenarios/account_management/<br/>enable_account.py", tc_mono), Paragraph("Explicitly invokes /v3/accounts/{id}/enable and validates enabled status.", tc_style), Paragraph("Validates explicit account restoration/enablement.", tc_style)],
        [Paragraph("scenarios/account_management/<br/>disable_account.py", tc_mono), Paragraph("Explicitly invokes /v3/accounts/{id}/disable and validates disabled status.", tc_style), Paragraph("Validates explicit account disablement.", tc_style)],
        [Paragraph("scenarios/account_management/<br/>unlock_account.py", tc_mono), Paragraph("Invokes /v3/accounts/{id}/unlock and clears AD lockout bitmask.", tc_style), Paragraph("Validates lockout remediation on AD accounts.", tc_style)],
        # Scenarios - Lifecycle
        [Paragraph("scenarios/lifecycle_management/<br/>active.py", tc_mono), Paragraph("Applies active lifecycle state and validates account enablement.", tc_style), Paragraph("Validates standard active employee provisioning.", tc_style)],
        [Paragraph("scenarios/lifecycle_management/<br/>leave_of_absence.py", tc_mono), Paragraph("Applies loa state and asserts account suspension.", tc_style), Paragraph("Validates temporary leave access suspension.", tc_style)],
        [Paragraph("scenarios/lifecycle_management/<br/>skp.py", tc_mono), Paragraph("Applies skp sabbatical state and validates policy enforcement.", tc_style), Paragraph("Standardized sabbatical policy testing.", tc_style)],
        [Paragraph("scenarios/lifecycle_management/<br/>emergency_access_removal.py", tc_mono), Paragraph("Applies ear state with mandatory EAR-CONFIRM safety check.", tc_style), Paragraph("Validates rapid security lockout in incident scenarios.", tc_style)],
        [Paragraph("scenarios/lifecycle_management/<br/>termination.py", tc_mono), Paragraph("Applies termination state with mandatory TERMINATE prompt.", tc_style), Paragraph("Validates deprovisioning and entitlement revocation.", tc_style)],
        [Paragraph("scenarios/lifecycle_management/<br/>full_lifecycle_demo.py", tc_mono), Paragraph("Runs sequential demo: Active -> SKP -> LOA -> EAR -> Termination.", tc_style), Paragraph("Validates complete identity lifecycle progression.", tc_style)],
        # Scenarios - Access
        [Paragraph("scenarios/access_management/<br/>role_request.py", tc_mono), Paragraph("Role search, source alignment validation, request submission, and polling.", tc_style), Paragraph("Validates role governance and target source matching.", tc_style)],
        # Scenarios - Inspection
        [Paragraph("scenarios/inspection/<br/>view_identity_details.py", tc_mono), Paragraph("Displays clean Identity Card with profile and attributes (Image 1).", tc_style), Paragraph("Read-only inspection of identity attributes.", tc_style)],
        [Paragraph("scenarios/inspection/<br/>view_correlated_accounts.py", tc_mono), Paragraph("Renders table of all correlated accounts across sources (Image 2).", tc_style), Paragraph("Read-only inspection of multi-source accounts.", tc_style)],
        [Paragraph("scenarios/inspection/<br/>view_source_attributes.py", tc_mono), Paragraph("Drill-down into target AD account's raw schema attributes (Image 3).", tc_style), Paragraph("Read-only inspection of directory attributes.", tc_style)],
        [Paragraph("scenarios/inspection/<br/>view_event_attributes.py", tc_mono), Paragraph("Audit log inspection with 3 options: Last 10, source filter, and all events.", tc_style), Paragraph("Read-only audit event log investigation.", tc_style)],
        # Sailpoint APIs
        [Paragraph("sailpoint/api_client.py", tc_mono), Paragraph("Central HTTP client with automatic retry, backoff, and bearer token redaction.", tc_style), Paragraph("Robust, centralized communication with SailPoint ISC.", tc_style)],
        [Paragraph("sailpoint/identity.py", tc_mono), Paragraph("Identity search (/v3/search), detail lookups, and card view formatters.", tc_style), Paragraph("Identity domain queries and terminal displays.", tc_style)],
        [Paragraph("sailpoint/identity_profiles.py", tc_mono), Paragraph("Retrieves identity profiles and configured lifecycle states from tenant.", tc_style), Paragraph("Dynamic retrieval of tenant governance configuration.", tc_style)],
        [Paragraph("sailpoint/sources.py", tc_mono), Paragraph("Retrieves tenant sources and filters Active Directory connectors.", tc_style), Paragraph("Identifies valid provisioning targets in tenant.", tc_style)],
        [Paragraph("sailpoint/accounts.py", tc_mono), Paragraph("Account creation, direct enablement, disablement, and detail queries.", tc_style), Paragraph("Low-level account management operations.", tc_style)],
        [Paragraph("sailpoint/roles.py", tc_mono), Paragraph("Role search, access profile resolution, and source alignment check.", tc_style), Paragraph("Verifies role targets correct directory before request.", tc_style)],
        [Paragraph("sailpoint/access_requests.py", tc_mono), Paragraph("Submits access requests (/v3/access-requests) and polls status.", tc_style), Paragraph("Governed entitlement grant orchestration.", tc_style)],
        [Paragraph("sailpoint/lifecycle.py", tc_mono), Paragraph("Executes set-lifecycle-state API and captures account activity IDs.", tc_style), Paragraph("Triggers tenant lifecycle engine evaluation.", tc_style)],
        [Paragraph("sailpoint/events.py", tc_mono), Paragraph("Queries /v3/search events index, parses sources, and formats event tables.", tc_style), Paragraph("Dedicated service powering event inspection.", tc_style)],
        # Validation
        [Paragraph("validation/identity_validation.py", tc_mono), Paragraph("Validates live technical lifecycle state against expectation.", tc_style), Paragraph("Tier 2 identity validation.", tc_style)],
        [Paragraph("validation/account_validation.py", tc_mono), Paragraph("Validates account existence and enabled/disabled status via UAC/flags.", tc_style), Paragraph("Tier 3 account validation.", tc_style)],
        [Paragraph("validation/provisioning_validation.py", tc_mono), Paragraph("Polls /beta/account-activities and verifies downstream policy match.", tc_style), Paragraph("Tier 1 task polling and Tier 4 policy evaluation.", tc_style)],
        # Reporting
        [Paragraph("reporting/report_generator.py", tc_mono), Paragraph("Maintains TestReportItem records; generates JSON, Markdown, and Excel.", tc_style), Paragraph("Central audit report coordination.", tc_style)],
        [Paragraph("reporting/excel_report_generator.py", tc_mono), Paragraph("Constructs 5-tab analytical Excel workbook with corporate styling.", tc_style), Paragraph("Leadership-ready analytical reporting.", tc_style)],
        [Paragraph("reporting/logger.py", tc_mono), Paragraph("Console and rotating file logger with automatic token redaction.", tc_style), Paragraph("Sanitized, timestamped diagnostic logging.", tc_style)],
        # Auth & Config
        [Paragraph("authentication/auth_client.py", tc_mono), Paragraph("OAuth2 Client Credentials manager with in-memory token caching.", tc_style), Paragraph("Secure, automated API authentication.", tc_style)],
        [Paragraph("config/settings.py", tc_mono), Paragraph("Environment configuration loader resolving paths and tenant URLs.", tc_style), Paragraph("Centralized application configuration.", tc_style)],
        [Paragraph("config/constants.py", tc_mono), Paragraph("Constant mappings for lifecycle states, API endpoints, and metadata.", tc_style), Paragraph("Eliminates hardcoded strings across codebase.", tc_style)],
        # Docs
        [Paragraph("docs/SETUP_GUIDE.md", tc_mono), Paragraph("Autonomous machine setup guide with step-by-step terminal instructions.", tc_style), Paragraph("Enables zero-AI setup on any fresh machine.", tc_style)],
        [Paragraph("docs/API_DOCUMENTATION.md", tc_mono), Paragraph("Complete reference of all SailPoint ISC REST endpoints utilized.", tc_style), Paragraph("Technical API integration specification.", tc_style)],
        [Paragraph("docs/WORKFLOW.md", tc_mono), Paragraph("Comprehensive workflow documentation with sequence diagrams and rules.", tc_style), Paragraph("Detailed testing process guide.", tc_style)],
    ]

    files_ref_table = Table(files_ref_data, colWidths=[2.2 * inch, 3.1 * inch, 2.2 * inch])
    files_ref_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_DARK),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
    ]))
    story.append(files_ref_table)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 6: MULTI-TIER VERIFICATION & AUDIT REPORTING
    # =========================================================================
    story.append(Paragraph("6. 4-TIER VERIFICATION PIPELINE & INSTITUTIONAL REPORTING", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY_DARK, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "A critical differentiator of this framework is its <b>4-Tier Technical Verification Pipeline</b>. "
        "A test scenario is not marked as successful merely because the API returned HTTP 200 OK. "
        "It must satisfy deterministic checks across all four independent verification tiers.",
        body_style
    ))

    tiers_data = [
        [Paragraph("Verification Tier", th_style), Paragraph("Target System & API", th_style), Paragraph("Verification Criteria & Assertion", th_style)],
        [
            Paragraph("Tier 1: Provisioning Activity Polling", tc_bold),
            Paragraph("GET /beta/account-activities/{id}", tc_mono),
            Paragraph("Polls backend task queue until status transitions from PENDING/IN_PROGRESS to COMPLETED. Confirms task completed without queue exceptions.", tc_style),
        ],
        [
            Paragraph("Tier 2: Real-time Live Identity State", tc_bold),
            Paragraph("GET /beta/identities/{id}", tc_mono),
            Paragraph("Directly queries live identity object to assert technical lifecycleState matches target (e.g. active, loa, skp, terminated).", tc_style),
        ],
        [
            Paragraph("Tier 3: Target Account Existence & Status", tc_bold),
            Paragraph("GET /v3/accounts?filters=...", tc_mono),
            Paragraph("Inspects target AD account record. Asserts root disabled boolean and decodes Active Directory userAccountControl (512 vs 514).", tc_style),
        ],
        [
            Paragraph("Tier 4: Downstream Policy & Outcome Evaluation", tc_bold),
            Paragraph("Framework Policy Engine", tc_mono),
            Paragraph("Correlates observed directory state against tenant identity profile expectation (e.g. confirming LOA resulted in AD disablement).", tc_style),
        ],
    ]
    tiers_table = Table(tiers_data, colWidths=[2.0 * inch, 2.0 * inch, 3.5 * inch])
    tiers_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SLATE_NAVY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
    ]))
    story.append(tiers_table)

    story.append(Spacer(1, 12))

    story.append(Paragraph("INSTITUTIONAL AUDIT & REPORTING ARTIFACTS", h2_style))
    story.append(Paragraph(
        "Upon session completion, the framework automatically generates three synchronized audit artifacts:",
        body_style
    ))

    reports_data = [
        [Paragraph("Artifact Format", th_style), Paragraph("File Path & Schema", th_style), Paragraph("Content & Analytical Purpose", th_style)],
        [
            Paragraph("Analytical Excel Workbook", tc_bold),
            Paragraph("reports/test_report_<TS>.xlsx", tc_mono),
            Paragraph("Corporate 5-tab report (Executive Summary, Scenario Master Log, Step-by-Step Audit, Verification Matrix, Account Inventory). Zero emojis, institutional typography, and KPI cards.", tc_style),
        ],
        [
            Paragraph("Executive Markdown Summary", tc_bold),
            Paragraph("reports/test_summary_<TS>.md", tc_mono),
            Paragraph("Human-readable document containing executive summary tables, verification check matrices, and failure rationales for rapid peer review.", tc_style),
        ],
        [
            Paragraph("Raw Audit JSON Data", tc_bold),
            Paragraph("reports/test_report_<TS>.json", tc_mono),
            Paragraph("Full machine-readable export with complete test parameters, raw API payloads, task IDs, and verification check dictionaries for CI/CD ingestion.", tc_style),
        ],
        [
            Paragraph("Sanitized Execution Log", tc_bold),
            Paragraph("logs/execution.log", tc_mono),
            Paragraph("Comprehensive chronological audit trail recording every HTTP request, status code, latency, and assertion, with automatic Bearer token redaction.", tc_style),
        ],
    ]
    reports_table = Table(reports_data, colWidths=[1.8 * inch, 2.0 * inch, 3.7 * inch])
    reports_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_DARK),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
    ]))
    story.append(reports_table)

    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 7: SECURITY & GOVERNANCE COMPLIANCE
    # =========================================================================
    story.append(Paragraph("7. SECURITY, CREDENTIAL ISOLATION & ZERO-TRUST GOVERNANCE", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY_DARK, spaceBefore=2, spaceAfter=8))

    sec_html = (
        "<b>ENTERPRISE SECURITY & DATA PRIVACY CONTROLS:</b><br/>"
        "• <b>Credential Isolation</b>: Personal Access Tokens (PAT Client ID & Client Secret) are loaded exclusively via environment variables (.env). "
        "Credentials are never hardcoded, never stored in version control, and .env is strictly excluded by .gitignore.<br/>"
        "• <b>In-Memory OAuth Token Lifecycle</b>: Access tokens are acquired dynamically via POST /oauth/token, cached in memory with expiration tracking, "
        "and automatically refreshed before expiry without writing tokens to disk.<br/>"
        "• <b>Sensitive Data Redaction</b>: The custom logging engine (reporting/logger.py) inspects all outgoing requests and diagnostic messages, "
        "automatically regex-sanitizing Authorization headers, Bearer tokens, and client secrets.<br/>"
        "• <b>High-Impact Guardrails</b>: Dangerous transitions (Employment Termination, Emergency Access Removal) mandate interactive safety confirmation "
        "('TERMINATE' / 'EAR-CONFIRM') to prevent accidental deprovisioning of non-test identities."
    )
    sec_table = Table([[Paragraph(sec_html, body_style)]], colWidths=[7.5 * inch])
    sec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#DC2626")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(sec_table)

    story.append(Spacer(1, 14))
    story.append(Paragraph("Document Reference: SAILPOINT-ISC-AD-PROV-ARCH-v2.0 | Approved for Enterprise Distribution", ParagraphStyle("DocFooterNote", fontName="Helvetica-Oblique", fontSize=8, textColor=TEXT_MUTED, alignment=1)))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Architecture PDF successfully generated: {output_path}")


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent if "__file__" in locals() else Path("docs")
    pdf_target = out_dir / "ARCHITECTURE_SYSTEM_DESIGN.pdf"
    create_architecture_pdf(pdf_target)

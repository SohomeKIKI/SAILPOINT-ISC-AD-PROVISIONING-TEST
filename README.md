# API-Driven Automation of Active Directory (AD) Provisioning Tests in SailPoint ISC

A modular, interactive Python automation framework designed to test Active Directory (AD) provisioning scenarios end-to-end in **SailPoint Identity Security Cloud (ISC)** through official ISC REST APIs.

---

## 1. Project Overview & Objective

The objective of this framework is to standardize, automate, and validate AD provisioning tests without manual UI work in SailPoint ISC. It provides repeatable, interactive verification across the following 8 core scenarios:

1. **Create Account** (`active`) - Create and enable a new AD account on the target source.
2. **Enable Account** (`active`) - Enable an existing AD account.
3. **Disable Account** (`loa` / `skp` / `ear`) - Disable an existing AD account.
4. **Role Request** - Search for a role by name, inspect associated sources, compare with target source, submit an access request, and poll status.
5. **Employment Termination** (`employmentTermination` / `terminated`) - Apply termination lifecycle state with mandatory safety confirmation, deprovisioning accounts and revoking access.
6. **Leave of Absence (LOA)** (`loa`) - Suspend access and disable the AD account.
7. **Sabbatical (SKP)** (`skp`) - Suspend the AD account while retaining identity attributes.
8. **Emergency Access Removal (EAR)** (`ear`) - Immediately disable AD account and revoke critical access following an emergency or risk event (restricted to non-production).

---

## 2. Architecture & Folder Structure

```
sailpoint_ad_automation/
│
├── .env                              # Tenant URL, Client ID, and Client Secret
├── .env.example                      # Template for environment configuration
├── .gitignore                        # Git exclusion rules for credentials and logs
├── requirements.txt                  # Python dependencies (requests, python-dotenv)
├── README.md                         # Project documentation and user guide
│
├── config/
│   ├── __init__.py                   # Package initializer
│   ├── settings.py                   # Central environment variables & path resolver
│   └── constants.py                  # Lifecycle states, API endpoints, and metadata
│
├── authentication/
│   ├── __init__.py                   # Package initializer
│   └── auth_client.py                # OAuth 2.0 Client Credentials token management
│
├── sailpoint/
│   ├── __init__.py                   # Package initializer
│   ├── api_client.py                 # Central HTTP client (retries, rate limiting, logging)
│   ├── identity.py                   # Identity search, retrieval, and attribute parsing
│   ├── identity_profiles.py          # Identity profile & lifecycle states retrieval
│   ├── lifecycle.py                  # Lifecycle state update API execution
│   ├── sources.py                    # AD & authoritative source management
│   ├── accounts.py                   # Account creation, enablement, and disablement
│   ├── roles.py                      # Role search and source alignment verification
│   └── access_requests.py            # Access request submission and status polling
│
├── test_scenarios/
│   ├── __init__.py                   # Package initializer
│   ├── create_account.py             # Create Account test handler
│   ├── enable_account.py             # Enable Account test handler
│   ├── disable_account.py            # Disable Account test handler
│   ├── role_request.py               # Interactive Role Request subflow handler
│   ├── termination.py                # Termination scenario (explicit safety prompt)
│   ├── leave_of_absence.py           # LOA scenario handler
│   ├── skp.py                        # Sabbatical (SKP) scenario handler
│   └── emergency_access_removal.py   # EAR scenario handler (explicit safety prompt)
│
├── validation/
│   ├── __init__.py                   # Package initializer
│   ├── identity_validation.py        # Identity existence, attributes, and lifecycle state checks
│   ├── account_validation.py         # Account existence and enabled/disabled state checks
│   └── provisioning_validation.py    # Downstream account activity (/beta/account-activities)
│
├── reporting/
│   ├── __init__.py                   # Package initializer
│   ├── logger.py                     # Console & file logger with sensitive data redaction
│   └── report_generator.py           # JSON and Markdown test execution reports
│
├── ad_connector/
│   ├── __init__.py                   # Package initializer
│   └── ad_client.py                  # Direct Active Directory abstraction (decoupled)
│
├── logs/                             # Output directory for execution logs
└── reports/                          # Output directory for generated audit reports
```

---

## 3. Getting Started & Installation

### Prerequisites
- Python 3.9+ (Python 3.10+ recommended)
- Personal Access Token (PAT) generated in your SailPoint ISC tenant.

### Installation

1. Navigate to the project root:
   ```powershell
   cd sailpoint_ad_automation
   ```

2. (Optional) Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install required packages:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 4. Configuration

Edit the `.env` file in `sailpoint_ad_automation/` with your tenant URL and PAT credentials:

```dotenv
SAILPOINT_BASE_URL=https://eu-partner28.api.identitynow.com
SAILPOINT_CLIENT_ID=YOUR_CLIENT_ID
SAILPOINT_CLIENT_SECRET=YOUR_CLIENT_SECRET
```

> **Security Note:** Credentials and access tokens are never logged or stored in version control. All log output automatically redacts OAuth tokens and client secrets.

---

## 5. End-to-End Application Workflow

When you run `python main.py`, the interactive CLI guides you through the 9-step workflow:

```
                  START
                    |
                    v
                 main.py
                    |
                    v
             AUTHENTICATION
                    |
                    v
              ACCESS TOKEN
                    |
                    v
             SEARCH IDENTITIES
                    |
                    v
           DISPLAY AVAILABLE USERS
                    |
                    v
           SELECT AN IDENTITY
                    |
                    v
          RETRIEVE IDENTITY DETAILS
                    |
                    v
          SELECT IDENTITY PROFILE
                    |
                    v
          RETRIEVE LIFECYCLE STATES
                    |
                    v
           SELECT TARGET SOURCE
                    |
                    v
           SELECT TEST SCENARIO
                    |
          +---------+----------+
          |                    |
          v                    v
     ROLE REQUEST       LIFECYCLE / ACCOUNT
          |                    |
          v                    v
     SEARCH ROLE        EXECUTE OPERATION
          |                    |
          v                    |
     VALIDATE SOURCE           |
          |                    |
          v                    |
     SUBMIT REQUEST            |
          |                    |
          +---------+----------+
                    |
                    v
              VALIDATION
                    |
                    v
         CHECK PROVISIONING STATUS
                    |
                    v
             WRITE EXECUTION LOG
                    |
                    v
           GENERATE TEST REPORT
                    |
                    v
                   END
```

---

## 6. Execution Modes

### Interactive Mode (Default)
Run the script interactively:
```powershell
python main.py
```

### Pre-Filtered Identity Mode
Target a specific user immediately by name, email, or ID:
```powershell
python main.py --user "Yuki Reyes"
```

### Direct Scenario Execution
Execute a specific scenario by number (e.g., Scenario 7 for SKP):
```powershell
python main.py --user "Lily Hayes" --scenario 7
```

### Inspect Identity & Correlated Accounts
Inspect the identity's full attributes, correlated accounts table, and drill into raw source attributes without executing provisioning scenarios:
```powershell
python main.py --user "Ava Ellis" --view-accounts
```
Or select **Option 10** from the interactive menu in Step 7. You can inspect individual accounts (`1-N`) or all accounts (`A`) together.

---

## 7. Supported Lifecycle States

| Lifecycle State | Full Name | Description | Typical Provisioning Behaviour |
|---|---|---|---|
| `active` | Active | Onboarded user with standard access | Create and enable AD account; provision roles |
| `loa` | Leave of Absence | User on temporary leave | Disable AD account; retain but suspend access |
| `skp` | Sabbatical (SKP) | User on sabbatical leave with provisioning configuration retained | Disable/suspend AD account; retain attributes |
| `ear` | Emergency Access Removal | Immediate access removal following risk event | Immediately disable AD account & revoke critical access |
| `employmentTermination` | Employment Termination | User no longer with organization | Disable or remove AD account, revoke access, and deprovision |

---

## 8. Role Request Detailed Sub-Flow

The Role Request scenario (`test_scenarios/role_request.py`) enforces strict validation before submitting access requests:
1. Prompts for a Role name or keyword.
2. Searches ISC roles via the Search Roles API.
3. If no role matches, offers to retry or exit.
4. If multiple roles match, displays numbered list for tester selection.
5. Inspects associated Access Profiles and resolves underlying sources.
6. Compares the role's source with the target test source.
7. Warns the tester on mismatch (avoiding unintended provisioning).
8. Submits the Access Request (`type: GRANT_ACCESS`).
9. Polls access request status until complete.
10. Records full execution outcome in the audit report.

---

## 9. Safety Precautions
- **Termination Confirmation**: Requires entering `TERMINATE` before applying `employmentTermination`.
- **EAR Confirmation**: High-impact security operation. Requires explicit authorization (`EAR-CONFIRM`) and warns to only run in non-production tenants.

---

## 10. Audit Logging and Reports

All test runs generate persistent audit artifacts:
- **Console Log & File**: `logs/execution.log` (timestamped, sensitive data redacted).
- **JSON Audit Report**: `reports/test_report_<TIMESTAMP>.json` (machine-readable, complete API request/response metadata).
- **Markdown Summary**: `reports/test_summary_<TIMESTAMP>.md` (executive summary with status tables and validation checks).

---

## 11. Project Documentation

Comprehensive documentation guides are available in the [`docs/`](docs/) directory:
* [**Setup & Installation Guide**](docs/SETUP_GUIDE.md): Complete setup walkthrough from scratch for fresh machines (Windows, macOS, Linux) without requiring AI help.
* [**API Endpoint Reference**](docs/API_ENDPOINTS.md): Exhaustive guide to all SailPoint ISC REST APIs used, headers, request bodies, sample responses, and search index nuances.
* [**Workflow & Architecture Guide**](docs/WORKFLOW.md): Complete architecture diagrams, 9-step interactive flow, multi-tier validation hierarchy, and scenario execution sequence.



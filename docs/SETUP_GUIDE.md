# Complete Setup Guide: SailPoint ISC AD Provisioning Automation

This guide provides step-by-step instructions for setting up, configuring, and executing this automation framework on any fresh machine (Windows, macOS, or Linux) **without requiring any AI assistance or external tools**.

---

## 1. System Requirements

* **Operating System**: Windows 10/11, macOS (10.15+), or modern Linux distribution (Ubuntu 20.04+, RHEL 8+, Debian 11+).
* **Python**: Python 3.9 or higher (Python 3.10, 3.11, or 3.12 recommended).
* **Git**: Installed and available in PATH.
* **Network Access**: Outbound HTTPS (port 443) connectivity to your SailPoint ISC tenant (`*.identitynow.com`).

---

## 2. Generating SailPoint ISC API Credentials (PAT)

Before running the application, you must generate a **Personal Access Token (PAT)** in SailPoint Identity Security Cloud:

1. Log in to your SailPoint ISC tenant admin portal (e.g. `https://<tenant>.identitynow.com`).
2. In the top-right corner, click on your **User Profile Avatar / Name** and select **Preferences** (or navigate to **Admin > Personal Access Tokens**).
3. Under the **Personal Access Tokens** section, click **New Token** (or **Generate Token**).
4. Enter a meaningful Description (e.g., `AD Provisioning Test Automation`).
5. Set an expiration date.
6. Click **Create Token**.
7. **Important**: Copy both the **Client ID** and **Client Secret** immediately. SailPoint will only show the secret once.

---

## 3. Terminal Setup & Installation Steps

### Step 3.1: Clone the Repository

Open your terminal or PowerShell and run:

```bash
git clone https://github.com/SohomeKIKI/SAILPOINT-ISC-AD-PROVISIONING-TEST.git
cd SAILPOINT-ISC-AD-PROVISIONING-TEST
```

---

### Step 3.2: Create and Activate a Python Virtual Environment

Using a virtual environment isolates project packages and prevents version conflicts.

#### On Windows (PowerShell):
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```
*(If PowerShell blocks execution of scripts, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first)*.

#### On Windows (Command Prompt - CMD):
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

#### On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3.3: Install Dependencies

With the virtual environment active, install all required dependencies:

```bash
pip install -r requirements.txt
```

Verify installed packages:
```bash
pip list
```
You should see:
* `requests` (HTTP REST API client)
* `python-dotenv` (Environment variable loader)
* `openpyxl` (Enterprise analytical Excel workbook generator)

---

### Step 3.4: Configure Environment Variables (`.env`)

Create your local `.env` configuration file from the provided template:

#### On Windows (PowerShell):
```powershell
Copy-Item .env.example .env
```

#### On macOS / Linux / Git Bash:
```bash
cp .env.example .env
```

Open `.env` in any text editor (Notepad, VS Code, Nano, Vim) and replace the placeholders with your actual SailPoint credentials:

```dotenv
# SailPoint Identity Security Cloud (ISC) Tenant Configuration
SAILPOINT_BASE_URL=https://eu-partner28.api.identitynow.com
SAILPOINT_CLIENT_ID=YOUR_ACTUAL_CLIENT_ID_HERE
SAILPOINT_CLIENT_SECRET=YOUR_ACTUAL_CLIENT_SECRET_HERE
```

> **Security Note**: Never commit `.env` to Git. It is already included in `.gitignore`.

---

## 4. Verifying the Setup

Run the included automated integration test suite to verify connectivity, authentication, API endpoints, and reporting:

```bash
python -m unittest tests/test_integration.py
```

Expected output:
```text
...........
----------------------------------------------------------------------
Ran 11 tests in 15.000s

OK
```

All 11 tests validate:
1. OAuth 2.0 token acquisition (`/oauth/token`)
2. Identity search API (`/v3/search`)
3. Direct identity details lookup (`/beta/identities/{id}`)
4. Identity Profile and Source retrieval (`/v3/identity-profiles`, `/v3/sources`)
5. Profile Lifecycle States inspection (`/v3/identity-profiles/{id}/lifecycle-states`)
6. Role search API
7. Multi-tier validation engine and Markdown/JSON/**Excel (.xlsx)** audit report generators
8. Account details and UI view formatters (Images 1, 2, 3)
9. Modular scenario registry and category mappings
10. ExecutionContext runtime model and MenuManager dispatch
11. Event fetching service with 3 options (Last 10, source-filtered, and all events)

---

## 5. Running the Application

### 5.1 Interactive CLI Walkthrough (Recommended)
```bash
python main.py
```
This guides you interactively through the 9 steps:
1. **Search & Select an Identity**: Search by name, email, or press Enter to list test users (e.g. `Ava Ellis` or `Yuki Reyes`).
2. **Review Identity Details**: Clean identity overview card.
3. **Confirm Identity Profile**: Defaults to linked profile (e.g. `Truist Employee Profile`).
4. **Display Lifecycle States**: Configured states (`preHire`, `active`, `skp`, `ear`, `loa`, `terminated`).
5. **Confirm Target Source**: Defaults to primary target (e.g. `AD_Demo_Source`).
6. **Hierarchical Category Selection (Step 7)**:
   * **Category 1: Account Management**: Create, Enable, Disable, and Unlock Target Accounts.
   * **Category 2: Lifecycle State Management**: Active, Leave of Absence (LOA), Sabbatical (SKP), Emergency Access Removal (EAR), Termination, and Full Demo Sequence.
   * **Category 3: Access & Entitlement Management**: Role Request with Source Alignment Validation.
   * **Category 4: Identity & Account Inspection**: Identity Details, Correlated Accounts, Raw Source Attributes, and Event Attributes (with Last 10, Source Filter, and All Events).

### 5.2 Direct Account & Identity Inspection Mode
Inspect an identity's correlated accounts across all sources and drill into raw source attributes:
```bash
python main.py --user "Ava Ellis" --view-accounts
```

### 5.3 Automated Headless Scenario Execution
Execute a single scenario directly using legacy numbers (1–10):
```bash
# Run Sabbatical (SKP) scenario on Elijah Novak
python main.py --user "Elijah Novak" --scenario 7

# Run Leave of Absence (LOA) scenario on Ava Ellis
python main.py --user "Ava Ellis" --scenario 6
```

---

## 6. Output & Audit Reports

Every execution automatically generates timestamped artifacts:
* **Executive Analytical Excel Workbook**: `reports/test_report_<TIMESTAMP>.xlsx` (Corporate 5-tab report with zero emojis: Executive Summary, Scenario Master Log, Step-by-Step Audit, Verification Matrix, and Account Inventory).
* **Executive Markdown Report**: `reports/test_summary_<TIMESTAMP>.md` (Human-readable summary).
* **Machine-readable JSON Report**: `reports/test_report_<TIMESTAMP>.json` (Full audit raw data).
* **Execution Log file**: `logs/execution.log` (All HTTP calls, parameters, and statuses with sensitive tokens redacted).

---

## 7. Troubleshooting Common Setup Issues

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| `AuthenticationError: HTTP 401 Unauthorized` | Invalid Client ID or Client Secret in `.env` | Regenerate Personal Access Token in SailPoint admin console and update `.env`. |
| `AuthenticationError: HTTP 404 / Connection Error` | Incorrect `SAILPOINT_BASE_URL` | Ensure URL does not have a trailing slash (e.g. `https://<tenant>.api.identitynow.com`). |
| `ModuleNotFoundError: No module named 'requests'` / `'openpyxl'` | Packages not installed or virtual environment not activated | Activate virtual environment (`.\venv\Scripts\Activate.ps1` or `source venv/bin/activate`) and run `pip install -r requirements.txt`. |
| `Script execution is disabled on this system` (PowerShell) | PowerShell ExecutionPolicy | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`. |
| `No identity found matching '<query>'` | Identity not loaded in tenant | Press Enter at the search prompt to list all active test identities loaded in the tenant. |

---

## 8. Quick Setup Cheatsheet (TL;DR)

For quick setup on any new machine:

```bash
# 1. Clone repository
git clone https://github.com/SohomeKIKI/SAILPOINT-ISC-AD-PROVISIONING-TEST.git
cd SAILPOINT-ISC-AD-PROVISIONING-TEST

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1       # On Windows PowerShell (or 'source venv/bin/activate' on macOS/Linux)

# 3. Install all dependencies (requests, python-dotenv, openpyxl)
pip install -r requirements.txt

# 4. Copy .env template and add your credentials
Copy-Item .env.example .env       # (or 'cp .env.example .env' on macOS/Linux)
# Edit .env with SAILPOINT_BASE_URL, CLIENT_ID, and CLIENT_SECRET

# 5. Verify connectivity and API tests (all 11 tests)
python -m unittest tests/test_integration.py

# 6. Run the interactive automation tool
python main.py
```

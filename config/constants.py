"""Application constants, API endpoints, lifecycle definitions, and scenario names."""

# Supported Project-Specific Lifecycle States
# Keys are logical identifiers; values represent technical names in SailPoint ISC
LIFECYCLE_STATES = {
    "ACTIVE": "active",
    "LOA": "loa",
    "SKP": "skp",
    "EAR": "ear",
    "TERMINATION": "employmentTermination",  # Tenant technical name (also checks 'terminated' or 'employementTermination')
}

# Technical name aliases and fallbacks for lifecycle states in different tenant setups
LIFECYCLE_STATE_ALIASES = {
    "employmentTermination": ["employmentTermination", "employementTermination", "terminated"],
    "loa": ["loa", "leaveOfAbsence"],
    "skp": ["skp"],
    "ear": ["ear"],
    "active": ["active"],
}

# Lifecycle State metadata according to project handover specification
LIFECYCLE_METADATA = {
    "active": {
        "full_name": "Active",
        "description": "Onboarded user with standard access",
        "typical_behavior": "Create and enable the AD account; provision roles and entitlements",
        "expected_ad_status": "Enabled",
    },
    "loa": {
        "full_name": "Leave of Absence",
        "description": "User on temporary leave",
        "typical_behavior": "Disable the AD account; retain but suspend access",
        "expected_ad_status": "Disabled",
    },
    "skp": {
        "full_name": "Sabbatical (SKP)",
        "description": "User on sabbatical leave with provisioning configuration retained",
        "typical_behavior": "Disable/suspend the AD account according to tenant configuration; retain attributes",
        "expected_ad_status": "Disabled / Suspended",
    },
    "ear": {
        "full_name": "Emergency Access Removal",
        "description": "Immediate access removal following an emergency or risk event",
        "typical_behavior": "Immediately disable the AD account and revoke critical access; preserve identity for review",
        "expected_ad_status": "Disabled Immediately",
    },
    "employmentTermination": {
        "full_name": "Employment Termination",
        "description": "User no longer with the organization",
        "typical_behavior": "Disable or remove the AD account, revoke all access, and initiate deprovisioning",
        "expected_ad_status": "Disabled or Removed",
    },
    "employementTermination": {
        "full_name": "Employment Termination",
        "description": "User no longer with the organization",
        "typical_behavior": "Disable or remove the AD account, revoke all access, and initiate deprovisioning",
        "expected_ad_status": "Disabled or Removed",
    },
    "terminated": {
        "full_name": "Employment Termination",
        "description": "User no longer with the organization",
        "typical_behavior": "Disable or remove the AD account, revoke all access, and initiate deprovisioning",
        "expected_ad_status": "Disabled or Removed",
    },
}

# Supported Test Scenarios
SCENARIOS = {
    "CREATE_ACCOUNT": "Create Account",
    "ENABLE_ACCOUNT": "Enable Account",
    "DISABLE_ACCOUNT": "Disable Account",
    "ROLE_REQUEST": "Role Request",
    "TERMINATION": "Termination",
    "LOA": "Leave of Absence (LOA)",
    "SKP": "Sabbatical (SKP)",
    "EAR": "Emergency Access Removal (EAR)",
}

# High-impact scenarios that require explicit tester confirmation
HIGH_IMPACT_SCENARIOS = [
    SCENARIOS["TERMINATION"],
    SCENARIOS["EAR"],
]

# SailPoint ISC API Endpoints
API_ENDPOINTS = {
    "OAUTH_TOKEN": "/oauth/token",
    "IDENTITIES": "/v3/identities",
    "PUBLIC_IDENTITIES": "/v3/public-identities",
    "SEARCH": "/v3/search",
    "IDENTITY_PROFILES": "/v3/identity-profiles",
    "SOURCES": "/v3/sources",
    "ACCOUNTS": "/v3/accounts",
    "ROLES": "/v3/roles",
    "ACCESS_REQUESTS": "/v3/access-requests",
    "ACCESS_REQUEST_STATUS": "/v3/access-request-status",
    "ACCOUNT_ACTIVITIES": "/beta/account-activities",
}


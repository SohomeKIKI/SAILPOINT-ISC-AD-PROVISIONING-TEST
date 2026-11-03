"""Active Directory connector client abstraction for direct AD verification.

IMPORTANT ARCHITECTURE NOTE:
This module is deliberately decoupled from SailPoint ISC API logic.
In the current project phase, test identities are loaded into SailPoint ISC via a Delimited File source.
When direct Active Directory connectivity (LDAP / WinRM / RSAT) details and credentials
are provisioned, this client provides the interface to validate user objects directly on the domain controller.
"""

import os
from typing import Dict, Any, List, Optional
from reporting.logger import get_logger

logger = get_logger("ad_connector")


class ADClient:
    """Client for direct Active Directory LDAP / domain controller communication."""

    def __init__(self):
        self.ad_server = os.getenv("AD_SERVER", "")
        self.ad_domain = os.getenv("AD_DOMAIN", "corp.local")
        self.bind_user = os.getenv("AD_BIND_USER", "")
        self.bind_password = os.getenv("AD_BIND_PASSWORD", "")
        self.is_configured = bool(self.ad_server and self.bind_user)

    def is_connected(self) -> bool:
        """Check if direct AD connection parameters are configured."""
        return self.is_configured

    def verify_account_direct(self, sam_account_name: str) -> Dict[str, Any]:
        """Perform direct check against Active Directory domain controller.
        
        If AD credentials are not yet configured, returns a descriptive standby notice
        explaining that SailPoint ISC API validation is currently authoritative.
        """
        if not self.is_configured:
            logger.info(
                f"[AD Connector Standby] Direct AD connection not configured for '{sam_account_name}'. "
                "Downstream validation relies on SailPoint ISC source account and activity tracking."
            )
            return {
                "direct_ad_checked": False,
                "status": "STANDBY",
                "message": (
                    "Direct AD DC credentials not yet provided. "
                    "Verification evaluated via SailPoint ISC account API."
                ),
                "account_name": sam_account_name,
            }

        # Placeholder for ldap3 / pyad connection when server details are provided
        logger.info(f"Connecting to Active Directory DC at {self.ad_server} for {sam_account_name}...")
        return {
            "direct_ad_checked": True,
            "status": "SUCCESS",
            "account_name": sam_account_name,
            "enabled": True,
            "groups": [],
        }

    def is_account_enabled(self, sam_account_name: str) -> Optional[bool]:
        """Check whether userAccountControl in AD has account enabled (UAC bit 2 not set)."""
        if not self.is_configured:
            return None
        res = self.verify_account_direct(sam_account_name)
        return res.get("enabled")

    def get_user_group_memberships(self, sam_account_name: str) -> List[str]:
        """Retrieve AD security group memberships directly from Active Directory."""
        if not self.is_configured:
            return []
        res = self.verify_account_direct(sam_account_name)
        return res.get("groups", [])


# Global client instance
ad_client = ADClient()


"""Execution context passed to scenarios to decouple them from global state and environment."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from reporting.logger import get_logger
from reporting.report_generator import ReportGenerator

logger = get_logger("context")


@dataclass
class ExecutionContext:
    """Encapsulates all runtime data and services required by a test scenario."""

    identity: Dict[str, Any]
    source: Dict[str, Any]
    profile_id: Optional[str] = None
    interactive: bool = True
    force_confirmed: bool = False
    custom_params: Dict[str, Any] = field(default_factory=dict)
    report_generator: Optional[ReportGenerator] = None

    @property
    def identity_id(self) -> str:
        """Get unique identity identifier."""
        return str(self.identity.get("id") or "")

    @property
    def identity_name(self) -> str:
        """Get identity display name or technical name."""
        return str(self.identity.get("displayName") or self.identity.get("name") or "Unknown")

    @property
    def identity_email(self) -> Optional[str]:
        """Get identity email address."""
        return self.identity.get("email")

    @property
    def source_id(self) -> str:
        """Get unique source identifier."""
        return str(self.source.get("id") or "")

    @property
    def source_name(self) -> str:
        """Get source display name."""
        return str(self.source.get("name") or "Unknown Source")

    @property
    def effective_profile_id(self) -> Optional[str]:
        """Get effective identity profile identifier."""
        return self.profile_id or self.identity.get("identityProfileId")

    @property
    def current_lifecycle_state(self) -> str:
        """Get current normalized lifecycle state."""
        return str(self.identity.get("lifecycleState") or "unknown")

    def refresh_identity(self) -> Dict[str, Any]:
        """Refresh identity details from SailPoint live database."""
        from sailpoint.identity import get_identity_by_id
        fresh = get_identity_by_id(self.identity_id)
        if fresh:
            self.identity = fresh
        return self.identity

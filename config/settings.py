"""Application settings and environment variable configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project directory structure
CONFIG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CONFIG_DIR.parent
LOGS_DIR = PROJECT_ROOT / "logs"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Ensure runtime directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables (.env in project root or parent workspace)
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class Settings:
    """Central configuration store reading from environment variables."""

    def __init__(self):
        self.base_url = os.getenv(
            "SAILPOINT_BASE_URL", "https://eu-partner28.api.identitynow.com"
        ).rstrip("/")
        self.client_id = os.getenv("SAILPOINT_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("SAILPOINT_CLIENT_SECRET", "").strip()
        
        # HTTP configuration
        self.http_timeout = int(os.getenv("SAILPOINT_HTTP_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("SAILPOINT_MAX_RETRIES", "3"))
        self.retry_backoff_factor = float(os.getenv("SAILPOINT_RETRY_BACKOFF", "1.5"))

        # Paths
        self.project_root = PROJECT_ROOT
        self.logs_dir = LOGS_DIR
        self.reports_dir = REPORTS_DIR

    def validate(self) -> None:
        """Validate that all required credentials are present."""
        errors = []
        if not self.base_url:
            errors.append("SAILPOINT_BASE_URL is not set.")
        if not self.client_id or self.client_id == "YOUR_CLIENT_ID":
            errors.append("SAILPOINT_CLIENT_ID is missing or using placeholder value.")
        if not self.client_secret or self.client_secret == "YOUR_CLIENT_SECRET":
            errors.append("SAILPOINT_CLIENT_SECRET is missing or using placeholder value.")

        if errors:
            raise ValueError(
                "Configuration Error:\n" + "\n".join(f"  - {e}" for e in errors) +
                "\nPlease configure sailpoint_ad_automation/.env with valid credentials."
            )

    @property
    def token_url(self) -> str:
        """Return the OAuth 2.0 token endpoint URL."""
        return f"{self.base_url}/oauth/token"


# Singleton instance
settings = Settings()


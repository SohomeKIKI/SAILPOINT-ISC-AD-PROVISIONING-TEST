"""OAuth 2.0 Client Credentials authentication handler for SailPoint ISC."""

import time
from typing import Optional, Dict
import requests
from config.settings import settings
from reporting.logger import get_logger

logger = get_logger("authentication")


class AuthenticationError(Exception):
    """Raised when authentication with SailPoint ISC fails."""
    pass


class AuthClient:
    """Manages OAuth 2.0 token acquisition, caching, and refresh for SailPoint ISC."""

    def __init__(self):
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0
        self._token_type: str = "Bearer"
        self._scope: Optional[str] = None

    def is_token_valid(self) -> bool:
        """Check if cached token exists and has at least 60 seconds of validity remaining."""
        if not self._access_token:
            return False
        return time.time() < (self._expires_at - 60)

    def get_token(self, force_refresh: bool = False) -> str:
        """Obtain a valid OAuth 2.0 access token using client credentials."""
        if not force_refresh and self.is_token_valid():
            return self._access_token

        settings.validate()

        token_url = settings.token_url
        logger.info(f"Requesting new OAuth access token from: {token_url}")

        payload = {
            "grant_type": "client_credentials",
            "client_id": settings.client_id,
            "client_secret": settings.client_secret,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        try:
            response = requests.post(
                token_url,
                data=payload,
                headers=headers,
                timeout=settings.http_timeout,
            )
        except requests.RequestException as e:
            logger.error(f"Network error during authentication: {type(e).__name__} - {e}")
            raise AuthenticationError(f"Network error connecting to SailPoint token endpoint: {e}") from e

        if response.status_code != 200:
            error_details = response.text
            logger.error(
                f"Authentication failed with status code {response.status_code}. Details: {error_details}"
            )
            raise AuthenticationError(
                f"Failed to authenticate with SailPoint ISC (HTTP {response.status_code}): {error_details}"
            )

        token_data = response.json()
        self._access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)
        self._expires_at = time.time() + float(expires_in)
        self._token_type = token_data.get("token_type", "Bearer")
        self._scope = token_data.get("scope")

        logger.info(
            f"Authentication successful. Token acquired (valid for {expires_in} seconds, scope: {self._scope})"
        )
        return self._access_token

    def get_auth_headers(self) -> Dict[str, str]:
        """Return authorization headers ready for API requests."""
        token = self.get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def clear_token(self) -> None:
        """Clear cached token to force re-authentication on subsequent calls."""
        self._access_token = None
        self._expires_at = 0.0
        logger.debug("Cached authentication token cleared.")


# Global instance
auth_client = AuthClient()


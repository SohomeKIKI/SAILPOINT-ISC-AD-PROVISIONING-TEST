"""Centralized HTTP client for SailPoint ISC REST APIs with retry, rate-limiting, and error handling."""

import time
import requests
from typing import Optional, Dict, Any, Union
from config.settings import settings
from authentication.auth_client import auth_client, AuthenticationError
from reporting.logger import get_logger

logger = get_logger("api_client")


class ApiClientError(Exception):
    """Raised when an API operation fails against SailPoint ISC."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class ApiClient:
    """Central HTTP client handling authentication, headers, retries, and errors."""

    def __init__(self):
        self.base_url = settings.base_url
        self.session = requests.Session()
        self.timeout = settings.http_timeout
        self.max_retries = settings.max_retries
        self.backoff_factor = settings.retry_backoff_factor

    def _build_url(self, endpoint: str) -> str:
        """Construct full URL from endpoint path."""
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        clean_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        return f"{self.base_url}{clean_endpoint}"

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Union[Dict[str, Any], list]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_on_401: bool = True,
    ) -> requests.Response:
        """Execute HTTP request with authentication, retries, and rate-limit handling."""
        url = self._build_url(endpoint)
        request_headers = auth_client.get_auth_headers()
        if headers:
            request_headers.update(headers)

        last_response: Optional[requests.Response] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                start_time = time.time()
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=json_data,
                    data=data,
                    headers=request_headers,
                    timeout=self.timeout,
                )
                duration = round(time.time() - start_time, 2)
                last_response = response

                logger.debug(
                    f"{method.upper()} {endpoint} -> HTTP {response.status_code} ({duration}s)"
                )

                # Handle Rate Limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", self.backoff_factor * attempt))
                    logger.warning(
                        f"Rate limit hit (HTTP 429) on {endpoint}. Backing off for {retry_after}s (attempt {attempt}/{self.max_retries})"
                    )
                    time.sleep(retry_after)
                    continue

                # Handle Token Expiration (401)
                if response.status_code == 401 and retry_on_401:
                    logger.warning("HTTP 401 Unauthorized encountered. Refreshing token and retrying...")
                    auth_client.get_token(force_refresh=True)
                    request_headers = auth_client.get_auth_headers()
                    if headers:
                        request_headers.update(headers)
                    # Retry once immediately with new token
                    retry_on_401 = False
                    continue

                # Handle Server Errors (502, 503, 504)
                if response.status_code in (502, 503, 504) and attempt < self.max_retries:
                    sleep_time = self.backoff_factor * attempt
                    logger.warning(
                        f"Server error HTTP {response.status_code} on {endpoint}. Retrying in {sleep_time}s..."
                    )
                    time.sleep(sleep_time)
                    continue

                return response

            except (requests.ConnectionError, requests.Timeout) as e:
                logger.warning(
                    f"Network error on {method} {endpoint} (attempt {attempt}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries:
                    time.sleep(self.backoff_factor * attempt)
                else:
                    raise ApiClientError(f"Network error communicating with SailPoint API: {e}") from e

        if last_response is not None:
            return last_response

        raise ApiClientError(f"Request failed after {self.max_retries} attempts.")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute GET request and return parsed JSON."""
        response = self.request("GET", endpoint, params=params)
        if not response.ok:
            raise ApiClientError(
                f"GET {endpoint} failed (HTTP {response.status_code}): {response.text}",
                status_code=response.status_code,
                response_text=response.text,
            )
        return response.json() if response.text else {}

    def post(
        self,
        endpoint: str,
        json_data: Optional[Union[Dict[str, Any], list]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
    ) -> Any:
        """Execute POST request and return parsed JSON or response text."""
        response = self.request("POST", endpoint, params=params, json_data=json_data, data=data)
        if not response.ok:
            raise ApiClientError(
                f"POST {endpoint} failed (HTTP {response.status_code}): {response.text}",
                status_code=response.status_code,
                response_text=response.text,
            )
        try:
            return response.json() if response.text else {}
        except ValueError:
            return {"raw_text": response.text, "status_code": response.status_code}

    def patch(self, endpoint: str, json_data: Optional[Union[Dict[str, Any], list]] = None) -> Any:
        """Execute PATCH request."""
        headers = {"Content-Type": "application/json-patch+json"}
        response = self.request("PATCH", endpoint, json_data=json_data, headers=headers)
        if not response.ok:
            raise ApiClientError(
                f"PATCH {endpoint} failed (HTTP {response.status_code}): {response.text}",
                status_code=response.status_code,
                response_text=response.text,
            )
        try:
            return response.json() if response.text else {}
        except ValueError:
            return {"raw_text": response.text, "status_code": response.status_code}

    def delete(self, endpoint: str) -> Any:
        """Execute DELETE request."""
        response = self.request("DELETE", endpoint)
        if not response.ok:
            raise ApiClientError(
                f"DELETE {endpoint} failed (HTTP {response.status_code}): {response.text}",
                status_code=response.status_code,
                response_text=response.text,
            )
        try:
            return response.json() if response.text else {}
        except ValueError:
            return {"status_code": response.status_code}


# Global instance
api_client = ApiClient()


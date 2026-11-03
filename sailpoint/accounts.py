"""Account management and account-level operations in SailPoint ISC."""

from typing import List, Dict, Any, Optional
from sailpoint.api_client import api_client, ApiClientError
from reporting.logger import get_logger

logger = get_logger("accounts")


def get_accounts_for_identity(identity_id: str) -> List[Dict[str, Any]]:
    """Retrieve all accounts linked to an identity across all sources."""
    params = {"filters": f'identityId eq "{identity_id}"'}
    try:
        accounts = api_client.get("/v3/accounts", params=params)
        if isinstance(accounts, list):
            logger.info(f"Retrieved {len(accounts)} accounts for identity '{identity_id}'.")
            return accounts
        return []
    except ApiClientError as e:
        logger.error(f"Failed to retrieve accounts for identity '{identity_id}': {e}")
        return []


def get_detailed_accounts_for_identity(identity_id: str) -> List[Dict[str, Any]]:
    """Retrieve accounts for an identity with full metadata and calculated status."""
    raw_accounts = get_accounts_for_identity(identity_id)
    detailed = []
    for acc in raw_accounts:
        acc_id = acc.get("id")
        # Fetch full account record if attributes or metadata are missing
        full_acc = get_account_by_id(acc_id) if acc_id else None
        merged = full_acc if full_acc else acc

        # Calculate Enabled / Disabled status
        try:
            from validation.account_validation import is_account_disabled_status
            is_disabled = is_account_disabled_status(merged)
        except Exception:
            is_disabled = bool(merged.get("disabled", False))

        status_label = "Disabled" if is_disabled else "Enabled"
        merged["calculatedStatus"] = status_label
        detailed.append(merged)
    return detailed


def get_account_by_id(account_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve details of a specific account by account ID."""
    try:
        account = api_client.get(f"/v3/accounts/{account_id}")
        return account if isinstance(account, dict) else None
    except ApiClientError as e:
        logger.error(f"Failed to retrieve account '{account_id}': {e}")
        return None


def get_account_on_source(identity_id: str, source_id: str) -> Optional[Dict[str, Any]]:
    """Find the specific account belonging to an identity on a given target source."""
    accounts = get_accounts_for_identity(identity_id)
    for acc in accounts:
        if acc.get("sourceId") == source_id:
            return acc
    return None


def enable_account(account_id: str) -> Dict[str, Any]:
    """Enable an account via POST /v3/accounts/{id}/enable."""
    logger.info(f"Sending Enable request for account: {account_id}")
    try:
        res = api_client.post(f"/v3/accounts/{account_id}/enable", json_data={"forceProvisioning": False})
        logger.info(f"Enable account response: {res}")
        return {"success": True, "account_id": account_id, "response": res}
    except ApiClientError as e:
        if "already in requested state" in (e.response_text or "").lower():
            logger.info(f"Account {account_id} is already enabled in ISC.")
            return {"success": True, "account_id": account_id, "status": "already_enabled", "response": e.response_text}
        logger.error(f"Failed to enable account {account_id}: {e}")
        return {
            "success": False,
            "account_id": account_id,
            "error": str(e),
            "status_code": e.status_code,
            "response_text": e.response_text,
        }


def disable_account(account_id: str) -> Dict[str, Any]:
    """Disable an account via POST /v3/accounts/{id}/disable."""
    logger.info(f"Sending Disable request for account: {account_id}")
    try:
        res = api_client.post(f"/v3/accounts/{account_id}/disable", json_data={"forceProvisioning": False})
        logger.info(f"Disable account response: {res}")
        return {"success": True, "account_id": account_id, "response": res}
    except ApiClientError as e:
        if "already in requested state" in (e.response_text or "").lower():
            logger.info(f"Account {account_id} is already disabled in ISC.")
            return {"success": True, "account_id": account_id, "status": "already_disabled", "response": e.response_text}
        logger.error(f"Failed to disable account {account_id}: {e}")
        return {
            "success": False,
            "account_id": account_id,
            "error": str(e),
            "status_code": e.status_code,
            "response_text": e.response_text,
        }


def create_account(source_id: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new account on a target source via POST /v3/accounts."""
    payload = {
        "sourceId": source_id,
        "attributes": attributes,
    }
    logger.info(f"Sending Create Account request on source {source_id}")
    try:
        res = api_client.post("/v3/accounts", json_data=payload)
        logger.info(f"Create account response: {res}")
        return {"success": True, "source_id": source_id, "account": res}
    except ApiClientError as e:
        logger.error(f"Failed to create account on source {source_id}: {e}")
        return {
            "success": False,
            "source_id": source_id,
            "error": str(e),
            "status_code": e.status_code,
            "response_text": e.response_text,
        }


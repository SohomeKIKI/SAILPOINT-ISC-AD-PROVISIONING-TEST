"""Account existence and status validation across sources."""

from typing import Dict, Any, Optional
from sailpoint.accounts import get_accounts_for_identity, get_account_on_source
from sailpoint.identity import get_identity_by_id
from reporting.logger import get_logger

logger = get_logger("account_validation")


def is_account_disabled_status(account: Dict[str, Any]) -> bool:
    """Accurately evaluate whether an account is disabled in SailPoint ISC.
    
    Checks:
    1. Root level boolean 'disabled'
    2. Attributes 'disabled' boolean or string ("true", "1", "yes")
    3. IIQDisabled attribute ("true")
    4. Active Directory userAccountControl attribute bit 2 (ACCOUNTDISABLE = 0x0002)
    5. Status attributes ("disabled", "inactive", "suspended", "locked")
    """
    if not account or not isinstance(account, dict):
        return False

    # 1. Root level disabled (authoritative boolean in SailPoint ISC)
    if account.get("disabled") is True:
        return True

    # 2. Attribute checks (safely handling None attributes)
    attrs = account.get("attributes")
    if not isinstance(attrs, dict):
        attrs = {}

    # Active Directory userAccountControl (UAC) check
    uac = attrs.get("userAccountControl")
    if uac is not None:
        try:
            uac_int = int(uac)
            if uac_int & 0x0002:  # ACCOUNTDISABLE bit
                return True
        except (ValueError, TypeError):
            pass

    if str(attrs.get("IIQDisabled", "")).strip().lower() in ("true", "1", "yes"):
        return True

    # If root-level is explicitly False, the account is active in ISC
    if account.get("disabled") is False:
        return False

    attr_disabled = attrs.get("disabled")
    if attr_disabled is True or str(attr_disabled).strip().lower() in ("true", "1", "yes"):
        return True

    # 4. Status keyword check
    status_val = str(attrs.get("status", "")).strip().lower()
    if status_val in ("disabled", "inactive", "suspended", "locked"):
        return True

    employee_status = str(attrs.get("employeeStatus", "")).strip().lower()
    if employee_status in ("emergency", "terminated", "inactive", "suspended"):
        return True

    return False


def validate_account_exists(
    identity_id: str,
    source_id: str,
    source_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify whether an account exists for the given identity on the specified target source."""
    account = get_account_on_source(identity_id, source_id)
    exists = account is not None
    src_label = source_name or source_id

    # If not found via direct source lookup, check identity's embedded accounts
    if not exists:
        user = get_identity_by_id(identity_id)
        if user and user.get("accounts"):
            for acc in user.get("accounts", []):
                acc_src = acc.get("source") if isinstance(acc.get("source"), dict) else {}
                if acc.get("sourceId") == source_id or acc_src.get("id") == source_id:
                    account = acc
                    exists = True
                    break

    logger.info(
        f"Validation [Account Existence]: Identity={identity_id}, Source={src_label}, Exists={exists}"
    )

    return {
        "passed": exists,
        "check": "Account Existence Verification",
        "details": (
            f"Account found on source '{src_label}' (Account ID: {account.get('id') if account else 'N/A'})"
            if exists
            else f"No account exists for identity on source '{src_label}'."
        ),
        "account": account,
        "source_id": source_id,
    }


def validate_account_status(
    identity_id: str,
    source_id: str,
    expected_status: str,  # "Enabled" or "Disabled"
    source_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify that the account on the target source has the expected Enabled or Disabled status."""
    acc_check = validate_account_exists(identity_id, source_id, source_name)
    account = acc_check.get("account")
    src_label = source_name or source_id

    if not account:
        return {
            "passed": False,
            "check": "Account Status Verification",
            "details": f"Cannot verify status: No account found on source '{src_label}'.",
            "actual_status": None,
            "expected_status": expected_status,
        }

    is_disabled = is_account_disabled_status(account)
    actual_status = "Disabled" if is_disabled else "Enabled"

    expected_clean = expected_status.strip().capitalize()
    is_matched = actual_status == expected_clean

    logger.info(
        f"Validation [Account Status]: Source={src_label}, Expected='{expected_clean}', "
        f"Actual='{actual_status}', Match={is_matched}"
    )

    return {
        "passed": is_matched,
        "check": "Account Status Verification",
        "details": (
            f"Account status is correctly '{actual_status}' on '{src_label}'."
            if is_matched
            else f"Account status mismatch on '{src_label}': expected '{expected_clean}', actual '{actual_status}'."
        ),
        "actual_status": actual_status,
        "expected_status": expected_clean,
        "account_id": account.get("id"),
        "account_native_identity": account.get("nativeIdentity") or account.get("name"),
    }

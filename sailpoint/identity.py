"""Identity search, retrieval, and attribute management for SailPoint ISC."""

from typing import List, Dict, Any, Optional
from sailpoint.api_client import api_client, ApiClientError
from reporting.logger import get_logger

logger = get_logger("identity")


def extract_identity_attributes(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw SailPoint identity data into the required project attribute format."""
    attrs = raw.get("attributes") or {}
    profile = raw.get("identityProfile") or {}
    source = raw.get("source") or {}
    accounts = raw.get("accounts") or []

    # Resolve manager reference if present
    manager_info = raw.get("manager") or attrs.get("manager") or {}
    manager_name = (
        manager_info.get("name") or manager_info.get("displayName")
        if isinstance(manager_info, dict)
        else str(manager_info or "None")
    )

    # Resolve primary AD / source account identifier
    primary_account_id = None
    first_acc_src = {}
    if accounts:
        primary_account_id = accounts[0].get("id") or accounts[0].get("accountId")
        if isinstance(accounts[0].get("source"), dict):
            first_acc_src = accounts[0]["source"]

    source_id = source.get("id") or first_acc_src.get("id") or (accounts[0].get("sourceId") if accounts else None)
    source_name = source.get("name") or first_acc_src.get("name") or (accounts[0].get("sourceName") if accounts else "N/A")

    # Resolve lifecycle state name safely (handles dict or string from beta API)
    state_val = raw.get("lifecycleState")
    if isinstance(state_val, dict):
        state_name = state_val.get("stateName")
    elif isinstance(state_val, str):
        state_name = state_val
    else:
        state_name = None

    effective_state = (
        state_name
        or attrs.get("cloudLifecycleState")
        or attrs.get("lifecycleState")
        or "unknown"
    )

    return {
        "id": raw.get("id"),
        "name": raw.get("name") or raw.get("displayName") or raw.get("alias"),
        "displayName": raw.get("displayName") or raw.get("name"),
        "email": raw.get("email") or raw.get("emailAddress") or attrs.get("email"),
        "department": attrs.get("department") or "N/A",
        "lifecycleState": effective_state,
        "identityProfileId": profile.get("id") or raw.get("identityProfileId"),
        "identityProfileName": profile.get("name") or raw.get("identityProfileName") or "N/A",
        "sourceId": source_id,
        "sourceName": source_name,
        "accountId": primary_account_id or attrs.get("identificationNumber") or "N/A",
        "accounts": accounts,
        "manager": manager_name,
        "inactive": raw.get("inactive", False),
        "modified": raw.get("modified") or raw.get("lastRefresh") or "N/A",
        "raw": raw,
    }


def search_identities(query_text: str, limit: int = 25) -> List[Dict[str, Any]]:
    """Search identities using the SailPoint Search API (/v3/search).
    
    Supports searching by name, email, or identity ID.
    """
    clean_query = query_text.strip()
    if not clean_query or clean_query == "*":
        search_query = "*"
    elif ":" in clean_query:
        search_query = clean_query
    else:
        # Wildcard match across name, email, and ID
        search_query = (
            f'name:*{clean_query}* OR displayName:*{clean_query}* '
            f'OR email:*{clean_query}* OR id:"{clean_query}"'
        )

    payload = {
        "indices": ["identities"],
        "query": {"query": search_query},
    }

    try:
        results = api_client.post(f"/v3/search?limit={limit}", json_data=payload)
        if isinstance(results, list):
            logger.info(f"Identity search for '{query_text}' returned {len(results)} identities.")
            return [extract_identity_attributes(item) for item in results]
        return []
    except ApiClientError as e:
        logger.error(f"Search identities failed: {e}")
        return []


def get_all_identities(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve existing test identities from SailPoint ISC."""
    # First attempt to query Truist / Delimited File profile or general query
    payload = {
        "indices": ["identities"],
        "query": {"query": "*"},
    }
    try:
        results = api_client.post(f"/v3/search?limit={limit}", json_data=payload)
        if isinstance(results, list) and results:
            logger.info(f"Retrieved {len(results)} identities from tenant.")
            return [extract_identity_attributes(item) for item in results]
    except ApiClientError as e:
        logger.warning(f"General identity search failed: {e}. Trying beta identities...")

    # Fallback to beta endpoint if search is unavailable
    try:
        results = api_client.get(f"/beta/identities?limit={limit}")
        if isinstance(results, list):
            return [extract_identity_attributes(item) for item in results]
    except ApiClientError as e:
        logger.error(f"Failed to fetch identities via beta endpoint: {e}")

    return []


def get_identity_by_id(identity_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full details of a specific identity by its unique ID.
    
    Combines direct DB lookup (/beta/identities) for real-time lifecycle state
    with search indexing (/v3/search) or account lookups for rich profile/account mappings.
    """
    clean_id = (identity_id or "").strip()
    if not clean_id:
        return None

    # 1. Fetch live authoritative state directly from transactional API
    live_identity = None
    try:
        live_res = api_client.get(f"/beta/identities/{clean_id}")
        if isinstance(live_res, dict) and "id" in live_res:
            live_identity = live_res
    except ApiClientError as e:
        logger.debug(f"Direct /beta/identities lookup for {clean_id} failed: {e}")

    # 2. Fetch rich identity metadata (profile, source, accounts) from search
    search_payload = {
        "indices": ["identities"],
        "query": {"query": f'id:{clean_id}'},
    }
    search_record = None
    try:
        search_res = api_client.post("/v3/search?limit=1", json_data=search_payload)
        if isinstance(search_res, list) and search_res:
            search_record = search_res[0]
    except ApiClientError as e:
        logger.debug(f"Search API lookup for {clean_id} failed: {e}")

    if not live_identity and not search_record:
        return None

    # Base attributes from search (or live identity if search missed)
    base = search_record or live_identity
    extracted = extract_identity_attributes(base)

    # If live_identity is available, override real-time fields directly from DB
    if live_identity:
        live_state_obj = live_identity.get("lifecycleState")
        if isinstance(live_state_obj, dict):
            live_state = live_state_obj.get("stateName")
        elif isinstance(live_state_obj, str):
            live_state = live_state_obj
        else:
            live_state = None

        if live_state:
            extracted["lifecycleState"] = live_state

        if "inactive" in live_identity:
            extracted["inactive"] = live_identity.get("inactive")
        if "modified" in live_identity:
            extracted["modified"] = live_identity.get("modified")

    # Ensure accounts are populated if empty
    if not extracted.get("accounts") and clean_id:
        try:
            from sailpoint.accounts import get_accounts_for_identity
            accs = get_accounts_for_identity(clean_id)
            if accs:
                extracted["accounts"] = accs
                if extracted.get("accountId") == "N/A" and accs:
                    extracted["accountId"] = accs[0].get("id") or accs[0].get("accountId")
        except Exception:
            pass

    return extracted


def format_identity_card(identity: Dict[str, Any]) -> str:
    """Format identity details as an informative text card for interactive display."""
    lines = [
        "--------------------------------------------------------------------------------",
        f"  IDENTITY DETAILS: {identity.get('displayName')} ({identity.get('id')})",
        "--------------------------------------------------------------------------------",
        f"  * Name            : {identity.get('name')}",
        f"  * Email           : {identity.get('email')}",
        f"  * Department      : {identity.get('department')}",
        f"  * Lifecycle State : {identity.get('lifecycleState')}",
        f"  * Identity Profile: {identity.get('identityProfileName')} (ID: {identity.get('identityProfileId')})",
        f"  * Primary Source  : {identity.get('sourceName')} (ID: {identity.get('sourceId')})",
        f"  * Account ID      : {identity.get('accountId')}",
        f"  * Manager         : {identity.get('manager')}",
        f"  * Inactive        : {identity.get('inactive')}",
        f"  * Last Modified   : {identity.get('modified')}",
        "--------------------------------------------------------------------------------",
    ]
    return "\n".join(lines)


def format_identity_details_view(identity: Dict[str, Any]) -> str:
    """Format full Identity Details and Attributes matching SailPoint UI (Image 1)."""
    raw = identity.get("raw") or {}
    attrs = raw.get("attributes") or {}

    lines = [
        "=" * 80,
        f"  IDENTITY: {identity.get('displayName')} (Details & Attributes)",
        "=" * 80,
        f"  Display Name      : {identity.get('displayName')}",
        f"  Email             : {identity.get('email') or 'N/A'}",
        f"  Identity ID       : {identity.get('id')}",
        f"  Account Name      : {identity.get('name') or identity.get('displayName')}",
        f"  Manager           : {identity.get('manager') or '--'}",
        f"  Lifecycle State   : {identity.get('lifecycleState')}",
        f"  Identity State    : {'INACTIVE' if identity.get('inactive') else 'ACTIVE'}",
        f"  Identity Profile  : {identity.get('identityProfileName')} (ID: {identity.get('identityProfileId')})",
        f"  Created           : {raw.get('created') or '--'}",
        f"  Last Modified     : {identity.get('modified') or raw.get('modified') or '--'}",
        "-" * 80,
        "  Identity Attributes:",
    ]

    # Display key attributes first, then remaining
    priority_keys = [
        "department", "displayName", "email", "firstname", "firstName",
        "lastname", "lastName", "uid", "disabled", "employeeStatus",
        "cloudLifecycleState", "cloudAuthoritativeSource"
    ]
    seen_keys = set()
    for k in priority_keys:
        if k in attrs:
            lines.append(f"    * {k:<22}: {attrs[k]}")
            seen_keys.add(k)

    for k, v in sorted(attrs.items()):
        if k not in seen_keys:
            lines.append(f"    * {k:<22}: {v}")

    lines.append("=" * 80)
    return "\n".join(lines)


def format_accounts_table_view(accounts: List[Dict[str, Any]], identity_name: str = "") -> str:
    """Format correlated accounts summary table matching SailPoint UI (Image 2)."""
    title = f"CORRELATED ACCOUNTS: {identity_name}" if identity_name else "CORRELATED ACCOUNTS"
    lines = [
        "=" * 80,
        f"  {title} ({len(accounts)} Results)",
        "=" * 80,
        f"{'#':<3} {'Account Name':<20} {'Native Identity':<18} {'Source Name':<20} {'Status':<10} {'Last Modified'}",
        "-" * 80,
    ]

    for idx, acc in enumerate(accounts, 1):
        name = str(acc.get("name") or acc.get("displayName") or "N/A")[:18]
        native_id = str(acc.get("nativeIdentity") or acc.get("id") or "N/A")[:16]
        src_name = str(acc.get("sourceName") or (acc.get("source") or {}).get("name") or "N/A")[:18]
        status = acc.get("calculatedStatus") or ("Disabled" if acc.get("disabled") else "Enabled")
        mod_date = str(acc.get("modified") or "N/A")[:19].replace("T", " ")
        lines.append(f"{idx:<3} {name:<20} {native_id:<18} {src_name:<20} [{status:<8}] {mod_date}")

    lines.append("=" * 80)
    return "\n".join(lines)


def format_account_detail_card(account: Dict[str, Any]) -> str:
    """Format single account details and raw source attributes matching SailPoint UI (Image 3)."""
    acc_name = account.get("name") or "N/A"
    src_name = account.get("sourceName") or (account.get("source") or {}).get("name") or "N/A"
    identity_ref = account.get("identity") or {}
    identity_label = identity_ref.get("name") if isinstance(identity_ref, dict) else str(identity_ref or "N/A")

    status = account.get("calculatedStatus") or ("Disabled" if account.get("disabled") else "Enabled")
    attrs = account.get("attributes") or {}

    lines = [
        "=" * 80,
        f"  SOURCE ACCOUNT: {acc_name} ON {src_name}",
        "=" * 80,
        f"  * Name                : {acc_name}",
        f"  * Account ID          : {account.get('id')}",
        f"  * Native Identity     : {account.get('nativeIdentity')}",
        f"  * Correlated Identity : {identity_label} (ID: {account.get('identityId') or (identity_ref.get('id') if isinstance(identity_ref, dict) else 'N/A')})",
        f"  * Source Name         : {src_name} (ID: {account.get('sourceId')})",
        f"  * Manually Correlated : {account.get('manuallyCorrelated', False)}",
        f"  * Status              : {status}",
        f"  * Locked              : {account.get('locked', False)}",
        f"  * Authoritative       : {account.get('authoritative', False)}",
        f"  * Created             : {account.get('created') or '--'}",
        f"  * Last Modified       : {account.get('modified') or '--'}",
        "-" * 80,
        f"  Raw Source Attributes (Inbound Feed Data - {len(attrs)} fields):",
    ]

    for k, v in sorted(attrs.items()):
        lines.append(f"    * {k:<20}: {v}")

    lines.append("=" * 80)
    return "\n".join(lines)


def display_account_drilldown(
    accounts: List[Dict[str, Any]],
    identity_name: str = "",
    interactive: bool = True,
) -> None:
    """Display correlated accounts with interactive option for individual drill-down or all accounts."""
    if not accounts:
        print(f"\nNo correlated accounts found for {identity_name}.\n")
        return

    print("\n" + format_accounts_table_view(accounts, identity_name) + "\n")

    if not interactive:
        print("Displaying details for all correlated accounts:")
        for acc in accounts:
            print(format_account_detail_card(acc) + "\n")
        return

    while True:
        prompt_text = (
            f"Select an account to view full source attributes [1-{len(accounts)}], "
            f"'A' for All accounts, or [ENTER/B] to return: "
        )
        choice = input(prompt_text).strip().lower()

        if choice in ("", "b", "back", "exit", "q"):
            break

        if choice in ("a", "all"):
            print("\n" + "=" * 80)
            print(f"  SHOWING ALL {len(accounts)} CORRELATED ACCOUNTS FOR {identity_name}")
            print("=" * 80 + "\n")
            for idx, acc in enumerate(accounts, 1):
                print(f">>> Account [{idx}/{len(accounts)}]:")
                print(format_account_detail_card(acc) + "\n")
            break

        try:
            sel_idx = int(choice) - 1
            if 0 <= sel_idx < len(accounts):
                selected_acc = accounts[sel_idx]
                print("\n" + format_account_detail_card(selected_acc) + "\n")
            else:
                print(f"Invalid selection. Please choose 1-{len(accounts)}, 'A', or 'B'.")
        except ValueError:
            print("Invalid input. Enter a number, 'A', or 'B'.")

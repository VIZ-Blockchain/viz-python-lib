"""
HF15 agent access (op-id 105 ``set_agent_permission``) — read-side helpers.

A principal may register agents: a label plus a public key that may sign an explicit list of the
principal's operations, optionally scoped to off-chain addons, optionally expiring. An agent is
not an account and never appears in any authority, so "look at active_authority.key_auths" rejects
agent keys. The recipe is authority OR agents; :func:`check` does both.

Mirrors ``agent.js`` of viz-js-lib and ``VIZ\\Agent`` of viz-php-lib; the node
(``agent_evaluator.cpp::usable_agent_row``) is the source of truth.
"""

from datetime import datetime, timezone
from typing import Any

from grapheneapi.exceptions import RPCError

from vizbase.account import PublicKey
from vizbase.chains import DEFAULT_PREFIX

from .instance import shared_blockchain_instance

# Mirrors the node's never_delegable_operation_names(): a row holding one of these grants nothing.
NEVER_DELEGABLE = frozenset(
    {
        "set_agent_permission",
        "proposal_update",
        "account_update",
        "recover_account",
        "change_recovery_account",
        "set_account_price",
        "set_subaccount_price",
        "target_account_sale",
    }
)

# Authority roles a key can belong to, most privileged first. Agents answer for none of them.
ROLES = ("master", "active", "regular")


def normalize_key(key: str) -> str:
    """Canonical ``VIZ...`` form of an encoded public key; the stripped input if it cannot be parsed."""
    value = str(key or "").strip()
    try:
        return format(
            PublicKey(DEFAULT_PREFIX + value.removeprefix(DEFAULT_PREFIX), prefix=DEFAULT_PREFIX), DEFAULT_PREFIX
        )
    except Exception:
        return value


def key_equals(a: object, b: object) -> bool:
    return isinstance(a, str) and isinstance(b, str) and normalize_key(a) == normalize_key(b)


def is_expired(row: dict) -> bool:
    """The node's own ``expired`` flag wins; the timestamp against the local clock is the fallback."""
    if "expired" in row:
        return bool(row["expired"])
    try:
        # The chain reports UTC without a trailing 'Z'.
        expiration = datetime.fromisoformat(row["expiration"]).replace(tzinfo=timezone.utc)
    except (KeyError, TypeError, ValueError):
        return False
    # epoch = perpetual
    return 0 < expiration.timestamp() <= datetime.now(timezone.utc).timestamp()


def poisoned(row: dict) -> bool:
    """True when the row lists a never-delegable name: the node refuses such a row whole."""
    return not NEVER_DELEGABLE.isdisjoint(row.get("operations") or ())


def grants(row: dict, operation: str) -> bool:
    """True when the row covers ``operation`` (wire name, e.g. ``transfer``) and is not poisoned."""
    return operation in (row.get("operations") or ()) and not poisoned(row)


def addon_matches(row: dict, scope: str) -> bool:
    """True when the row carries the off-chain ``scope`` (exact, case-sensitive) and is not poisoned."""
    return scope in (row.get("addons") or ()) and not poisoned(row)


def in_authority(authority: dict | None, key: str) -> bool:
    """True when ``key`` alone meets the authority's threshold. Nested account_auths are not resolved."""
    if not authority:
        return False
    weight = sum(int(w) for k, w in authority.get("key_auths", ()) if key_equals(k, key))
    return weight > 0 and weight >= int(authority.get("weight_threshold", 0))


def find(account: str, key: str, blockchain_instance: Any = None) -> dict | None:
    """First live agent row of ``account`` signed by ``key``, or None."""
    rpc = (blockchain_instance or shared_blockchain_instance()).rpc
    try:
        rows = rpc.get_agent_permissions(account)
    except RPCError:
        # A node without HF15 has no such method: no agents. Transport errors still propagate.
        return None
    for row in rows or ():
        if row.get("agent_key") and not is_expired(row) and key_equals(row["agent_key"], key):
            return row
    return None


def has(account: str, key: str, operation: str | None = None, blockchain_instance: Any = None) -> bool:
    """True when ``key`` is a live agent of ``account`` — and, if ``operation`` is given, may sign it."""
    row = find(account, key, blockchain_instance)
    return row is not None and (not operation or grants(row, operation))


def check(account: str, key: str, operation: str | None = None, blockchain_instance: Any = None) -> dict:
    """
    May ``key`` act for ``account``? Authority roles first, then agents.

    Returns ``{"allowed", "source": "authority"|"agent"|"none", "role", "agent", "operation"}``.
    With ``operation`` omitted an agent is only answered as "this is a live agent key"; pass the
    wire name to check a specific operation. An authority match is by direct key membership and
    does not consider which role ``operation`` requires. For the full recursive check use the
    node's ``verify_authority`` with a signed transaction.
    """
    result = {"allowed": False, "source": "none", "role": None, "agent": None, "operation": operation}
    rpc = (blockchain_instance or shared_blockchain_instance()).rpc
    accounts = rpc.get_accounts([account])
    if accounts and accounts[0] and accounts[0].get("name") == account:
        for role in ROLES:
            if in_authority(accounts[0].get(f"{role}_authority"), key):
                return {**result, "allowed": True, "source": "authority", "role": role}
    row = find(account, key, blockchain_instance)
    if row is not None and (not operation or grants(row, operation)):
        return {**result, "allowed": True, "source": "agent", "agent": row}
    return result

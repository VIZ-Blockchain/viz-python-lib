"""
Witness -> Validator migration compatibility layer.

Single source of truth for old -> new name translation. When the migration
is complete (Phase C), delete this file and remove all imports from it.
"""

import warnings

# Wire-format op name aliases (old -> new).
OP_NAME_ALIASES = {
    "witness_update": "validator_update",
    "account_witness_vote": "account_validator_vote",
    "account_witness_proxy": "account_validator_proxy",
    "shutdown_witness": "shutdown_validator",
    "witness_reward": "validator_reward",
}

# JSON-RPC API method aliases (old -> new).
API_METHOD_ALIASES = {
    "get_active_witnesses": "get_active_validators",
    "get_witness_schedule": "get_validator_schedule",
    "get_witnesses": "get_validators",
    "get_witness_by_account": "get_validator_by_account",
    "get_witnesses_by_vote": "get_validators_by_vote",
    "get_witnesses_by_counted_vote": "get_validators_by_counted_vote",
    "get_witness_count": "get_validator_count",
    "lookup_witness_accounts": "lookup_validator_accounts",
    "debug_get_witness_schedule": "debug_get_validator_schedule",
}

# Chain-properties field aliases (old -> new). Applies to chain_properties_hf4/hf6/hf9.
CHAIN_PROPS_FIELD_ALIASES = {
    "inflation_witness_percent": "inflation_validator_percent",
    "witness_miss_penalty_percent": "validator_miss_penalty_percent",
    "witness_miss_penalty_duration": "validator_miss_penalty_duration",
    "witness_declaration_fee": "validator_declaration_fee",
}

# Per-op kwarg field aliases (old -> new), keyed by canonical new op name.
OP_FIELD_ALIASES = {
    "account_validator_vote": {"witness": "validator"},
    "validator_reward": {"witness": "validator"},  # virtual op; reserved for future use
}


def translate_kwargs(kwargs: dict, alias_map: dict, *, context: str) -> dict:
    """
    Return a copy of `kwargs` with old keys renamed to new keys per `alias_map`.

    Emits one DeprecationWarning per old key found, citing `context`.
    If both old and new keys are present, the new value wins and the old
    key triggers a warning.
    """
    out = dict(kwargs)
    for old, new in alias_map.items():
        if old in out:
            warnings.warn(
                f"{context}: '{old}' is deprecated; use '{new}' instead",
                DeprecationWarning,
                stacklevel=3,
            )
            if new not in out:
                out[new] = out.pop(old)
            else:
                out.pop(old)
    return out


def pick(obj, *keys, default=None):
    """
    Return obj[k] for the first k in `keys` that exists; else `default`.

    Used at response-read sites to tolerate both old (witness_*) and new
    (validator_*) field names. Call with new key first, old key second.
    """
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            return obj[k]
        if not isinstance(obj, dict) and hasattr(obj, k):
            return getattr(obj, k)
    return default

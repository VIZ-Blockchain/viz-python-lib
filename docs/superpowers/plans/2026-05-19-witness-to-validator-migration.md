# Witness → Validator Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the Python lib to Phase A of the witness → validator terminology migration: send new names on the wire, accept both old and new names from callers (with `DeprecationWarning`), tolerate old nodes via a runtime fallback.

**Architecture:** Single compat module `vizbase/validator_compat.py` is the source of truth for old↔new translation (op names, API methods, chain-properties field names, per-op kwarg renames). Operation classes and chain-properties builder run incoming `kwargs` through `translate_kwargs()` and warn on old names. Wire JSON uses new names exclusively. API dispatcher in `vizapi/noderpc.py` canonicalizes inbound calls (old name → new name) and falls back to `witness_api` namespace on `NoSuchMethod` errors, caching the result per `Rpc` instance.

**Tech Stack:** Python 3.10+, pytest, poetry, graphenebase / graphenecommon / grapheneapi (upstream).

**Spec:** `docs/superpowers/specs/2026-05-19-witness-to-validator-migration-design.md`

**Implementation note found during planning:** `graphenecommon.witness.Witness.__init__` calls `self.blockchain.rpc.get_witness_by_account(...)` (line 27/32 in upstream). Since we remove `get_witness_by_account` from `vizapi/consts.py:API`, the dispatcher must canonicalize inbound method names too (translate old → new at the top of `Rpc.__getattr__`), not only fall back on failure. Task 9 covers both. This is consistent with the spec's "Phase A dual-support" intent.

**Implementation note on op-class resolution:** `graphenebase.objects.Operation.klass_name` is `name[0].upper() + name[1:]` (verified during planning). So `"validator_update"` → `"Validator_update"` class. The existing class naming convention is preserved. Old op names resolve to deprecated alias classes (e.g. `"witness_update"` → `"Witness_update"`) which inherit from the new canonical class.

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `vizbase/validator_compat.py` | **Create** | Old↔new alias dicts + `translate_kwargs` + `pick` helpers |
| `vizbase/operationids.py` | Modify | Rename op strings in `OPS` / `VIRTUAL_OPS`; extend `operations` dict with old-name aliases |
| `vizbase/operations.py` | Modify | Rename `Witness_update` / `Account_witness_vote` classes; kwarg translation; deprecated aliases |
| `vizbase/objects.py` | Modify | Rename 4 chain_properties field names; kwarg translation |
| `vizapi/consts.py` | Modify | Replace 9 `witness_api` entries with `validator_api` entries |
| `vizapi/exceptions.py` | Modify | Add `NoSuchMethod` exception class |
| `vizapi/noderpc.py` | Modify | Detect `NoSuchMethod` in `post_process_exception`; inbound translation + outbound fallback in `Rpc.__getattr__` |
| `viz/witness.py` | **Rename → `viz/validator.py`** | Classes renamed to `Validator` / `Validators` |
| `viz/witness.py` (new) | **Create** | Deprecation shim re-exporting from `viz.validator` |
| `viz/blockchain.py` | Modify | Update docstring examples; canonicalize stream `filter_by` |
| `viz/viz.py` | Modify | Update TODO comments (witness → validator) |
| `tests/test_serialization.py` | Modify | Use new chain_properties field names |
| `tests/test_blockchain.py` | Modify | Use `validator_reward` instead of `witness_reward` |
| `tests/test_validator_compat.py` | **Create** | Unit tests for compat module + alias resolution + dispatcher fallback + module shim |

---

## Task 1: Create `vizbase/validator_compat.py`

**Files:**
- Create: `vizbase/validator_compat.py`
- Create: `tests/test_validator_compat.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_validator_compat.py` with this content:

```python
"""Unit tests for the witness -> validator compatibility layer."""
import warnings

import pytest

from vizbase.validator_compat import (
    API_METHOD_ALIASES,
    CHAIN_PROPS_FIELD_ALIASES,
    OP_FIELD_ALIASES,
    OP_NAME_ALIASES,
    pick,
    translate_kwargs,
)


def test_op_name_aliases_complete():
    assert OP_NAME_ALIASES == {
        "witness_update": "validator_update",
        "account_witness_vote": "account_validator_vote",
        "account_witness_proxy": "account_validator_proxy",
        "shutdown_witness": "shutdown_validator",
        "witness_reward": "validator_reward",
    }


def test_api_method_aliases_complete():
    assert API_METHOD_ALIASES == {
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


def test_chain_props_field_aliases_complete():
    assert CHAIN_PROPS_FIELD_ALIASES == {
        "inflation_witness_percent": "inflation_validator_percent",
        "witness_miss_penalty_percent": "validator_miss_penalty_percent",
        "witness_miss_penalty_duration": "validator_miss_penalty_duration",
        "witness_declaration_fee": "validator_declaration_fee",
    }


def test_op_field_aliases_account_validator_vote():
    assert OP_FIELD_ALIASES["account_validator_vote"] == {"witness": "validator"}


def test_translate_kwargs_renames_and_warns():
    with pytest.warns(DeprecationWarning, match=r"'witness' is deprecated; use 'validator'"):
        out = translate_kwargs(
            {"witness": "alice", "approve": True},
            {"witness": "validator"},
            context="Account_validator_vote",
        )
    assert out == {"validator": "alice", "approve": True}


def test_translate_kwargs_no_warning_for_new_names():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        out = translate_kwargs(
            {"validator": "alice", "approve": True},
            {"witness": "validator"},
            context="Account_validator_vote",
        )
    assert out == {"validator": "alice", "approve": True}


def test_translate_kwargs_new_wins_when_both_present():
    with pytest.warns(DeprecationWarning):
        out = translate_kwargs(
            {"witness": "alice", "validator": "bob"},
            {"witness": "validator"},
            context="Account_validator_vote",
        )
    assert out == {"validator": "bob"}


def test_translate_kwargs_returns_copy():
    inp = {"witness": "alice"}
    with pytest.warns(DeprecationWarning):
        out = translate_kwargs(inp, {"witness": "validator"}, context="ctx")
    assert "witness" in inp
    assert out == {"validator": "alice"}


def test_pick_returns_first_present_dict_key():
    d = {"current_shuffled_witnesses": ["a"]}
    assert pick(d, "current_shuffled_validators", "current_shuffled_witnesses") == ["a"]


def test_pick_prefers_first_listed():
    d = {"current_shuffled_validators": ["new"], "current_shuffled_witnesses": ["old"]}
    assert pick(d, "current_shuffled_validators", "current_shuffled_witnesses") == ["new"]


def test_pick_default_when_none_present():
    assert pick({}, "a", "b", default=[]) == []


def test_pick_works_on_objects_with_attributes():
    class O:
        current_validator = "alice"
    assert pick(O(), "current_validator", "current_witness") == "alice"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validator_compat.py -v`
Expected: ImportError — `No module named 'vizbase.validator_compat'`

- [ ] **Step 3: Create the module**

Create `vizbase/validator_compat.py`:

```python
"""
Witness -> Validator migration compatibility layer.

Single source of truth for old -> new name translation. When the migration
is complete (Phase C), delete this file and remove all imports from it.
"""
import warnings

# Wire-format op name aliases (old -> new).
OP_NAME_ALIASES = {
    "witness_update":         "validator_update",
    "account_witness_vote":   "account_validator_vote",
    "account_witness_proxy":  "account_validator_proxy",
    "shutdown_witness":       "shutdown_validator",
    "witness_reward":         "validator_reward",
}

# JSON-RPC API method aliases (old -> new).
API_METHOD_ALIASES = {
    "get_active_witnesses":           "get_active_validators",
    "get_witness_schedule":           "get_validator_schedule",
    "get_witnesses":                  "get_validators",
    "get_witness_by_account":         "get_validator_by_account",
    "get_witnesses_by_vote":          "get_validators_by_vote",
    "get_witnesses_by_counted_vote":  "get_validators_by_counted_vote",
    "get_witness_count":              "get_validator_count",
    "lookup_witness_accounts":        "lookup_validator_accounts",
    "debug_get_witness_schedule":     "debug_get_validator_schedule",
}

# Chain-properties field aliases (old -> new). Applies to chain_properties_hf4/hf6/hf9.
CHAIN_PROPS_FIELD_ALIASES = {
    "inflation_witness_percent":      "inflation_validator_percent",
    "witness_miss_penalty_percent":   "validator_miss_penalty_percent",
    "witness_miss_penalty_duration":  "validator_miss_penalty_duration",
    "witness_declaration_fee":        "validator_declaration_fee",
}

# Per-op kwarg field aliases (old -> new), keyed by canonical new op name.
OP_FIELD_ALIASES = {
    "account_validator_vote": {"witness": "validator"},
    "validator_reward":       {"witness": "validator"},  # virtual op; reserved for future use
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
                DeprecationWarning, stacklevel=3,
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validator_compat.py -v`
Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add vizbase/validator_compat.py tests/test_validator_compat.py
git commit -m "Add validator_compat module with alias dicts and translate_kwargs/pick helpers"
```

---

## Task 2: Update `vizbase/operationids.py`

**Files:**
- Modify: `vizbase/operationids.py`
- Test: `tests/test_validator_compat.py` (add tests)

- [ ] **Step 1: Add failing tests for op-id resolution**

Append to `tests/test_validator_compat.py`:

```python
def test_operations_dict_has_new_names():
    from vizbase.operationids import operations
    assert operations["validator_update"] == 6
    assert operations["account_validator_vote"] == 7
    assert operations["account_validator_proxy"] == 8
    assert operations["shutdown_validator"] == 30
    assert operations["validator_reward"] == 42


def test_operations_dict_has_old_name_aliases():
    from vizbase.operationids import operations
    assert operations["witness_update"] == operations["validator_update"] == 6
    assert operations["account_witness_vote"] == operations["account_validator_vote"] == 7
    assert operations["account_witness_proxy"] == operations["account_validator_proxy"] == 8
    assert operations["shutdown_witness"] == operations["shutdown_validator"] == 30
    assert operations["witness_reward"] == operations["validator_reward"] == 42


def test_ops_list_order_preserved():
    """Operation type IDs are positional; renaming must not shift indices."""
    from vizbase.operationids import OPS
    assert OPS.index("transfer") == 2
    assert OPS.index("account_update") == 5
    assert OPS.index("validator_update") == 6
    assert OPS.index("account_validator_vote") == 7
    assert OPS.index("account_validator_proxy") == 8
    assert OPS.index("shutdown_validator") == 30
    assert OPS.index("validator_reward") == 42
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validator_compat.py -v -k operations`
Expected: 3 FAIL — `KeyError: 'validator_update'` etc.

- [ ] **Step 3: Edit `vizbase/operationids.py`**

Replace the file's content with:

```python
from .validator_compat import OP_NAME_ALIASES

#: Operation ids
# Note: take operations from libraries/protocol/include/graphene/protocol/operations.hpp
# Beware to keep operations order!
OPS = [
    "vote",
    "content",
    "transfer",
    "transfer_to_vesting",
    "withdraw_vesting",
    "account_update",
    "validator_update",
    "account_validator_vote",
    "account_validator_proxy",
    "delete_content",
    "custom",
    "set_withdraw_vesting_route",
    "request_account_recovery",
    "recover_account",
    "change_recovery_account",
    "escrow_transfer",
    "escrow_dispute",
    "escrow_release",
    "escrow_approve",
    "delegate_vesting_shares",
    "account_create",
    "account_metadata",
    "proposal_create",
    "proposal_update",
    "proposal_delete",
    "chain_properties_update",
    "author_reward",
    "curation_reward",
    "content_reward",
    "fill_vesting_withdraw",
    "shutdown_validator",
    "hardfork",
    "content_payout_update",
    "content_benefactor_reward",
    "return_vesting_delegation",
    "committee_worker_create_request",
    "committee_worker_cancel_request",
    "committee_vote_request",
    "committee_cancel_request",
    "committee_approve_request",
    "committee_payout_request",
    "committee_pay_request",
    "validator_reward",
    "create_invite",
    "claim_invite_balance",
    "invite_registration",
    "versioned_chain_properties_update",
    "award",
    "receive_award",
    "benefactor_award",
    "set_paid_subscription",
    "paid_subscribe",
    "paid_subscription_action",
    "cancel_paid_subscription",
    "set_account_price",
    "set_subaccount_price",
    "buy_account",
    "account_sale",
    "use_invite_balance",
    "expire_escrow_ratification",
    "fixed_award",
    "target_account_sale",
    "bid",
    "outbid",
]
operations = {o: OPS.index(o) for o in OPS}

# Phase A dual-support: register old op names as aliases pointing to the
# same integer ID. Lookup by either old or new name returns the same id.
# Remove these alias entries during Phase C cleanup.
for _old, _new in OP_NAME_ALIASES.items():
    operations[_old] = operations[_new]

# libraries/protocol/include/graphene/protocol/chain_virtual_operations.hpp
VIRTUAL_OPS = [
    "author_reward",
    "curation_reward",
    "content_reward",
    "fill_vesting_withdraw",
    "shutdown_validator",
    "hardfork",
    "content_payout_update",
    "content_benefactor_reward",
    "return_vesting_delegation",
    "committee_cancel_request",
    "committee_approve_request",
    "committee_payout_request",
    "committee_pay_request",
    "validator_reward",
    "receive_award",
    "benefactor_award",
    "paid_subscription_action",
    "cancel_paid_subscription",
    "expire_escrow_ratification",
    "bid",
    "outbid",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validator_compat.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add vizbase/operationids.py tests/test_validator_compat.py
git commit -m "Rename witness ops to validator in OPS/VIRTUAL_OPS and register old-name aliases"
```

---

## Task 3: Rename `Witness_update` → `Validator_update` with deprecated alias

**Files:**
- Modify: `vizbase/operations.py:271-290`
- Test: `tests/test_validator_compat.py` (add tests)

- [ ] **Step 1: Add failing tests**

Append to `tests/test_validator_compat.py`:

```python
def test_validator_update_class_exists_and_serializes():
    from vizbase.operations import Validator_update
    op = Validator_update(
        owner="alice",
        url="https://alice.example",
        block_signing_key="VIZ1111111111111111111111111111111114T1Anm",
    )
    j = op.json()
    assert j["owner"] == "alice"
    assert j["url"] == "https://alice.example"
    assert j["block_signing_key"] == "VIZ1111111111111111111111111111111114T1Anm"


def test_witness_update_alias_emits_deprecation_warning_once():
    from vizbase.operations import _DeprecatedAlias
    _DeprecatedAlias._warned.discard("Witness_update")

    from vizbase.operations import Validator_update, Witness_update
    with pytest.warns(DeprecationWarning, match=r"Witness_update is deprecated"):
        op1 = Witness_update(
            owner="alice", url="https://x",
            block_signing_key="VIZ1111111111111111111111111111111114T1Anm",
        )
    assert isinstance(op1, Validator_update)

    # Second instantiation: no warning.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        Witness_update(
            owner="alice", url="https://x",
            block_signing_key="VIZ1111111111111111111111111111111114T1Anm",
        )


def test_witness_update_and_validator_update_serialize_identically():
    from vizbase.operations import Validator_update, Witness_update
    kwargs = dict(
        owner="alice",
        url="https://alice.example",
        block_signing_key="VIZ1111111111111111111111111111111114T1Anm",
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        a = bytes(Validator_update(**kwargs))
        b = bytes(Witness_update(**kwargs))
    assert a == b
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validator_compat.py -v -k validator_update`
Expected: FAIL — `ImportError: cannot import name 'Validator_update'`.

- [ ] **Step 3: Edit `vizbase/operations.py`**

At the top of `vizbase/operations.py` (after the existing imports, before `class Account_create`):

```python
import warnings


class _DeprecatedAlias:
    """Warn once-per-process on first instantiation of a deprecated class name."""

    _warned: set[str] = set()

    @classmethod
    def make(cls, old_name: str, new_class: type) -> type:
        warned = cls._warned

        class _Alias(new_class):
            def __init__(self, *args, **kwargs):
                if old_name not in warned:
                    warnings.warn(
                        f"{old_name} is deprecated; use {new_class.__name__} instead",
                        DeprecationWarning, stacklevel=2,
                    )
                    warned.add(old_name)
                super().__init__(*args, **kwargs)

        _Alias.__name__ = old_name
        _Alias.__qualname__ = old_name
        return _Alias
```

Replace the existing `class Witness_update(GrapheneObject):` definition (around line 271) with:

```python
class Validator_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", DEFAULT_PREFIX)

            if not kwargs["block_signing_key"]:
                kwargs["block_signing_key"] = f"{prefix}1111111111111111111111111111111114T1Anm"
            super().__init__(
                OrderedDict(
                    [
                        ("owner", String(kwargs["owner"])),
                        ("url", String(kwargs["url"])),
                        ("block_signing_key", PublicKey(kwargs["block_signing_key"], prefix=prefix)),
                    ]
                )
            )
```

At the bottom of `vizbase/operations.py`, add:

```python
# Deprecated witness-named aliases. Subclasses that warn once per process
# on first instantiation. Remove during Phase C cleanup.
Witness_update = _DeprecatedAlias.make("Witness_update", Validator_update)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validator_compat.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add vizbase/operations.py tests/test_validator_compat.py
git commit -m "Rename Witness_update to Validator_update with deprecated alias"
```

---

## Task 4: Rename `Account_witness_vote` → `Account_validator_vote` with field & kwarg translation

**Files:**
- Modify: `vizbase/operations.py:313-328`
- Test: `tests/test_validator_compat.py` (add tests)

- [ ] **Step 1: Add failing tests**

Append to `tests/test_validator_compat.py`:

```python
def test_account_validator_vote_serializes_new_kwargs():
    from vizbase.operations import Account_validator_vote
    op = Account_validator_vote(account="alice", validator="bob", approve=True)
    j = op.json()
    assert j == {"account": "alice", "validator": "bob", "approve": True}


def test_account_validator_vote_accepts_old_witness_kwarg_with_warning():
    from vizbase.operations import Account_validator_vote
    with pytest.warns(DeprecationWarning, match=r"'witness' is deprecated"):
        op = Account_validator_vote(account="alice", witness="bob", approve=True)
    j = op.json()
    assert j == {"account": "alice", "validator": "bob", "approve": True}


def test_account_witness_vote_alias_class_works():
    from vizbase.operations import _DeprecatedAlias
    _DeprecatedAlias._warned.discard("Account_witness_vote")

    from vizbase.operations import Account_validator_vote, Account_witness_vote
    with pytest.warns(DeprecationWarning):
        op = Account_witness_vote(account="alice", witness="bob", approve=True)
    assert isinstance(op, Account_validator_vote)
    assert op.json() == {"account": "alice", "validator": "bob", "approve": True}


def test_account_validator_vote_old_and_new_serialize_identically():
    from vizbase.operations import Account_validator_vote
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        a = bytes(Account_validator_vote(account="alice", validator="bob", approve=True))
        b = bytes(Account_validator_vote(account="alice", witness="bob", approve=True))
    assert a == b
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validator_compat.py -v -k account_validator_vote`
Expected: FAIL — `cannot import name 'Account_validator_vote'`.

- [ ] **Step 3: Edit `vizbase/operations.py`**

At the top of the file with the other imports, add:

```python
from .validator_compat import OP_FIELD_ALIASES, translate_kwargs
```

Replace the existing `class Account_witness_vote` definition (around line 313) with:

```python
class Account_validator_vote(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            kwargs = translate_kwargs(
                kwargs,
                OP_FIELD_ALIASES["account_validator_vote"],
                context="Account_validator_vote",
            )
            super().__init__(
                OrderedDict(
                    [
                        ("account", String(kwargs["account"])),
                        ("validator", String(kwargs["validator"])),
                        ("approve", Bool(bool(kwargs["approve"]))),
                    ]
                )
            )
```

At the bottom of the file, alongside the `Witness_update` alias, add:

```python
Account_witness_vote = _DeprecatedAlias.make("Account_witness_vote", Account_validator_vote)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validator_compat.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add vizbase/operations.py tests/test_validator_compat.py
git commit -m "Rename Account_witness_vote to Account_validator_vote; translate witness= kwarg"
```

---

## Task 5: Update chain-properties field names in `vizbase/objects.py`

**Files:**
- Modify: `vizbase/objects.py:130-176`
- Test: `tests/test_validator_compat.py` (add tests)

- [ ] **Step 1: Add failing tests**

Append to `tests/test_validator_compat.py`:

```python
CHAIN_PROPS_NEW = {
    "account_creation_fee": "1.000 VIZ",
    "maximum_block_size": 65536,
    "create_account_delegation_ratio": 2,
    "create_account_delegation_time": 3600,
    "min_delegation": "10.000 VIZ",
    "min_curation_percent": 1000,
    "max_curation_percent": 2000,
    "bandwidth_reserve_percent": 1000,
    "bandwidth_reserve_below": "10.000 SHARES",
    "flag_energy_additional_cost": 1000,
    "vote_accounting_min_rshares": 100000,
    "committee_request_approve_min_percent": 1000,
    "inflation_validator_percent": 1000,
    "inflation_ratio_committee_vs_reward_fund": 5000,
    "inflation_recalc_period": 3600,
    "data_operations_cost_additional_bandwidth": 0,
    "validator_miss_penalty_percent": 1000,
    "validator_miss_penalty_duration": 3600,
    "create_invite_min_balance": "1.000 VIZ",
    "committee_create_request_fee": "1.000 VIZ",
    "create_paid_subscription_fee": "1.000 VIZ",
    "account_on_sale_fee": "1.000 VIZ",
    "subaccount_on_sale_fee": "1.000 VIZ",
    "validator_declaration_fee": "1.000 VIZ",
    "withdraw_intervals": 10,
}

CHAIN_PROPS_OLD = {
    **{k: v for k, v in CHAIN_PROPS_NEW.items()
       if k not in {
           "inflation_validator_percent",
           "validator_miss_penalty_percent",
           "validator_miss_penalty_duration",
           "validator_declaration_fee",
       }},
    "inflation_witness_percent": 1000,
    "witness_miss_penalty_percent": 1000,
    "witness_miss_penalty_duration": 3600,
    "witness_declaration_fee": "1.000 VIZ",
}


def test_chain_properties_serializes_with_new_field_names():
    from vizbase.operations import Versioned_chain_properties_update
    op = Versioned_chain_properties_update(owner="alice", props=CHAIN_PROPS_NEW)
    bytes(op)


def test_chain_properties_old_field_names_warn_and_serialize_identically():
    from vizbase.operations import Versioned_chain_properties_update
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        new_bytes = bytes(Versioned_chain_properties_update(owner="alice", props=CHAIN_PROPS_NEW))

    with pytest.warns(DeprecationWarning, match=r"'inflation_witness_percent' is deprecated"):
        op_old = Versioned_chain_properties_update(owner="alice", props=CHAIN_PROPS_OLD)
    old_bytes = bytes(op_old)

    assert new_bytes == old_bytes
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validator_compat.py -v -k chain_properties`
Expected: FAIL — `KeyError: 'inflation_validator_percent'`.

- [ ] **Step 3: Edit `vizbase/objects.py`**

At the top of `vizbase/objects.py` with the other imports, add:

```python
from .validator_compat import CHAIN_PROPS_FIELD_ALIASES, translate_kwargs
```

In the chain-properties `__init__` (around lines 130-176), insert a `translate_kwargs` call before the `OrderedDict` build, and rename the four field names. The full block becomes:

```python
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            kwargs = translate_kwargs(
                kwargs, CHAIN_PROPS_FIELD_ALIASES, context="chain_properties_update",
            )

            super().__init__(
                OrderedDict(
                    [
                        # initial, version 0
                        ("account_creation_fee", Amount(kwargs["account_creation_fee"])),
                        ("maximum_block_size", Uint32(kwargs["maximum_block_size"])),
                        ("create_account_delegation_ratio", Uint32(kwargs["create_account_delegation_ratio"])),
                        ("create_account_delegation_time", Uint32(kwargs["create_account_delegation_time"])),
                        ("min_delegation", Amount(kwargs["min_delegation"])),
                        ("min_curation_percent", Uint16(kwargs["min_curation_percent"])),
                        ("max_curation_percent", Uint16(kwargs["max_curation_percent"])),
                        ("bandwidth_reserve_percent", Uint16(kwargs["bandwidth_reserve_percent"])),
                        ("bandwidth_reserve_below", Amount(kwargs["bandwidth_reserve_below"])),
                        ("flag_energy_additional_cost", Uint16(kwargs["flag_energy_additional_cost"])),
                        ("vote_accounting_min_rshares", Uint32(kwargs["vote_accounting_min_rshares"])),
                        (
                            "committee_request_approve_min_percent",
                            Uint16(kwargs["committee_request_approve_min_percent"]),
                        ),
                        # chain_properties_hf4, version 1
                        ("inflation_validator_percent", Uint16(kwargs["inflation_validator_percent"])),
                        (
                            "inflation_ratio_committee_vs_reward_fund",
                            Uint16(kwargs["inflation_ratio_committee_vs_reward_fund"]),
                        ),
                        ("inflation_recalc_period", Uint32(kwargs["inflation_recalc_period"])),
                        # chain_properties_hf6: version 2
                        (
                            "data_operations_cost_additional_bandwidth",
                            Uint32(kwargs["data_operations_cost_additional_bandwidth"]),
                        ),
                        ("validator_miss_penalty_percent", Uint16(kwargs["validator_miss_penalty_percent"])),
                        ("validator_miss_penalty_duration", Uint32(kwargs["validator_miss_penalty_duration"])),
                        # chain_properties_hf9: version 3
                        ("create_invite_min_balance", Amount(kwargs["create_invite_min_balance"])),
                        ("committee_create_request_fee", Amount(kwargs["committee_create_request_fee"])),
                        ("create_paid_subscription_fee", Amount(kwargs["create_paid_subscription_fee"])),
                        ("account_on_sale_fee", Amount(kwargs["account_on_sale_fee"])),
                        ("subaccount_on_sale_fee", Amount(kwargs["subaccount_on_sale_fee"])),
                        ("validator_declaration_fee", Amount(kwargs["validator_declaration_fee"])),
                        ("withdraw_intervals", Uint16(kwargs["withdraw_intervals"])),
                    ]
                )
            )
```

Field order is preserved. The only changes are the four field renames and the `translate_kwargs` call at the top.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validator_compat.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add vizbase/objects.py tests/test_validator_compat.py
git commit -m "Rename chain_properties witness fields to validator; translate old kwargs"
```

---

## Task 6: Update existing serialization test to new field names

**Files:**
- Modify: `tests/test_serialization.py:62-79`

- [ ] **Step 1: Edit the test**

In `tests/test_serialization.py`, find `test_versioned_chain_properties_update`. Replace the four old field names with new ones in the `props` dict:

- `"inflation_witness_percent"` → `"inflation_validator_percent"`
- `"witness_miss_penalty_percent"` → `"validator_miss_penalty_percent"`
- `"witness_miss_penalty_duration"` → `"validator_miss_penalty_duration"`
- `"witness_declaration_fee"` → `"validator_declaration_fee"`

(Keep all other fields and the surrounding `do_test` call unchanged.)

- [ ] **Step 2: Run the test**

Run: `pytest tests/test_serialization.py::TestSerialization::test_versioned_chain_properties_update -v`

Expected behavior depends on the testnet image:
- Against an upgraded node that accepts new field names: PASS.
- Against `vizblockchain/vizd:pr-85-merge` (predates the rename): FAIL — the node rejects unknown field names in `get_transaction_hex`.

If the test fails because of the testnet image, do not roll back the rename. The failure is expected and documented in the spec's "Integration-test caveat." Mark it `xfail` only if CI green is required:

```python
@pytest.mark.xfail(reason="Requires upgraded vizd image with validator field names")
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_serialization.py
git commit -m "Update chain_properties test to use new validator field names"
```

---

## Task 7: Update `vizapi/consts.py` (API method renames)

**Files:**
- Modify: `vizapi/consts.py:100-108` and `:61`
- Test: `tests/test_validator_compat.py` (add tests)

- [ ] **Step 1: Add failing tests**

Append to `tests/test_validator_compat.py`:

```python
def test_consts_api_has_validator_methods():
    from vizapi.consts import API
    assert API["get_active_validators"] == "validator_api"
    assert API["get_validator_schedule"] == "validator_api"
    assert API["get_validators"] == "validator_api"
    assert API["get_validator_by_account"] == "validator_api"
    assert API["get_validators_by_vote"] == "validator_api"
    assert API["get_validators_by_counted_vote"] == "validator_api"
    assert API["get_validator_count"] == "validator_api"
    assert API["lookup_validator_accounts"] == "validator_api"
    assert API["get_miner_queue"] == "validator_api"
    assert API["debug_get_validator_schedule"] == "debug_node"


def test_consts_api_does_not_have_old_witness_methods():
    from vizapi.consts import API
    for old_name in (
        "get_active_witnesses", "get_witness_schedule", "get_witnesses",
        "get_witness_by_account", "get_witnesses_by_vote",
        "get_witnesses_by_counted_vote", "get_witness_count",
        "lookup_witness_accounts", "debug_get_witness_schedule",
    ):
        assert old_name not in API, f"{old_name} should be removed from API map"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validator_compat.py -v -k consts_api`
Expected: FAIL — KeyError on validator method names.

- [ ] **Step 3: Edit `vizapi/consts.py`**

Replace the `debug_get_witness_schedule` line:

```python
    "debug_get_validator_schedule": "debug_node",
```

Replace the nine `witness_api` block (lines ~100-108) with:

```python
    "get_miner_queue": "validator_api",
    "get_validators_by_counted_vote": "validator_api",
    "get_active_validators": "validator_api",
    "get_validator_schedule": "validator_api",
    "get_validators": "validator_api",
    "get_validator_by_account": "validator_api",
    "get_validators_by_vote": "validator_api",
    "get_validator_count": "validator_api",
    "lookup_validator_accounts": "validator_api",
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validator_compat.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add vizapi/consts.py tests/test_validator_compat.py
git commit -m "Rename witness_api methods to validator_api in vizapi/consts"
```

---

## Task 8: Add `NoSuchMethod` exception

**Files:**
- Modify: `vizapi/exceptions.py`
- Test: `tests/test_validator_compat.py` (add test)

- [ ] **Step 1: Add failing test**

Append to `tests/test_validator_compat.py`:

```python
def test_no_such_method_exception_exists():
    from vizapi.exceptions import NoSuchMethod, RPCError
    assert issubclass(NoSuchMethod, RPCError)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_validator_compat.py -v -k no_such_method`
Expected: FAIL — `cannot import name 'NoSuchMethod'`.

- [ ] **Step 3: Edit `vizapi/exceptions.py`**

Add a new class:

```python
class NoSuchMethod(RPCError):
    """Raised when the node reports the requested method is not available on the API."""
    pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_validator_compat.py -v -k no_such_method`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add vizapi/exceptions.py tests/test_validator_compat.py
git commit -m "Add NoSuchMethod exception for method-not-found RPC errors"
```

---

## Task 9: Dispatcher inbound translation + outbound fallback

**Files:**
- Modify: `vizapi/noderpc.py:38-63` (`post_process_exception`)
- Modify: `vizapi/noderpc.py:101-140` (`Rpc` class)
- Test: `tests/test_validator_compat.py` (add tests)

- [ ] **Step 1: Add failing tests**

Append to `tests/test_validator_compat.py`:

```python
def test_post_process_exception_raises_no_such_method():
    from vizapi.exceptions import NoSuchMethod
    from vizapi.noderpc import NodeRPC

    rpc = NodeRPC.__new__(NodeRPC)

    class FakeError(Exception):
        pass

    err = FakeError("foo bar (123)\nCould not find method get_active_validators\n\n")
    with pytest.raises(NoSuchMethod):
        rpc.post_process_exception(err)


def _build_rpc_with_runner(runner):
    """Build a Rpc with rpcexec stubbed and a request-id counter, no network."""
    from vizapi.noderpc import Rpc
    rpc = Rpc.__new__(Rpc)
    rpc._uses_legacy_witness_api = None
    rpc._request_id = 0

    def get_request_id():
        rpc._request_id += 1
        return rpc._request_id

    def parse_response(resp):
        return resp["result"]

    rpc.get_request_id = get_request_id
    rpc.rpcexec = runner
    rpc.parse_response = parse_response
    return rpc


def test_dispatcher_inbound_translates_old_method_name_with_warning():
    seen = []

    def runner(query):
        seen.append(query["params"])
        return {"result": ["alice", "bob"]}

    rpc = _build_rpc_with_runner(runner)
    with pytest.warns(DeprecationWarning, match=r"get_active_witnesses.*deprecated"):
        result = rpc.get_active_witnesses()
    assert result == ["alice", "bob"]
    assert seen[0] == ["validator_api", "get_active_validators", []]


def test_dispatcher_falls_back_to_witness_api_on_no_such_method():
    from vizapi.exceptions import NoSuchMethod

    calls = []

    def runner(query):
        calls.append(query["params"])
        if query["params"][1] == "get_active_validators":
            raise NoSuchMethod("Could not find method")
        return {"result": ["alice"]}

    rpc = _build_rpc_with_runner(runner)
    with pytest.warns(DeprecationWarning, match=r"witness_api"):
        result = rpc.get_active_validators()
    assert result == ["alice"]
    assert calls[0] == ["validator_api", "get_active_validators", []]
    assert calls[1] == ["witness_api", "get_active_witnesses", []]
    assert rpc._uses_legacy_witness_api is True


def test_dispatcher_uses_cached_legacy_on_subsequent_calls():
    from vizapi.exceptions import NoSuchMethod

    calls = []

    def runner(query):
        calls.append(query["params"])
        if query["params"][1] == "get_active_validators":
            raise NoSuchMethod("Could not find method")
        return {"result": ["alice"]}

    rpc = _build_rpc_with_runner(runner)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rpc.get_active_validators()
        rpc.get_active_validators()

    # First call: tried new then fell back -> 2 calls.
    # Second call: skipped new attempt -> 1 call. Total: 3.
    assert len(calls) == 3
    assert calls[2] == ["witness_api", "get_active_witnesses", []]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_validator_compat.py -v -k dispatcher or post_process_exception`
Expected: FAIL — current dispatcher doesn't translate, doesn't fall back, and `post_process_exception` doesn't raise `NoSuchMethod`.

- [ ] **Step 3: Update `vizapi/noderpc.py`**

Replace the top imports block:

```python
import logging
import warnings
from threading import Lock

from grapheneapi.api import Api as GrapheneApi
from grapheneapi.http import Http as GrapheneHttp
from grapheneapi.rpc import Rpc as GrapheneRpc
from grapheneapi.websocket import Websocket as GrapheneWebsocket

from vizbase.chains import KNOWN_CHAINS
from vizbase.validator_compat import API_METHOD_ALIASES

from . import exceptions
from .consts import API

log = logging.getLogger(__name__)

# Reverse map for runtime fallback: new method name -> old method name.
_REVERSE_API_METHOD = {new: old for old, new in API_METHOD_ALIASES.items()}
```

Replace the body of `post_process_exception` (around lines 38-63):

```python
    def post_process_exception(self, error: Exception) -> None:
        if isinstance(error, exceptions.NoSuchAPI):
            raise

        msg = exceptions.decode_rpc_error_msg(error)
        msg_lower = msg.lower()
        if (
            msg.startswith("Missing Active Authority")
            or msg.startswith("Missing Master Authority")
            or msg.startswith("Missing Authority")
            or msg.startswith("Missing Regular Authority")
        ):
            raise exceptions.MissingRequiredAuthority(msg)
        elif msg == "Unable to acquire READ lock":
            raise exceptions.ReadLockFail(msg)
        elif (
            "could not find method" in msg_lower
            or "method not found" in msg_lower
            or "no such method" in msg_lower
        ):
            raise exceptions.NoSuchMethod(msg)
        elif msg:
            raise exceptions.UnhandledRPCError(msg)
        else:
            raise error
```

Replace the `Rpc` class (around lines 101-140) with:

```python
class Rpc(GrapheneRpc):
    """
    This class is responsible for making RPC queries.

    Phase A of the witness -> validator migration: inbound calls using old
    method names are translated to new names with a DeprecationWarning.
    On a NoSuchMethod error against the new method, the dispatcher falls
    back to the old method on `witness_api` and caches the result so
    subsequent calls skip the new-name attempt.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # None = unknown; True = node only knows witness_api; False = new names confirmed.
        self._uses_legacy_witness_api: bool | None = None

    def __getattr__(self, name):
        """Map all methods to RPC calls and pass through the arguments."""

        def method(*args, **kwargs):
            # Inbound translation: if caller used a deprecated witness_* name,
            # translate to the validator_* equivalent and warn.
            canonical_name = API_METHOD_ALIASES.get(name, name)
            if canonical_name != name:
                warnings.warn(
                    f"API method '{name}' is deprecated; use '{canonical_name}' instead",
                    DeprecationWarning, stacklevel=2,
                )

            api = kwargs.get("api", API.get(canonical_name))
            if not api:
                raise exceptions.NoSuchAPI(f'Cannot find API for you request "{canonical_name}"')

            # Fix wrong api name hardcoded in graphenecommon.TransactionBuilder
            if api == "network_broadcast":
                api = "network_broadcast_api"

            # If the node is known to only speak witness_api, skip new-name attempt.
            if self._uses_legacy_witness_api and canonical_name in _REVERSE_API_METHOD:
                return self._call_legacy(canonical_name, list(args))

            return self._call_with_fallback(api, canonical_name, list(args))

        return method

    def _call_legacy(self, canonical_name: str, params_args: list):
        old_name = _REVERSE_API_METHOD[canonical_name]
        return self._do_call("witness_api", old_name, params_args)

    def _call_with_fallback(self, api: str, canonical_name: str, params_args: list):
        try:
            result = self._do_call(api, canonical_name, params_args)
        except exceptions.NoSuchMethod:
            if canonical_name not in _REVERSE_API_METHOD:
                raise
            if self._uses_legacy_witness_api is None:
                warnings.warn(
                    "Node responded on witness_api; upgrade recommended",
                    DeprecationWarning, stacklevel=4,
                )
            self._uses_legacy_witness_api = True
            return self._call_legacy(canonical_name, params_args)
        else:
            if self._uses_legacy_witness_api is None:
                self._uses_legacy_witness_api = False
            return result

    def _do_call(self, api: str, name: str, params_args: list):
        query = {
            "method": "call",
            "params": [api, name, params_args],
            "jsonrpc": "2.0",
            "id": self.get_request_id(),
        }
        log.debug(query)
        while True:
            try:
                response = self.rpcexec(query)
                message = self.parse_response(response)
            except exceptions.ReadLockFail:
                pass
            else:
                break
        return message
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validator_compat.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add vizapi/noderpc.py tests/test_validator_compat.py
git commit -m "Dispatcher: translate old method names inbound, fall back to witness_api outbound"
```

---

## Task 10: Rename `viz/witness.py` → `viz/validator.py`

**Files:**
- Rename: `viz/witness.py` → `viz/validator.py`
- Test: `tests/test_validator_compat.py` (add test)

- [ ] **Step 1: Add failing test**

Append to `tests/test_validator_compat.py`:

```python
def test_validator_class_importable():
    from viz.validator import Validator, Validators
    from graphenecommon.witness import Witness as GrapheneWitness
    from graphenecommon.witness import Witnesses as GrapheneWitnesses
    assert issubclass(Validator, GrapheneWitness)
    assert issubclass(Validators, GrapheneWitnesses)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_validator_compat.py -v -k validator_class_importable`
Expected: FAIL — `No module named 'viz.validator'`.

- [ ] **Step 3: Move the file and rename classes**

Run:

```bash
git mv viz/witness.py viz/validator.py
```

Replace the contents of `viz/validator.py`:

```python
from graphenecommon.witness import Witness as GrapheneWitness
from graphenecommon.witness import Witnesses as GrapheneWitnesses

from .account import Account
from .instance import BlockchainInstance


@BlockchainInstance.inject
class Validator(GrapheneWitness):
    """
    Read data about a validator in the chain.

    :param str account_name: Name of the validator
    :param viz blockchain_instance: Client() instance to use when
           accesing a RPC

    .. note::
        Inherits from graphenecommon.witness.Witness. Once graphenecommon
        migrates its terminology, this parent can be swapped to the
        validator-named equivalent.
    """

    def define_classes(self):
        self.account_class = Account
        self.type_ids = [6, 2]


@BlockchainInstance.inject
class Validators(GrapheneWitnesses):
    """
    Obtain a list of **active** validators and the current schedule.

    :param bool only_active: (False) Only return validators that are
        actively producing blocks
    :param viz blockchain_instance: Client() instance to use when
        accesing a RPC
    """

    def define_classes(self):
        self.account_class = Account
        # graphenecommon contract: parent asserts self.witness_class.
        self.witness_class = Validator
        # Forward-compat for a future graphenecommon migration. Harmless today.
        self.validator_class = Validator
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_validator_compat.py -v -k validator_class_importable`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add viz/validator.py
git commit -m "Rename viz/witness.py to viz/validator.py with Validator/Validators classes"
```

---

## Task 11: Create `viz/witness.py` deprecation shim

**Files:**
- Create: `viz/witness.py`
- Test: `tests/test_validator_compat.py` (add test)

- [ ] **Step 1: Add failing test**

Append to `tests/test_validator_compat.py`:

```python
def test_viz_witness_shim_emits_warning_and_reexports():
    import sys
    sys.modules.pop("viz.witness", None)

    with pytest.warns(DeprecationWarning, match=r"viz.witness is deprecated"):
        import viz.witness  # noqa: F401

    from viz.validator import Validator, Validators
    assert viz.witness.Witness is Validator
    assert viz.witness.Witnesses is Validators
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_validator_compat.py -v -k viz_witness_shim`
Expected: FAIL — `No module named 'viz.witness'` (renamed in Task 10).

- [ ] **Step 3: Create `viz/witness.py`**

```python
"""
Deprecated module: use viz.validator instead.

This shim re-exports Validator/Validators under their old witness names
to preserve backward compatibility during the witness -> validator
terminology migration. Remove during Phase C cleanup.
"""
import warnings

from .validator import Validator, Validators

warnings.warn(
    "viz.witness is deprecated; import from viz.validator instead",
    DeprecationWarning, stacklevel=2,
)

Witness = Validator
Witnesses = Validators

__all__ = ["Witness", "Witnesses"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_validator_compat.py -v -k viz_witness_shim`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add viz/witness.py tests/test_validator_compat.py
git commit -m "Add viz.witness deprecation shim re-exporting from viz.validator"
```

---

## Task 12: Update `viz/blockchain.py` (docstring + filter canonicalization)

**Files:**
- Modify: `viz/blockchain.py`
- Test: `tests/test_validator_compat.py` (add test)

- [ ] **Step 1: Add failing test**

Append to `tests/test_validator_compat.py`:

```python
def test_filter_canonicalization_helper():
    from viz.blockchain import _canonical_filter
    assert _canonical_filter("witness_reward") == "validator_reward"
    assert _canonical_filter("validator_reward") == "validator_reward"
    assert _canonical_filter("transfer") == "transfer"
    assert _canonical_filter(None) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_validator_compat.py -v -k filter_canonicalization`
Expected: FAIL — `cannot import name '_canonical_filter'`.

- [ ] **Step 3: Read and edit `viz/blockchain.py`**

Read `viz/blockchain.py` to locate the docstring examples and the stream method. Make these edits:

1. Line ~141: `'type': 'witness_reward',` → `'type': 'validator_reward',`
2. Line ~145: `'witness': 'committee',` → `'validator': 'committee',`
3. Line ~160: `'op': ['witness_reward', {'witness': 'committee', 'shares': '0.032999 SHARES'}],` → `'op': ['validator_reward', {'validator': 'committee', 'shares': '0.032999 SHARES'}],`

Add the canonical-filter helper near the top of the file (after the existing imports):

```python
from vizbase.validator_compat import OP_NAME_ALIASES


def _canonical_filter(filter_by):
    """Translate deprecated witness_* op names to validator_*; pass through others."""
    if filter_by is None:
        return None
    return OP_NAME_ALIASES.get(filter_by, filter_by)
```

In the `stream` method, add this line as the first statement of the method body, before any use of `filter_by`:

```python
        filter_by = _canonical_filter(filter_by)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_validator_compat.py -v -k filter_canonicalization`
Expected: PASS.

Sanity check that the blockchain test file still collects without import errors:

Run: `pytest tests/test_blockchain.py -v --collect-only`
Expected: tests collect cleanly.

- [ ] **Step 5: Commit**

```bash
git add viz/blockchain.py tests/test_validator_compat.py
git commit -m "Update viz/blockchain.py docstring examples and canonicalize filter_by"
```

---

## Task 13: Update `tests/test_blockchain.py`

**Files:**
- Modify: `tests/test_blockchain.py:12,14,19,23`

- [ ] **Step 1: Edit the test**

Open `tests/test_blockchain.py`. Update both streaming tests:

- Line 12: `filter_by="witness_reward"` → `filter_by="validator_reward"`
- Line 14: `assert op["type"] == "witness_reward"` → `"validator_reward"`
- Line 19: same as line 12 update
- Line 23: `assert op["op"][0] == "witness_reward"` → `"validator_reward"`

- [ ] **Step 2: Run tests**

Run: `pytest tests/test_blockchain.py -v`

Expected behavior depends on the testnet image:
- Against an upgraded node returning `validator_reward`: PASS.
- Against `pr-85-merge` (still returns `witness_reward`): the canonicalizer in Task 12 makes `filter_by="validator_reward"` match either old or new op names, so the stream call succeeds. The `assert op["type"] == "validator_reward"` will fail because the old node emits `"witness_reward"`. Mark the test `xfail`:

```python
@pytest.mark.xfail(reason="Requires upgraded vizd image that emits validator_reward")
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_blockchain.py
git commit -m "Update test_blockchain.py to use validator_reward op name"
```

---

## Task 14: Update TODO comments in `viz/viz.py`

**Files:**
- Modify: `viz/viz.py:744-757`

- [ ] **Step 1: Edit the TODO block**

In `viz/viz.py`, find the TODO block at the end of the `Client` class (around line 744-757). Replace it with:

```python
    # TODO: Methods to implement:
    # - validator_update
    # - chain_properties_update
    # - allow / disallow
    # - update_memo_key
    # - approve_validator / disapprove_validator
    # - account_metadata
    # - proposal_create / proposal_update / proposal_delete
    # - validator_proxy
    # - recover-related methods
    # - escrow-related methods
    # - worker create / cancel / vote
    # - invite-related: create_invite, claim_invite_balance, invite_registration
    # - paid subscrives related: set_paid_subscription / paid_subscribe
```

- [ ] **Step 2: Commit**

```bash
git add viz/viz.py
git commit -m "Update viz.py TODO comments: witness -> validator"
```

---

## Task 15: Coverage drift test

**Files:**
- Modify: `tests/test_validator_compat.py`

- [ ] **Step 1: Add parametrized coverage tests**

Append to `tests/test_validator_compat.py`:

```python
@pytest.mark.parametrize("old,new", list(OP_NAME_ALIASES.items()))
def test_every_op_alias_resolves(old, new):
    from vizbase.operationids import operations
    assert operations[old] == operations[new]


@pytest.mark.parametrize("old,new", list(API_METHOD_ALIASES.items()))
def test_every_api_alias_in_reverse_map(old, new):
    from vizapi.noderpc import _REVERSE_API_METHOD
    assert _REVERSE_API_METHOD[new] == old


@pytest.mark.parametrize("old,new", list(CHAIN_PROPS_FIELD_ALIASES.items()))
def test_every_chain_props_alias_translatable(old, new):
    out = translate_kwargs({old: 1}, CHAIN_PROPS_FIELD_ALIASES, context="ctx")
    assert out == {new: 1}
```

- [ ] **Step 2: Run the full compat test suite**

Run: `pytest tests/test_validator_compat.py -v`
Expected: all tests pass (parametrized cases should add ~18 new test invocations).

- [ ] **Step 3: Final commit**

```bash
git add tests/test_validator_compat.py
git commit -m "Add parametrized coverage drift tests across all alias dicts"
```

---

## Verification

After all tasks complete, run the unit suite:

```bash
pytest tests/test_validator_compat.py -v
```

Expected: all tests pass.

Run the full non-integration suite:

```bash
pytest tests/ -v --ignore=tests/test_blockchain.py --ignore=tests/test_serialization.py
```

Then the integration suite (requires testnet, may `xfail` until image is rebuilt):

```bash
pytest tests/test_blockchain.py tests/test_serialization.py -v
```

The implementation is complete when the unit suite is green and the integration suite either passes or `xfail`s only on the documented testnet-image-blocked tests.

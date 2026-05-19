# Witness → Validator Migration (Python Lib)

**Date:** 2026-05-19
**Status:** Design approved; ready for implementation plan.
**Reference:** `~/Downloads/witness-to-validator-migration-reference.md` (JS/PHP migration reference)

## Context

The VIZ blockchain is renaming "witness" terminology to "validator" across the entire stack. JSON string names change everywhere (operations, API methods, API namespace, response fields, chain-properties fields, dynamic global properties, account fields, `get_config` keys). Integer operation type IDs and binary wire format are unchanged.

The C++ node already accepts both old and new JSON field names in incoming transactions and responds with new names only. Old API method names remain as deprecated aliases for one release cycle.

This spec brings the Python lib to **Phase A** of the migration (full dual-support), matching the JS/PHP libraries' approach: send new names, accept both old and new on input, fall back to old names when reading from older nodes.

## Goals

- Send new validator names on the wire (op names, API methods, chain-properties fields).
- Accept both old and new names from callers (builder kwargs, op-name filters, API method lookups) with a `DeprecationWarning` when old names are used.
- Tolerate responses from nodes that still emit old names (response-side reads).
- Keep all existing user code working unchanged, emitting clear deprecation warnings for what needs to migrate.
- Make Phase C cleanup (removing the compat layer) a localized, auditable change — single file deletion plus removal of its imports.

## Non-goals

- **New high-level wrapper methods** (`validator_update`, `approve_validator`, `validator_proxy`). Existing TODO comments in `viz/viz.py` get their op names updated; no new functionality added here.
- **graphenecommon migration.** `viz.validator.Validator` continues to inherit from `graphenecommon.witness.Witness`. We do not shadow upstream-owned attributes (`self.witness_class`, etc.). When graphenecommon migrates, a follow-up spec switches inheritance.
- **Phase C cleanup** (removing the compat module, deleted class aliases, `witness_api` fallback). Separate future spec; runs only after node operators have widely upgraded.
- **CLI wallet commands.** Not applicable to a library.
- **Account / block-header / dynamic-global-property / `get_config` reads.** Grep confirms zero current sites in the lib read these response fields by hardcoded name (only `viz/blockchain.py` docstring examples and the stream `filter_by` parameter need attention). If post-merge code adds such reads, use the `pick()` helper introduced here.

## Architecture

A new module **`vizbase/validator_compat.py`** is the single source of truth for the witness→validator translation. Every other file that needs to know about the rename imports from this module.

Phase C cleanup is `git rm vizbase/validator_compat.py` plus deleting its imports — the diff makes the entire rename surface auditable in one place.

### `vizbase/validator_compat.py` contents

```python
import warnings

# Wire-format op name aliases (old -> new)
OP_NAME_ALIASES = {
    "witness_update":         "validator_update",
    "account_witness_vote":   "account_validator_vote",
    "account_witness_proxy":  "account_validator_proxy",
    "shutdown_witness":       "shutdown_validator",
    "witness_reward":         "validator_reward",
}

# JSON-RPC API method aliases (old -> new)
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

# Chain-properties field aliases (old -> new). Applies to chain_properties_hf4 / hf6 / hf9.
CHAIN_PROPS_FIELD_ALIASES = {
    "inflation_witness_percent":      "inflation_validator_percent",
    "witness_miss_penalty_percent":   "validator_miss_penalty_percent",
    "witness_miss_penalty_duration":  "validator_miss_penalty_duration",
    "witness_declaration_fee":        "validator_declaration_fee",
}

# Per-operation kwarg field aliases (old -> new), keyed by canonical new op name.
OP_FIELD_ALIASES = {
    "account_validator_vote": {"witness": "validator"},
    "validator_reward":       {"witness": "validator"},  # virtual op; reserved for future
}


def translate_kwargs(kwargs: dict, alias_map: dict, *, context: str) -> dict:
    """
    Return a copy of `kwargs` with old keys renamed to new keys per `alias_map`.

    Emits one DeprecationWarning per old key found, citing `context`.
    If both old and new are present, the new value wins and the old key
    triggers a warning.
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

    Used at response-read sites to tolerate both old (`witness_*`) and new
    (`validator_*`) field names. Call with new key first, old key second:

        pick(schedule, "current_shuffled_validators", "current_shuffled_witnesses")
    """
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            return obj[k]
        if hasattr(obj, k):
            return getattr(obj, k)
    return default
```

**Design notes:**

- Type IDs are the contract. All wire serialization uses the integer ID. The alias dicts only govern JSON string names. Binary format is untouched.
- No fifth global dict for response reads. `pick()` handles dual-name access where needed (small number of sites today).
- `translate_kwargs` is the only function with side effects (DeprecationWarning). It centralizes the warning text so every site reads the same way.

## Component changes

### `vizbase/operationids.py`

Rename five entries in the `OPS` list (positional order preserved):

```python
OPS = [
    ...,
    "validator_update",        # 6, was "witness_update"
    "account_validator_vote",  # 7, was "account_witness_vote"
    "account_validator_proxy", # 8, was "account_witness_proxy"
    ...,
    "shutdown_validator",      # 30, was "shutdown_witness"
    ...,
    "validator_reward",        # 42, was "witness_reward"
    ...,
]
```

Same renames in `VIRTUAL_OPS` (`shutdown_validator`, `validator_reward`).

After building `operations = {o: OPS.index(o) for o in OPS}`, extend the dict with old-name aliases:

```python
from .validator_compat import OP_NAME_ALIASES
for old, new in OP_NAME_ALIASES.items():
    operations[old] = operations[new]
```

This makes `operations["witness_update"] == operations["validator_update"] == 6`. Any caller doing name → ID lookup with an old name still works.

### `vizbase/operations.py`

**Rename classes (canonical = new name):**

- `Witness_update` → `Validator_update`
- `Account_witness_vote` → `Account_validator_vote`

**Wire-format field rename in `Account_validator_vote`:** OrderedDict key `"witness"` → `"validator"`.

**Kwarg dual-support in `Account_validator_vote.__init__`:**

```python
from .validator_compat import translate_kwargs, OP_FIELD_ALIASES

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
                OrderedDict([
                    ("account",   String(kwargs["account"])),
                    ("validator", String(kwargs["validator"])),
                    ("approve",   Bool(bool(kwargs["approve"]))),
                ])
            )
```

**Deprecated class aliases** (at module bottom, after the canonical classes are defined):

```python
class _DeprecatedAlias:
    """Warn once-per-process on first instantiation of a deprecated class name."""
    _warned: set[str] = set()

    @classmethod
    def make(cls, old_name: str, new_class: type) -> type:
        class _Alias(new_class):
            def __init__(self, *args, **kwargs):
                if old_name not in _DeprecatedAlias._warned:
                    warnings.warn(
                        f"{old_name} is deprecated; use {new_class.__name__} instead",
                        DeprecationWarning, stacklevel=2,
                    )
                    _DeprecatedAlias._warned.add(old_name)
                super().__init__(*args, **kwargs)
        _Alias.__name__ = old_name
        _Alias.__qualname__ = old_name
        return _Alias

Witness_update       = _DeprecatedAlias.make("Witness_update",       Validator_update)
Account_witness_vote = _DeprecatedAlias.make("Account_witness_vote", Account_validator_vote)
```

**Note:** the `Operation` dispatcher / class registry in `vizbase/operations.py` (the code that maps op-name strings → operation classes) must register both old and new names → the canonical new class. Verify during implementation; if `Operation` uses a `klass_name = op_name.title()` style lookup, the dispatch already works once `Validator_update` exists.

**No new classes added** for types 8, 30, 42. None exist in the lib today; strict rename scope.

### `vizbase/objects.py` (chain_properties)

OrderedDict keys change for the four fields:

| Old key | New key |
|---|---|
| `inflation_witness_percent` | `inflation_validator_percent` |
| `witness_miss_penalty_percent` | `validator_miss_penalty_percent` |
| `witness_miss_penalty_duration` | `validator_miss_penalty_duration` |
| `witness_declaration_fee` | `validator_declaration_fee` |

Field order is preserved (binary serialization depends on it).

At the top of the relevant `__init__`:

```python
from .validator_compat import translate_kwargs, CHAIN_PROPS_FIELD_ALIASES
kwargs = translate_kwargs(
    kwargs, CHAIN_PROPS_FIELD_ALIASES, context="chain_properties_update",
)
```

### `vizapi/consts.py`

Remove these entries:

```
get_miner_queue                 -> witness_api
get_witnesses_by_counted_vote   -> witness_api
get_active_witnesses            -> witness_api
get_witness_schedule            -> witness_api
get_witnesses                   -> witness_api
get_witness_by_account          -> witness_api
get_witnesses_by_vote           -> witness_api
get_witness_count               -> witness_api
lookup_witness_accounts         -> witness_api
debug_get_witness_schedule      -> debug_node
```

Add these:

```
get_miner_queue                  -> validator_api
get_validators_by_counted_vote   -> validator_api
get_active_validators            -> validator_api
get_validator_schedule           -> validator_api
get_validators                   -> validator_api
get_validator_by_account         -> validator_api
get_validators_by_vote           -> validator_api
get_validator_count              -> validator_api
lookup_validator_accounts        -> validator_api
debug_get_validator_schedule     -> debug_node
```

### `vizapi/noderpc.py` (dispatcher fallback)

The dispatcher lives in `Rpc.__getattr__` (lines 111–140). It resolves `name → api` via `API.get(name)` and submits a JSON-RPC `call` with `[api, name, args]` params.

Add a runtime fallback: if a method call fails with a "method not found" / "no such method" RPC error and `name` is a value in `API_METHOD_ALIASES`, retry once against the old name + `witness_api` namespace.

```python
class Rpc(GrapheneRpc):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._uses_legacy_witness_api: bool | None = None  # None = unknown

    def __getattr__(self, name):
        def method(*args, **kwargs):
            # Build the primary (new-name) query as before.
            # On NoSuchMethod-style error, if name is in API_METHOD_ALIASES.values():
            #   - look up the old name (reverse-map)
            #   - retry with api="witness_api", method=old_name
            #   - on success, set self._uses_legacy_witness_api = True
            #     and emit one DeprecationWarning per Rpc instance
            # On first success of any *new*-name call, set _uses_legacy_witness_api = False
            # If self._uses_legacy_witness_api is True, skip the new-name attempt entirely
            # (already-known legacy node).
            ...
        return method
```

**Cache scope:** per-`Rpc` instance. Once flipped to legacy, stay on legacy for the lifetime of the connection. No global state.

**Reverse map:** built once at import time from `API_METHOD_ALIASES`:

```python
_REVERSE_API_METHOD = {new: old for old, new in API_METHOD_ALIASES.items()}
```

**Error detection:** rely on the existing `vizapi.exceptions` types. The exact predicate (which exception means "method not found") needs to be verified against `vizapi/exceptions.py` and `post_process_exception` during implementation. If the current code raises `UnhandledRPCError` for everything, add a `NoSuchMethod` exception class and detect it from the message in `post_process_exception`.

**One-time warning:** emit `DeprecationWarning("Node responded on witness_api; upgrade recommended")` exactly once per `Rpc` instance, on the first legacy fallback.

### `viz/witness.py` → `viz/validator.py`

Rename the file. Classes become:

```python
# viz/validator.py
from graphenecommon.witness import Witness as GrapheneWitness
from graphenecommon.witness import Witnesses as GrapheneWitnesses

from .account import Account
from .instance import BlockchainInstance


@BlockchainInstance.inject
class Validator(GrapheneWitness):
    # TODO: switch parent to graphenecommon.validator.Validator once graphenecommon migrates.
    def define_classes(self):
        self.account_class = Account
        self.type_ids = [6, 2]


@BlockchainInstance.inject
class Validators(GrapheneWitnesses):
    def define_classes(self):
        self.account_class = Account
        self.witness_class = Validator         # graphenecommon contract; must stay
        self.validator_class = Validator       # forward-compat; harmless if upstream ignores
```

**Shim file** at `viz/witness.py`:

```python
import warnings

from .validator import Validator, Validators

warnings.warn(
    "viz.witness is deprecated; import from viz.validator instead",
    DeprecationWarning, stacklevel=2,
)

Witness = Validator
Witnesses = Validators
```

**`viz/__init__.py`** — currently has zero witness references. If a future change adds re-exports, expose both `Validator`/`Validators` (canonical) and `Witness`/`Witnesses` (deprecated alias). No action required today.

### `viz/blockchain.py`

Two changes:

1. **Docstring/example strings on lines ~141, 145, 160** reference `witness_reward` and `'witness': 'committee'`. Update example strings to `validator_reward` / `'validator': 'committee'`. No logic change.
2. **Stream `filter_by` parameter** — canonicalize the user-supplied filter through `OP_NAME_ALIASES` at the top of the stream loop:

   ```python
   from vizbase.validator_compat import OP_NAME_ALIASES
   filter_by_canonical = OP_NAME_ALIASES.get(filter_by, filter_by)
   ```

   Then match against both the canonical name and the original. This makes `filter_by="witness_reward"` match streams that emit either `witness_reward` (old node) or `validator_reward` (new node).

## Tests

### Update existing tests to new names

- **`tests/test_serialization.py`** — chain_properties dict uses new field names (`inflation_validator_percent`, `validator_miss_penalty_percent`, `validator_miss_penalty_duration`, `validator_declaration_fee`). Expected binary hex output is byte-identical (field order preserved, names not on wire); the hex assertion does not change.
- **`tests/test_blockchain.py`** — `filter_by="validator_reward"`, assertions match `validator_reward`. Note: this test currently runs against a live testnet which is pinned to a pre-migration image; see "Integration-test caveat" below.

### New file: `tests/test_validator_compat.py`

Unit-level coverage (no live node required):

1. **Operation kwarg dual-support.** `Account_validator_vote(witness="alice", account="bob", approve=True)` — succeeds, emits exactly one `DeprecationWarning` mentioning `witness`, serialized JSON has `"validator": "alice"`. Same call with `validator="alice"` emits zero warnings.
2. **Chain-properties kwarg dual-support.** Build chain_properties with old field names — warns per old field, serializes to byte-identical output as the new-name build.
3. **Op-name alias resolution.** `operations["witness_update"] == operations["validator_update"] == 6`. Repeat for all five entries in `OP_NAME_ALIASES`.
4. **Stream filter canonicalization.** `filter_by="witness_reward"` matches a synthetic stream emitting `validator_reward` ops, and vice versa.
5. **Module shim.** `from viz.witness import Witness` succeeds, emits the module-level DeprecationWarning, and `Witness is Validator` evaluates True.
6. **API dispatcher fallback.** Mock a node that errors `NoSuchMethod` on `get_active_validators` and returns `["alice"]` on `get_active_witnesses`. Assert:
   - First call: tries new name, falls back, returns `["alice"]`, emits one `DeprecationWarning("Node responded on witness_api ...")`.
   - Second call on same `Rpc` instance: skips the new-name attempt (cache flipped), single legacy call, no further warnings.
   - A fresh `Rpc` instance starts at `_uses_legacy_witness_api = None`.
7. **Deprecated class alias.** Instantiating `Witness_update(...)` emits one DeprecationWarning across the process; second instantiation emits none. `isinstance(Witness_update(...), Validator_update)` is True.

### Coverage drift check

A parametrized test loops over `OP_NAME_ALIASES.items()`, `API_METHOD_ALIASES.items()`, and `CHAIN_PROPS_FIELD_ALIASES.items()`, asserting each entry has at least one exercising test. Implemented via a simple registry-set assertion: every alias mentioned by a passing test is added to a set during test runs; the parametrized check confirms the set equals the alias dict keys. Catches drift when someone adds an alias and forgets the test.

### Integration-test caveat

Phase-A wire-format integration tests need a node that accepts both old and new names. The currently-pinned `vizblockchain/vizd:pr-85-merge` image predates the rename and likely accepts only old names. Integration tests that submit operations using new names must be marked `pytest.mark.skipif(not node_supports_validators(), reason=...)` until the testnet image is rebuilt. The unit tests in `tests/test_validator_compat.py` above don't depend on a live node.

## Out of scope (explicit non-goals — reiterated)

- New high-level wrapper methods (`validator_update`, `approve_validator`/`disapprove_validator`, `validator_proxy`). Existing `TODO` comments in `viz/viz.py` get their op names updated (witness → validator) but no implementation.
- graphenecommon parent-class migration.
- Phase C cleanup (deleting `vizbase/validator_compat.py` and its imports).
- CLI wallet command renames.
- `get_config` key renames (`CHAIN_MAX_WITNESSES` → `CHAIN_MAX_VALIDATORS` etc.) — grep confirms the lib reads zero of these keys today.
- Account-object field renames (`witnesses_voted_for` etc.) — grep confirms the lib reads zero of these today.
- Block-header field renames (`witness_signature` etc.) — grep confirms the lib does not access these directly.
- Dynamic-global-property field renames (`current_witness`) — grep confirms zero direct reads.

If post-merge code adds reads of any of the above, use the `pick()` helper from `vizbase.validator_compat`.

## Migration phases (post-merge)

This spec implements Phase A. Future phases:

- **Phase B** (after node-operator upgrades stabilize): default to new names for sending; keep old-name acceptance for reading historical data. No code change required from Phase A — already there.
- **Phase C** (cleanup, separate spec): delete `vizbase/validator_compat.py`; remove deprecated class aliases (`Witness_update`, `Account_witness_vote`); delete the `viz/witness.py` shim; remove the `witness_api` fallback path in `vizapi/noderpc.py`. One-file deletion plus a small import sweep.

## Risks & open verifications

These need confirmation during implementation, not before:

- **Op dispatch registry.** Verify how `Operation` (in `vizbase/operations.py`) resolves an op-name string to a class. The current class naming convention (`Witness_update`, capital W with lowercase after underscore) suggests a custom capitalization, not `str.title()`. Whatever the resolver uses, ensure it maps the new names in `OPS` to the renamed canonical classes (`Validator_update`, `Account_validator_vote`). If the resolver consults a flat `globals()`-style lookup, the deprecated `_DeprecatedAlias`-wrapped classes also need to be discoverable so any code path that resolves an old op name from historical data returns a working class.
- **NoSuchMethod exception.** Verify the exception type raised by the current dispatcher for an unknown method. If `UnhandledRPCError` is the only signal, add a dedicated `NoSuchMethod` exception and detect it from the message in `NodeRPC.post_process_exception`.
- **graphenecommon `Witnesses.witness_class` contract.** Confirm graphenecommon uses `self.witness_class` (not `self.validator_class`) when iterating; the `Validators` class above sets both for safety.

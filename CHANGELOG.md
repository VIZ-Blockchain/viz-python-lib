# Version history

We follow [Semantic Versions](https://semver.org/).

## Version 1.4.2

- Fix `Account.virtual_op_count()` (and `history_reverse()`) on nodes that reject
  `get_account_history` with `limit=0` (viz-cpp-node since 2026-03).
- Package metadata moved to the standard `[project]` table: SPDX license expression,
  no longer advertises untested Python 3.15.
- Releases now also create a GitHub Release with the wheel and sdist attached.

## Version 1.4.1

- Apply ruff-format across the codebase and fix mypy errors in tests (no behavior change).
- Add the missing 1.3.0 changelog entry.

## Version 1.4.0

- Refresh all runtime, development and documentation dependencies and regenerate the lockfile.
  Keep Python 3.10 support with explicit latest-compatible Sphinx/pre-commit variants.
- Add DAO request serialization without the obsolete fixed 500,000 VIZ client ceiling;
  the node checks the HF16 limit (1% of current supply). Wire bytes match the PHP library.
- Pin HF16 virtual-operation index 106 and live block-interval changes in offline tests.
- Update Ruff/mypy hooks and documentation tooling.
- Add `viz.agent`: read-side helper for HF15 agent keys (`check`, `find`, `has`, `grants`,
  `addon_matches`, ...), mirroring `agent.js` of viz-js-lib and `VIZ\Agent` of viz-php-lib.
- Route `get_deferred_claims` (`prediction_market_api`) and `get_master_history`
  (`database_api`, the node's current name of `get_owner_history`).
- HF15: `set_agent_permission` (op-id 105) serializer, byte-identical to viz-php-lib;
  read-API `get_agent_permissions`, `get_key_history`, `get_key_history_by_key`
- HF14 (Onix) Prediction Markets support:
  - Serializers for all 23 broadcastable `pm_*` operations and `set_reward_sharing`;
    `operationids.py` extended to match the node's `pm`-branch operation order
    (op-id == static_variant index)
  - `versioned_chain_properties` variants 4 (`chain_properties_hf13`) and 5
    (`chain_properties_pm`, ~47 PM governance params); variant auto-selected from
    the fields present
  - `prediction_market_api` read methods registered in the RPC API map
- Serialization verified byte-for-byte against viz-php-lib and the live testnet
  node's `get_transaction_hex` (23 PM ops + chain-props v3/v4/v5); regression
  tests added for op-ids and byte output

## Version 1.3.0

- Witness → validator rename, following the node. Operations, chain-property fields and
  `validator_api` methods use the new names on the wire:
  - `Validator_update`, `Account_validator_vote`; `viz.validator` with `Validator`/`Validators`
  - Old names (`Witness_update`, `Account_witness_vote`, `witness=` kwargs, `viz.witness`)
    still work and emit `DeprecationWarning`
  - The RPC dispatcher translates old `witness_*` method names and falls back to `witness_api`
    on nodes that predate the rename
- Add `NoSuchMethod` exception for method-not-found RPC errors
- `Blockchain.stream(filter_by=...)` accepts old and new operation names, including lists
- Bump idna 3.13 → 3.15 and aiohttp 3.13.5 → 3.14.0

## Version 1.2.0

- Drop Python 3.8 and 3.9 support (both EOL); minimum is now 3.10
- Modernize type annotations to PEP 585 / PEP 604
- Refresh dependencies; clear all open Dependabot alerts:
  aiohttp 3.10 → 3.13.5, ecdsa → 0.19.2, requests → 2.33.1, pygments → 2.20
- Bump pytest to 9.x
- Replace abandoned `m2r` with maintained `m2r2`; align dev sphinx versions
  with `docs/requirements.txt` so docs build locally
- Replace deprecated `datetime.utcnow()` in `viz/utils.py`
- Fix `__all__` in `viz/__init__.py` to reflect actual exports
- Add unit tests for `viz.utils` and extend `viz.amount` coverage
- Various tooling fixes (ruff target py310, mypy config, pre-commit, README)

## Version 1.1.0

- Refactoring and support for Python from 3.8 to 3.14
- Update dependencies
- Fix docs build

## Version 1.0.2

- Add `delegate_vesting_shares` method

## Version 1.0.1

- Support Python 3.12

## Version 1.0.0

- Add `fixed_award` and `update_account_profile` methods
- Fix memo decoding errors
- Bump dependencies versions

## Version 0.1.0

- Initial release

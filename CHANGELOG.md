# Version history

We follow [Semantic Versions](https://semver.org/).

## Unreleased

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

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
    class Obj:
        current_validator = "alice"

    assert pick(Obj(), "current_validator", "current_witness") == "alice"


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
            owner="alice",
            url="https://x",
            block_signing_key="VIZ1111111111111111111111111111111114T1Anm",
        )
    assert isinstance(op1, Validator_update)

    # Second instantiation: no warning.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        Witness_update(
            owner="alice",
            url="https://x",
            block_signing_key="VIZ1111111111111111111111111111111114T1Anm",
        )


def test_witness_update_and_validator_update_serialize_identically():
    from vizbase.operations import Validator_update, Witness_update

    kwargs = {
        "owner": "alice",
        "url": "https://alice.example",
        "block_signing_key": "VIZ1111111111111111111111111111111114T1Anm",
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        a = bytes(Validator_update(**kwargs))
        b = bytes(Witness_update(**kwargs))
    assert a == b

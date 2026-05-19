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
    **{
        k: v
        for k, v in CHAIN_PROPS_NEW.items()
        if k
        not in {
            "inflation_validator_percent",
            "validator_miss_penalty_percent",
            "validator_miss_penalty_duration",
            "validator_declaration_fee",
        }
    },
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
        "get_active_witnesses",
        "get_witness_schedule",
        "get_witnesses",
        "get_witness_by_account",
        "get_witnesses_by_vote",
        "get_witnesses_by_counted_vote",
        "get_witness_count",
        "lookup_witness_accounts",
        "debug_get_witness_schedule",
    ):
        assert old_name not in API, f"{old_name} should be removed from API map"


def test_no_such_method_exception_exists():
    from vizapi.exceptions import NoSuchMethod, RPCError

    assert issubclass(NoSuchMethod, RPCError)


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


def test_validator_class_importable():
    from graphenecommon.witness import Witness as GrapheneWitness
    from graphenecommon.witness import Witnesses as GrapheneWitnesses

    from viz.validator import Validator, Validators

    assert issubclass(Validator, GrapheneWitness)
    assert issubclass(Validators, GrapheneWitnesses)

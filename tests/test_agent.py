"""HF15 agent read-side helper and API routing (no network)."""

from types import SimpleNamespace

import pytest
from grapheneapi.exceptions import RPCError

from viz import agent
from vizapi.consts import API
from vizbase.account import PrivateKey

AGENT_KEY = str(PrivateKey().pubkey)
ACTIVE_KEY = str(PrivateKey().pubkey)
OTHER_KEY = str(PrivateKey().pubkey)

ROW = {
    "account": "alice",
    "agent_name": "bot",
    "agent_key": AGENT_KEY,
    "operations": ["transfer", "award"],
    "expiration": "1970-01-01T00:00:00",
    "addons": ["vizhub"],
    "expired": False,
}
ACCOUNT = {
    "name": "alice",
    "master_authority": {"weight_threshold": 1, "key_auths": [], "account_auths": []},
    "active_authority": {"weight_threshold": 1, "key_auths": [[ACTIVE_KEY, 1]], "account_auths": []},
    "regular_authority": {"weight_threshold": 2, "key_auths": [[OTHER_KEY, 1]], "account_auths": []},
}


def chain(rows=(ROW,), accounts=(ACCOUNT,)):
    def get_agent_permissions(account):
        if isinstance(rows, Exception):
            raise rows
        return list(rows)

    return SimpleNamespace(
        rpc=SimpleNamespace(get_agent_permissions=get_agent_permissions, get_accounts=lambda names: list(accounts))
    )


def test_new_read_methods_are_routed():
    assert API["get_deferred_claims"] == "prediction_market_api"
    assert API["get_master_history"] == "database_api"


def test_key_equals_tolerates_prefix_and_whitespace():
    assert agent.key_equals(AGENT_KEY, f" {AGENT_KEY[3:]} ")
    assert not agent.key_equals(AGENT_KEY, ACTIVE_KEY)
    assert not agent.key_equals(AGENT_KEY, None)


def test_expiry():
    assert not agent.is_expired(ROW)
    assert agent.is_expired({**ROW, "expired": True})
    # no node flag: fall back to the timestamp; epoch is perpetual
    assert not agent.is_expired({"expiration": "1970-01-01T00:00:00"})
    assert agent.is_expired({"expiration": "2020-01-01T00:00:00"})
    assert not agent.is_expired({"expiration": "2999-01-01T00:00:00"})
    assert not agent.is_expired({"expiration": "garbage"})


def test_grants_and_poisoned_row():
    assert agent.grants(ROW, "transfer")
    assert not agent.grants(ROW, "pm_place_bet")
    bad = {**ROW, "operations": ["transfer", "account_update"]}
    assert agent.poisoned(bad)
    assert not agent.grants(bad, "transfer")
    assert agent.addon_matches(ROW, "vizhub")
    assert not agent.addon_matches(ROW, "VizHub")
    assert not agent.addon_matches(bad, "vizhub")


def test_find_and_has():
    assert agent.find("alice", AGENT_KEY, chain()) == ROW
    assert agent.find("alice", OTHER_KEY, chain()) is None
    assert agent.find("alice", AGENT_KEY, chain(rows=[{**ROW, "expired": True}])) is None
    assert agent.has("alice", AGENT_KEY, blockchain_instance=chain())
    assert agent.has("alice", AGENT_KEY, "award", chain())
    assert not agent.has("alice", AGENT_KEY, "pm_place_bet", chain())


def test_node_without_hf15_reads_as_no_agents_but_transport_errors_propagate():
    assert agent.find("alice", AGENT_KEY, chain(rows=RPCError("no method"))) is None
    with pytest.raises(ConnectionError):
        agent.find("alice", AGENT_KEY, chain(rows=ConnectionError()))


def test_check():
    by_authority = agent.check("alice", ACTIVE_KEY, "transfer", chain())
    assert (by_authority["allowed"], by_authority["source"], by_authority["role"]) == (True, "authority", "active")

    by_agent = agent.check("alice", AGENT_KEY, "transfer", chain())
    assert (by_agent["allowed"], by_agent["source"], by_agent["agent"]) == (True, "agent", ROW)

    assert not agent.check("alice", AGENT_KEY, "pm_place_bet", chain())["allowed"]
    # weight 1 of threshold 2: the key alone does not satisfy the authority
    assert agent.check("alice", OTHER_KEY, None, chain()) == {
        "allowed": False,
        "source": "none",
        "role": None,
        "agent": None,
        "operation": None,
    }
    # unknown account: no authority match, agents still decide
    assert agent.check("alice", ACTIVE_KEY, None, chain(accounts=[]))["source"] == "none"

"""HF16 API compatibility and DAO wire regression (no network)."""
from types import SimpleNamespace

from viz.blockchain import Blockchain
from vizbase.objects import Operation
from vizbase.operationids import VIRTUAL_OPS


def test_slot_is_read_live_across_hf16():
    config = {"CHAIN_BLOCK_INTERVAL": 3}
    rpc = SimpleNamespace(get_config=lambda: dict(config), config=dict(config))
    chain = SimpleNamespace(blockchain=SimpleNamespace(rpc=rpc))
    assert Blockchain.get_block_interval(chain) == 3
    config["CHAIN_BLOCK_INTERVAL"] = 1
    assert Blockchain.get_block_interval(chain) == 1


def test_equivocation_is_virtual_and_append_only():
    assert Operation("validator_equivocation").id == 106
    assert "validator_equivocation" in VIRTUAL_OPS


def test_dao_above_old_ceiling_matches_php_bytes():
    op = Operation(["committee_worker_create_request", {
        "creator": "alice", "url": "x", "worker": "alice",
        "required_amount_min": "0.000 VIZ", "required_amount_max": "1000000.001 VIZ",
        "duration": 432000,
    }])
    assert bytes(op).hex() == (
        "2305616c696365017805616c69636500000000000000000356495a00000000"
        "01ca9a3b000000000356495a0000000080970600"
    )

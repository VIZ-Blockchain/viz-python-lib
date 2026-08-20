"""Serialization tests for HF14 Prediction Market (Onix) operations.

The expected hex strings are byte-for-byte identical to viz-php-lib's
build_pm_* serializers, which are themselves byte-verified against the C++
FC_REFLECT macros in the node's pm_operations.hpp. Field order/types come from
libraries/protocol/include/graphene/protocol/{operations.hpp,pm_operations.hpp}
on the `pm` branch. Do not "fix" a failing hex without re-checking the node
struct — a mismatch means a real consensus divergence.
"""

import pytest

from vizbase.objects import Operation

# Consensus op-id = index in the `operation` static_variant on the pm branch.
PM_OP_IDS = {
    "set_reward_sharing": 64,
    "pm_oracle_register": 66,
    "pm_oracle_update": 67,
    "pm_create_market": 68,
    "pm_oracle_accept_market": 69,
    "pm_place_bet": 70,
    "pm_commit_bet": 71,
    "pm_reveal_bet": 72,
    "pm_cancel_bet": 73,
    "pm_add_liquidity": 74,
    "pm_withdraw_liquidity": 75,
    "pm_resolve_market": 76,
    "pm_no_contest": 77,
    "pm_dispute_create": 78,
    "pm_dispute_vote": 79,
    "pm_dispute_resolve": 80,
    "pm_transfer_position": 81,
    "pm_lazy_deposit": 82,
    "pm_lazy_withdraw": 83,
    "pm_leverage_open": 91,
    "pm_leverage_close": 92,
    "pm_leverage_convert": 93,
    "pm_dispute_oracle_respond": 98,
    "pm_unban": 99,
    "pm_dispute_opened": 102,  # virtual, id only
    "pm_early_exit_claim_paid": 103,  # virtual, id only (F1/#300)
    "pm_lp_payout": 104,  # virtual, id only (#442/#681)
}


@pytest.mark.parametrize("name,op_id", PM_OP_IDS.items())
def test_pm_op_ids(name, op_id):
    assert Operation(name).id == op_id


# (op_name, kwargs, expected_full_op_hex) — expected == viz-php-lib build_pm_* output.
PM_CASES = [
    (
        "pm_oracle_register",
        {"owner": "alice", "insurance": "5000.000 VIZ", "fee_percent": 250, "fixed_fee": "1.000 VIZ",
             "rules_url": "http://r", "auto_accept_creator": "", "auto_accept_resolver": "", "auto_accept": True},
        "4205616c696365404b4c00000000000356495a00000000fa00e8030000000000000356495a00000000"
        "08687474703a2f2f7200000100",
    ),
    (
        "pm_oracle_update",
        {"owner": "alice", "insurance_delta": "100.000 VIZ", "fee_percent": None, "fixed_fee": "2.000 VIZ",
             "rules_url": None, "auto_accept_creator": None, "auto_accept_resolver": None, "auto_accept": False},
        "4305616c69636501a0860100000000000356495a000000000001d0070000000000000356495a"
        "00000000000000010000",
    ),
    (
        "pm_create_market",
        {"creator": "cre", "oracle": "ora", "market_type": 1, "outcomes": ["Yes", "No", "Maybe"], "url": "http://u",
             "oracle_fee_percent": 300, "oracle_fixed_fee": "1.000 VIZ", "creator_fee_percent": 100,
             "liquidity_fee_percent": 50, "liquidity": "1000.000 VIZ", "lmsr_b": 722,
             "betting_expiration": "2030-01-01T00:00:00", "result_expiration": "2030-01-02T00:00:00",
             "time_penalty_type": 1, "time_penalty_value": 86400, "penalty_curve_type": 0,
             "allow_early_resolution": True, "allow_cancellation": False, "allow_batch": False,
             "allow_instant_bet": True, "endogeneity_tier": 2, "dispute_mode": 1, "dispute_resolver": "res",
             "dispute_penalty_percent": -500, "metadata": '{"tags":["x"]}'},
        "4403637265036f7261010303596573024e6f054d6179626508687474703a2f2f752c01e803000000000000"
        "0356495a000000006400320040420f00000000000356495a00000000d20200000000000080d8db70002add70"
        "018051010000010000010201037265730cfe0e7b2274616773223a5b2278225d7d00",
    ),
    (
        "pm_oracle_accept_market",
        {"oracle": "ora", "market_id": 42, "accept": True, "oracle_fee_percent": 200, "oracle_fixed_fee": "0.500 VIZ"},
        "45036f72612a0000000000000001c800f4010000000000000356495a0000000000",
    ),
    (
        "pm_place_bet",
        {"account": "alice", "market_id": 42, "side": 1, "outcome_index": -1, "amount": "1.500 VIZ",
             "min_tokens": 0, "mode": 0},
        "4605616c6963652a0000000000000001ffffdc050000000000000356495a0000000000000000000000000000",
    ),
    (
        "pm_commit_bet",
        {"account": "alice", "market_id": 42, "commitment": "ab" * 32, "escrow_amount": "10.000 VIZ",
             "no_reveal_fee_percent": 2000},
        "4705616c6963652a00000000000000abababababababababababababababababababababababababababababab"
        "abab10270000000000000356495a00000000d00700",
    ),
    (
        "pm_reveal_bet",
        {"account": "alice", "commit_id": 9, "side": 0, "outcome_index": -1, "amount": "5.000 VIZ",
             "salt": "saltsalt", "min_tokens": 0},
        "4805616c696365090000000000000000ffff88130000000000000356495a000000000873616c7473616c74"
        "000000000000000000",
    ),
    (
        "pm_cancel_bet",
        {"account": "alice", "bet_id": 9, "min_return": 100},
        "4905616c6963650900000000000000640000000000000000",
    ),
    (
        "pm_add_liquidity",
        {"provider": "lp", "market_id": 42, "amount": "500.000 VIZ"},
        "4a026c702a0000000000000020a10700000000000356495a0000000000",
    ),
    (
        "pm_withdraw_liquidity",
        {"provider": "lp", "liquidity_id": 3, "amount": "0.000 VIZ"},
        "4b026c70030000000000000000000000000000000356495a0000000000",
    ),
    (
        "pm_resolve_market",
        {"oracle": "ora", "market_id": 42, "winning_outcome": 1, "decision_url": "http://d",
             "decision_reason": "because"},
        "4c036f72612a00000000000000010008687474703a2f2f64076265636175736500",
    ),
    (
        "pm_no_contest",
        {"oracle": "ora", "market_id": 42, "reason": "void"},
        "4d036f72612a0000000000000004766f696400",
    ),
    (
        "pm_dispute_create",
        {"disputer": "bob", "market_id": 7, "proposed_outcome": 1, "reason": "wrong"},
        "4e03626f62070000000000000001000577726f6e6700",
    ),
    (
        "pm_dispute_vote",
        {"voter": "carol", "market_id": 7, "vote_outcome": 0, "vote_percent": 5000},
        "4f056361726f6c07000000000000000000881300",
    ),
    (
        "pm_dispute_resolve",
        {"resolver": "res", "market_id": 7, "correct_outcome": 1, "penalty_amount": "50.000 VIZ",
             "ban_oracle": True, "ban_oracle_until": "2027-01-01T00:00:00", "ban_creator": False,
             "ban_creator_until": "1970-01-01T00:00:00"},
        "50037265730700000000000000010050c30000000000000356495a000000000180ec366b000000000000",
    ),
    (
        "pm_transfer_position",
        {"from": "alice", "bet_id": 9, "to": "bob", "amount": 1000, "memo": "hi"},
        "5105616c696365090000000000000003626f62e80300000000000002686900",
    ),
    (
        "pm_lazy_deposit",
        {"account": "alice", "amount": "200.000 VIZ"},
        "5205616c696365400d0300000000000356495a0000000000",
    ),
    (
        "pm_lazy_withdraw",
        {"account": "alice", "shares": 500, "emergency": True},
        "5305616c696365f4010000000000000100",
    ),
    (
        "pm_leverage_open",
        {"account": "alice", "market_id": 42, "outcome_index": 0, "collateral": "10.000 VIZ",
             "loan": "40.000 VIZ", "min_tokens": 0, "max_slippage_percent": 1000},
        "5b05616c6963652a00000000000000000010270000000000000356495a00000000409c0000000000000356495a"
        "000000000000000000000000e80300",
    ),
    (
        "pm_leverage_close",
        {"account": "alice", "position_id": 5, "min_return": 100},
        "5c05616c6963650500000000000000640000000000000000",
    ),
    (
        "pm_leverage_convert",
        {"account": "alice", "position_id": 5, "conversion_profit_cost": 300},
        "5d05616c69636505000000000000002c0100",
    ),
    (
        "pm_dispute_oracle_respond",
        {"oracle": "ora", "market_id": 7, "response": "rebuttal"},
        "62036f7261070000000000000008726562757474616c00",
    ),
    (
        "pm_unban",
        {"resolver": "res", "target": "ora", "unban_oracle": True, "unban_creator": False},
        "6303726573036f7261010000",
    ),
]


@pytest.mark.parametrize("name,kwargs,expected", PM_CASES)
def test_pm_op_serialization(name, kwargs, expected):
    assert bytes(Operation([name, kwargs])).hex() == expected

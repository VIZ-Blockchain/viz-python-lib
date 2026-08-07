"""Byte-exact serialization tests for versioned_chain_properties variants 4 and 5.

Self-contained (no live node): the expected hex is byte-for-byte identical to
viz-php-lib build_versioned_chain_properties_update($owner,$props,$version)
output, which mirrors FC_REFLECT_DERIVED(chain_properties_hf13 / _pm) in the
node. Variant index == C++ static_variant index (4 = hf13, 5 = pm/HF14 Onix).

The live round-trip check against a node lives in test_serialization.py
(test_versioned_chain_properties_update, xfail until the testnet image is
rebuilt with the validator-renamed schema).
"""

from vizbase.objects import Operation

_BASE = {
    "account_creation_fee": "1.000 VIZ",
    "maximum_block_size": 65536,
    "create_account_delegation_ratio": 10,
    "create_account_delegation_time": 2592000,
    "min_delegation": "1.000 VIZ",
    "min_curation_percent": 0,
    "max_curation_percent": 10000,
    "bandwidth_reserve_percent": 0,
    "bandwidth_reserve_below": "0.000000 SHARES",
    "flag_energy_additional_cost": 0,
    "vote_accounting_min_rshares": 100000,
    "committee_request_approve_min_percent": 1000,
    "inflation_validator_percent": 2000,
    "inflation_ratio_committee_vs_reward_fund": 5000,
    "inflation_recalc_period": 806400,
    "data_operations_cost_additional_bandwidth": 10000,
    "validator_miss_penalty_percent": 100,
    "validator_miss_penalty_duration": 86400,
    "create_invite_min_balance": "10.000 VIZ",
    "committee_create_request_fee": "100.000 VIZ",
    "create_paid_subscription_fee": "100.000 VIZ",
    "account_on_sale_fee": "10.000 VIZ",
    "subaccount_on_sale_fee": "100.000 VIZ",
    "validator_declaration_fee": "10.000 VIZ",
    "withdraw_intervals": 28,
    "distribution_epoch_length": 28800,  # hf13 → selects variant 4
}

_PM = {
    "pm_oracle_registration_fee": "10.000 VIZ",
    "pm_min_oracle_insurance": "5000.000 VIZ",
    "pm_market_creation_fee": "5.000 VIZ",
    "pm_min_liquidity": "100.000 VIZ",
    "pm_max_outcomes": 10,
    "pm_max_market_duration": 31536000,
    "pm_max_oracle_fee_percent": 500,
    "pm_oracle_accept_window_sec": 3600,
    "pm_listing_min_coverage_percent": 250,
    "pm_betting_min_coverage_percent": 150,
    "pm_default_time_penalty_percent": 50,
    "pm_max_time_penalty": 1000000,
    "pm_dispute_fee": "1000.000 VIZ",
    "pm_dispute_grace_sec": 43200,
    "pm_oracle_dispute_response_sec": 43200,
    "pm_dispute_auto_close_sec": 1209600,
    "pm_dispute_vote_period_sec": 259200,
    "pm_dispute_approve_min_percent": 1000,
    "pm_oracle_penalty_percent": 500,
    "pm_no_contest_penalty_percent": 5000,
    "pm_dispute_reward_multiplier": 30000,
    "pm_batch_epoch_blocks": 20,
    "pm_reveal_window_blocks": 200,
    "pm_commit_no_reveal_penalty_percent": 2000,
    "pm_min_batch_bet": "1.000 VIZ",
    "pm_commit_reveal_enabled": True,
    "pm_processing_cap_per_block": 200,
    "pm_lazy_pool_enabled": True,
    "pm_lazy_alloc_percent": 2000,
    "pm_lazy_max_total_alloc_percent": 7000,
    "pm_lazy_lock_sec": 604800,
    "pm_lazy_recall_step_percent": 1000,
    "pm_lazy_emergency_penalty_percent": 5000,
    "pm_lazy_min_liquidity_fee_percent": 200,
    "pm_leverage_enabled": False,
    "pm_leverage_fund_percent": 10,
    "pm_leverage_max_per_position_bp": 20,
    "pm_leverage_pool_profit_percent": 10,
    "pm_leverage_safety_margin_percent": 1,
    "pm_leverage_max_slippage_percent": 10,
    "pm_leverage_min_market_liquidity": "5000.000 VIZ",
    "pm_leverage_max_position_ratio_percent": 5,
    "pm_leverage_expiration_buffer_sec": 86400,
    "pm_leverage_m_factor_percent": 50,
    "pm_leverage_funding_rate_ppm_per_day": 50,
    "pm_conversion_profit_cost_percent": 50,
    "pm_closed_market_retention_sec": 432000,
}

_V4_HEX = (
    "2e05616c69636504e8030000000000000356495a00000000000001000a000000008d2700e8030000000000000356495a"
    "00000000000010270000000000000000000006534841524553000000a0860100e803d0078813004e0c00102700006400"
    "8051010010270000000000000356495a00000000a0860100000000000356495a00000000a0860100000000000356495a"
    "0000000010270000000000000356495a00000000a0860100000000000356495a0000000010270000000000000356495a"
    "000000001c0080700000"
)

_V5_HEX = (
    "2e05616c69636505e8030000000000000356495a00000000000001000a000000008d2700e8030000000000000356495a"
    "00000000000010270000000000000000000006534841524553000000a0860100e803d0078813004e0c00102700006400"
    "8051010010270000000000000356495a00000000a0860100000000000356495a00000000a0860100000000000356495a"
    "0000000010270000000000000356495a00000000a0860100000000000356495a0000000010270000000000000356495a"
    "000000001c008070000010270000000000000356495a00000000404b4c00000000000356495a000000008813000000000"
    "0000356495a00000000a0860100000000000356495a000000000a8033e101f401100e0000fa009600320040420f004042"
    "0f00000000000356495a00000000c0a80000c0a800000075120080f40300e803f40188133075000014000000c8000000d"
    "007e8030000000000000356495a0000000001c800000001d007581b803a0900e8038813c800000a0014000a0001000a00"
    "404b4c00000000000356495a00000000050080510100320032000000320080970600"
)


def test_versioned_chain_properties_v4():
    op = Operation(["versioned_chain_properties_update", {"owner": "alice", "props": dict(_BASE)}])
    assert bytes(op).hex() == _V4_HEX


def test_versioned_chain_properties_v5_pm():
    op = Operation(["versioned_chain_properties_update", {"owner": "alice", "props": {**_BASE, **_PM}}])
    assert bytes(op).hex() == _V5_HEX

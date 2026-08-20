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
    "set_reward_sharing",
    "stakeholder_reward",
    # HF14 Prediction Markets (Onix). Order = the single `operation` static_variant in
    # libraries/protocol/include/graphene/protocol/operations.hpp on the `pm` branch; the
    # variant index IS the consensus op-id. Virtual ops (never broadcast, no serializer) MUST
    # stay listed in-place so the broadcastable ids keep their exact offsets.
    "pm_oracle_register",          # 66
    "pm_oracle_update",            # 67
    "pm_create_market",            # 68
    "pm_oracle_accept_market",     # 69
    "pm_place_bet",                # 70
    "pm_commit_bet",               # 71
    "pm_reveal_bet",               # 72
    "pm_cancel_bet",               # 73
    "pm_add_liquidity",            # 74
    "pm_withdraw_liquidity",       # 75
    "pm_resolve_market",           # 76
    "pm_no_contest",               # 77
    "pm_dispute_create",           # 78
    "pm_dispute_vote",             # 79
    "pm_dispute_resolve",          # 80
    "pm_transfer_position",        # 81
    "pm_lazy_deposit",             # 82
    "pm_lazy_withdraw",            # 83
    "pm_batch_settle",             # 84 (virtual)
    "pm_commit_forfeit",           # 85 (virtual)
    "pm_auto_payout",              # 86 (virtual)
    "pm_dispute_finalize",         # 87 (virtual)
    "pm_dispute_auto_close",       # 88 (virtual)
    "pm_oracle_missed_penalty",    # 89 (virtual)
    "pm_lazy_recall",              # 90 (virtual)
    "pm_leverage_open",            # 91
    "pm_leverage_close",           # 92
    "pm_leverage_convert",         # 93
    "pm_leverage_liquidate",       # 94 (virtual)
    "pm_leverage_resolve",         # 95 (virtual)
    "pm_market_accepted",          # 96 (virtual)
    "pm_payout",                   # 97 (virtual)
    "pm_dispute_oracle_respond",   # 98
    "pm_unban",                    # 99
    "pm_ban_expired",              # 100 (virtual)
    "pm_market_expired",           # 101 (virtual)
    "pm_dispute_opened",           # 102 (virtual)
    "pm_early_exit_claim_paid",    # 103 (virtual)
    "pm_lp_payout",                # 104 (virtual)
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
    "stakeholder_reward",
    "pm_batch_settle",
    "pm_commit_forfeit",
    "pm_auto_payout",
    "pm_dispute_finalize",
    "pm_dispute_auto_close",
    "pm_oracle_missed_penalty",
    "pm_lazy_recall",
    "pm_leverage_liquidate",
    "pm_leverage_resolve",
    "pm_market_accepted",
    "pm_payout",
    "pm_ban_expired",
    "pm_market_expired",
    "pm_dispute_opened",
    "pm_early_exit_claim_paid",
    "pm_lp_payout",
]

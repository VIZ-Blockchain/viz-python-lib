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
    "witness_update",
    "account_witness_vote",
    "account_witness_proxy",
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
    "shutdown_witness",
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
    "witness_reward",
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
    "outbid"
]
operations = {o: OPS.index(o) for o in OPS}

# libraries/protocol/include/graphene/protocol/chain_virtual_operations.hpp
VIRTUAL_OPS = [
    "author_reward",
    "curation_reward",
    "content_reward",
    "fill_vesting_withdraw",
    "shutdown_witness",
    "hardfork",
    "content_payout_update",
    "content_benefactor_reward",
    "return_vesting_delegation",
    "committee_cancel_request",
    "committee_approve_request",
    "committee_payout_request",
    "committee_pay_request",
    "witness_reward",
    "receive_award",
    "benefactor_award",
    "paid_subscription_action",
    "cancel_paid_subscription",
    "expire_escrow_ratification",
    "bid",
    "outbid"
]

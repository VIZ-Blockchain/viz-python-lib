import struct
from collections import OrderedDict

from graphenebase.objects import GrapheneObject, isArgsThisClass
from graphenebase.objects import Operation as GrapheneOperation
from graphenebase.types import (
    Bool,
    Bytes,
    Int16,
    Map,
    Static_variant,
    String,
    Uint8,
    Uint16,
    Uint32,
    Uint64,
)

from .account import PublicKey
from .chains import DEFAULT_PREFIX, PRECISIONS
from .exceptions import AssetUnknown
from .operationids import operations
from .validator_compat import CHAIN_PROPS_FIELD_ALIASES, translate_kwargs


class Operation(GrapheneOperation):
    """Need to overwrite a few attributes to load proper operations from viz."""

    module = "vizbase.operations"
    operations = operations


class Amount:
    def __init__(self, d):
        self.amount, self.asset = d.strip().split(" ")
        self.amount = float(self.amount)

        if self.asset in PRECISIONS:
            self.precision = PRECISIONS[self.asset]
        else:
            raise AssetUnknown

    def __bytes__(self):
        # padding
        asset = self.asset + "\x00" * (7 - len(self.asset))
        amount = round(float(self.amount) * 10**self.precision)
        return struct.pack("<q", amount) + struct.pack("<b", self.precision) + bytes(asset, "ascii")

    def __str__(self):
        return "{:.{}f} {}".format(self.amount, self.precision, self.asset)


class Beneficiary(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(
                OrderedDict(
                    [
                        ("account", String(kwargs["account"])),
                        ("weight", Int16(kwargs["weight"])),
                    ]
                )
            )


class Memo(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            prefix = kwargs.pop("prefix", DEFAULT_PREFIX)

            super().__init__(
                OrderedDict(
                    [
                        ("from", PublicKey(kwargs["from"], prefix=prefix)),
                        ("to", PublicKey(kwargs["to"], prefix=prefix)),
                        ("nonce", Uint64(int(kwargs["nonce"]))),
                        ("check", Uint32(int(kwargs["check"]))),
                        ("encrypted", Bytes(kwargs["encrypted"])),
                    ]
                )
            )


class Permission(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            prefix = kwargs.pop("prefix", DEFAULT_PREFIX)

            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            kwargs["key_auths"] = sorted(
                kwargs["key_auths"],
                key=lambda x: x[0],
                reverse=False,
            )
            accountAuths = Map([[String(e[0]), Uint16(e[1])] for e in kwargs["account_auths"]])
            keyAuths = Map([[PublicKey(e[0], prefix=prefix), Uint16(e[1])] for e in kwargs["key_auths"]])
            super().__init__(
                OrderedDict(
                    [
                        ("weight_threshold", Uint32(int(kwargs["weight_threshold"]))),
                        ("account_auths", accountAuths),
                        ("key_auths", keyAuths),
                    ]
                )
            )


class ChainPropertiesVariant(Static_variant):
    def __init__(self, props):
        # Pick the versioned_chain_properties variant (index == C++ static_variant
        # index) from the fields present. HF14/Onix (chain_properties_pm) = 5,
        # HF13 (chain_properties_hf13) = 4, HF9 (chain_properties_hf9) = 3.
        if "pm_oracle_registration_fee" in props:
            version = 5
            data = ChainPropertiesPm(**props)
        elif "distribution_epoch_length" in props:
            version = 4
            data = ChainPropertiesHf13(**props)
        else:
            version = 3
            data = ChainProperties(**props)

        super().__init__(data, version)


def _chain_properties_hf9_items(kwargs):
    """Fields shared by chain_properties_hf9 (variant 3) and all later versions,
    in the exact FC_REFLECT order (binary layout is consensus-critical)."""
    return [
        # initial, version 0
        ("account_creation_fee", Amount(kwargs["account_creation_fee"])),
        ("maximum_block_size", Uint32(kwargs["maximum_block_size"])),
        ("create_account_delegation_ratio", Uint32(kwargs["create_account_delegation_ratio"])),
        ("create_account_delegation_time", Uint32(kwargs["create_account_delegation_time"])),
        ("min_delegation", Amount(kwargs["min_delegation"])),
        ("min_curation_percent", Uint16(kwargs["min_curation_percent"])),
        ("max_curation_percent", Uint16(kwargs["max_curation_percent"])),
        ("bandwidth_reserve_percent", Uint16(kwargs["bandwidth_reserve_percent"])),
        ("bandwidth_reserve_below", Amount(kwargs["bandwidth_reserve_below"])),
        ("flag_energy_additional_cost", Uint16(kwargs["flag_energy_additional_cost"])),
        ("vote_accounting_min_rshares", Uint32(kwargs["vote_accounting_min_rshares"])),
        ("committee_request_approve_min_percent", Uint16(kwargs["committee_request_approve_min_percent"])),
        # chain_properties_hf4, version 1
        ("inflation_validator_percent", Uint16(kwargs["inflation_validator_percent"])),
        ("inflation_ratio_committee_vs_reward_fund", Uint16(kwargs["inflation_ratio_committee_vs_reward_fund"])),
        ("inflation_recalc_period", Uint32(kwargs["inflation_recalc_period"])),
        # chain_properties_hf6: version 2
        ("data_operations_cost_additional_bandwidth", Uint32(kwargs["data_operations_cost_additional_bandwidth"])),
        ("validator_miss_penalty_percent", Uint16(kwargs["validator_miss_penalty_percent"])),
        ("validator_miss_penalty_duration", Uint32(kwargs["validator_miss_penalty_duration"])),
        # chain_properties_hf9: version 3
        ("create_invite_min_balance", Amount(kwargs["create_invite_min_balance"])),
        ("committee_create_request_fee", Amount(kwargs["committee_create_request_fee"])),
        ("create_paid_subscription_fee", Amount(kwargs["create_paid_subscription_fee"])),
        ("account_on_sale_fee", Amount(kwargs["account_on_sale_fee"])),
        ("subaccount_on_sale_fee", Amount(kwargs["subaccount_on_sale_fee"])),
        ("validator_declaration_fee", Amount(kwargs["validator_declaration_fee"])),
        ("withdraw_intervals", Uint16(kwargs["withdraw_intervals"])),
    ]


def _chain_properties_hf13_items(kwargs):
    """hf9 + chain_properties_hf13 (variant 4)."""
    return _chain_properties_hf9_items(kwargs) + [
        ("distribution_epoch_length", Uint32(kwargs["distribution_epoch_length"])),
    ]


def _chain_properties_pm_items(kwargs):
    """hf13 + HF14/Onix chain_properties_pm (variant 5) governance params.
    Order/types mirror FC_REFLECT_DERIVED(chain_properties_pm) exactly."""
    return _chain_properties_hf13_items(kwargs) + [
        ("pm_oracle_registration_fee", Amount(kwargs["pm_oracle_registration_fee"])),
        ("pm_min_oracle_insurance", Amount(kwargs["pm_min_oracle_insurance"])),
        ("pm_market_creation_fee", Amount(kwargs["pm_market_creation_fee"])),
        ("pm_min_liquidity", Amount(kwargs["pm_min_liquidity"])),
        ("pm_max_outcomes", Uint8(kwargs["pm_max_outcomes"])),
        ("pm_max_market_duration", Uint32(kwargs["pm_max_market_duration"])),
        ("pm_max_oracle_fee_percent", Uint16(kwargs["pm_max_oracle_fee_percent"])),
        ("pm_oracle_accept_window_sec", Uint32(kwargs["pm_oracle_accept_window_sec"])),
        ("pm_listing_min_coverage_percent", Uint16(kwargs["pm_listing_min_coverage_percent"])),
        ("pm_betting_min_coverage_percent", Uint16(kwargs["pm_betting_min_coverage_percent"])),
        ("pm_default_time_penalty_percent", Uint16(kwargs["pm_default_time_penalty_percent"])),
        ("pm_max_time_penalty", Uint32(kwargs["pm_max_time_penalty"])),
        ("pm_dispute_fee", Amount(kwargs["pm_dispute_fee"])),
        ("pm_dispute_grace_sec", Uint32(kwargs["pm_dispute_grace_sec"])),
        ("pm_oracle_dispute_response_sec", Uint32(kwargs["pm_oracle_dispute_response_sec"])),
        ("pm_dispute_auto_close_sec", Uint32(kwargs["pm_dispute_auto_close_sec"])),
        ("pm_dispute_vote_period_sec", Uint32(kwargs["pm_dispute_vote_period_sec"])),
        ("pm_dispute_approve_min_percent", Uint16(kwargs["pm_dispute_approve_min_percent"])),
        ("pm_oracle_penalty_percent", Uint16(kwargs["pm_oracle_penalty_percent"])),
        ("pm_no_contest_penalty_percent", Uint16(kwargs["pm_no_contest_penalty_percent"])),
        ("pm_dispute_reward_multiplier", Uint32(kwargs["pm_dispute_reward_multiplier"])),
        ("pm_batch_epoch_blocks", Uint32(kwargs["pm_batch_epoch_blocks"])),
        ("pm_reveal_window_blocks", Uint32(kwargs["pm_reveal_window_blocks"])),
        ("pm_commit_no_reveal_penalty_percent", Uint16(kwargs["pm_commit_no_reveal_penalty_percent"])),
        ("pm_min_batch_bet", Amount(kwargs["pm_min_batch_bet"])),
        ("pm_commit_reveal_enabled", Bool(bool(kwargs["pm_commit_reveal_enabled"]))),
        ("pm_processing_cap_per_block", Uint32(kwargs["pm_processing_cap_per_block"])),
        ("pm_lazy_pool_enabled", Bool(bool(kwargs["pm_lazy_pool_enabled"]))),
        ("pm_lazy_alloc_percent", Uint16(kwargs["pm_lazy_alloc_percent"])),
        ("pm_lazy_max_total_alloc_percent", Uint16(kwargs["pm_lazy_max_total_alloc_percent"])),
        ("pm_lazy_lock_sec", Uint32(kwargs["pm_lazy_lock_sec"])),
        ("pm_lazy_recall_step_percent", Uint16(kwargs["pm_lazy_recall_step_percent"])),
        ("pm_lazy_emergency_penalty_percent", Uint16(kwargs["pm_lazy_emergency_penalty_percent"])),
        ("pm_lazy_min_liquidity_fee_percent", Uint16(kwargs["pm_lazy_min_liquidity_fee_percent"])),
        ("pm_leverage_enabled", Bool(bool(kwargs["pm_leverage_enabled"]))),
        ("pm_leverage_fund_percent", Uint16(kwargs["pm_leverage_fund_percent"])),
        ("pm_leverage_max_per_position_bp", Uint16(kwargs["pm_leverage_max_per_position_bp"])),
        ("pm_leverage_pool_profit_percent", Uint16(kwargs["pm_leverage_pool_profit_percent"])),
        ("pm_leverage_safety_margin_percent", Uint16(kwargs["pm_leverage_safety_margin_percent"])),
        ("pm_leverage_max_slippage_percent", Uint16(kwargs["pm_leverage_max_slippage_percent"])),
        ("pm_leverage_min_market_liquidity", Amount(kwargs["pm_leverage_min_market_liquidity"])),
        ("pm_leverage_max_position_ratio_percent", Uint16(kwargs["pm_leverage_max_position_ratio_percent"])),
        ("pm_leverage_expiration_buffer_sec", Uint32(kwargs["pm_leverage_expiration_buffer_sec"])),
        ("pm_leverage_m_factor_percent", Uint16(kwargs["pm_leverage_m_factor_percent"])),
        ("pm_leverage_funding_rate_ppm_per_day", Uint32(kwargs["pm_leverage_funding_rate_ppm_per_day"])),
        ("pm_conversion_profit_cost_percent", Uint16(kwargs["pm_conversion_profit_cost_percent"])),
        ("pm_closed_market_retention_sec", Uint32(kwargs["pm_closed_market_retention_sec"])),
        ("pm_early_exit_reward_cap_percent", Uint16(kwargs["pm_early_exit_reward_cap_percent"])),
    ]


class ChainProperties(GrapheneObject):
    """versioned_chain_properties variant 3 (chain_properties_hf9)."""

    _items = staticmethod(_chain_properties_hf9_items)

    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            kwargs = translate_kwargs(
                kwargs,
                CHAIN_PROPS_FIELD_ALIASES,
                context="chain_properties_update",
            )

            super().__init__(OrderedDict(self._items(kwargs)))


class ChainPropertiesHf13(ChainProperties):
    """versioned_chain_properties variant 4 (chain_properties_hf13)."""

    _items = staticmethod(_chain_properties_hf13_items)


class ChainPropertiesPm(ChainProperties):
    """versioned_chain_properties variant 5 (chain_properties_pm, HF14/Onix)."""

    _items = staticmethod(_chain_properties_pm_items)


class Op_wrapper(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([("op", Operation(kwargs["op"]))]))

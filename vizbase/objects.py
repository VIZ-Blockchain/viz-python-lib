# -*- coding: utf-8 -*-
import struct
from collections import OrderedDict

from graphenebase.objects import GrapheneObject
from graphenebase.objects import Operation as GrapheneOperation
from graphenebase.objects import isArgsThisClass
from graphenebase.types import (
    Bytes,
    Int16,
    Map,
    Optional,
    PointInTime,
    Set,
    Signature,
    Static_variant,
    String,
    Uint8,
    Uint16,
    Uint32,
    Uint64,
    Varint32,
    Void,
    VoteId,
)

from .account import PublicKey
from .chains import DEFAULT_PREFIX, PRECISIONS
from .exceptions import AssetUnknown
from .operationids import operations


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
        amount = round(float(self.amount) * 10 ** self.precision)
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
                OrderedDict([("account", String(kwargs["account"])), ("weight", Int16(kwargs["weight"])),])
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
            kwargs["key_auths"] = sorted(kwargs["key_auths"], key=lambda x: x[0], reverse=False,)
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

        version = 3
        data = ChainProperties(**props)

        super().__init__(data, version)


class ChainProperties(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            super().__init__(
                OrderedDict(
                    [
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
                        (
                            "committee_request_approve_min_percent",
                            Uint16(kwargs["committee_request_approve_min_percent"]),
                        ),
                        # chain_properties_hf4, version 1
                        ("inflation_witness_percent", Uint16(kwargs["inflation_witness_percent"])),
                        (
                            "inflation_ratio_committee_vs_reward_fund",
                            Uint16(kwargs["inflation_ratio_committee_vs_reward_fund"]),
                        ),
                        ("inflation_recalc_period", Uint32(kwargs["inflation_recalc_period"])),
                        # chain_properties_hf6: version 2
                        (
                            "data_operations_cost_additional_bandwidth",
                            Uint32(kwargs["data_operations_cost_additional_bandwidth"]),
                        ),
                        ("witness_miss_penalty_percent", Uint16(kwargs["witness_miss_penalty_percent"])),
                        ("witness_miss_penalty_duration", Uint32(kwargs["witness_miss_penalty_duration"])),
                        # chain_properties_hf9: version 3
                        ("create_invite_min_balance", Amount(kwargs["create_invite_min_balance"])),
                        ("committee_create_request_fee", Amount(kwargs["committee_create_request_fee"])),
                        ("create_paid_subscription_fee", Amount(kwargs["create_paid_subscription_fee"])),
                        ("account_on_sale_fee", Amount(kwargs["account_on_sale_fee"])),
                        ("subaccount_on_sale_fee", Amount(kwargs["subaccount_on_sale_fee"])),
                        ("witness_declaration_fee", Amount(kwargs["witness_declaration_fee"])),
                        ("withdraw_intervals", Uint16(kwargs["withdraw_intervals"])),
                    ]
                )
            )


class Op_wrapper(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([("op", Operation(kwargs["op"]))]))

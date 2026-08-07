import json
import struct
import warnings
from collections import OrderedDict

from graphenebase.types import (
    Array,
    Bool,
    Int16,
    Int64,
    Optional,
    PointInTime,
    Sha256,
    String,
    Uint8,
    Uint16,
    Uint32,
    Uint64,
)

from .account import PublicKey
from .chains import DEFAULT_PREFIX
from .objects import (
    Amount,
    Beneficiary,
    ChainPropertiesVariant,
    GrapheneObject,
    Op_wrapper,
    Permission,
    isArgsThisClass,
)
from .validator_compat import OP_FIELD_ALIASES, translate_kwargs

# You can find operations definitions in
# libraries/protocol/include/graphene/protocol/chain_operations.hpp


class Int8:
    """Signed 8-bit integer. graphenebase.types has Uint8/Int16 but no Int8;
    PM `side` fields are int8_t."""

    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return struct.pack("<b", int(self.data))

    def __str__(self):
        return f"{self.data}"


class _DeprecatedAlias:
    """Warn once-per-process on first instantiation of a deprecated class name."""

    _warned: set[str] = set()

    @classmethod
    def make(cls, old_name: str, new_class: type) -> type:
        warned = cls._warned

        class _Alias(new_class):
            def __init__(self, *args, **kwargs):
                if old_name not in warned:
                    warnings.warn(
                        f"{old_name} is deprecated; use {new_class.__name__} instead",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                    warned.add(old_name)
                super().__init__(*args, **kwargs)

        _Alias.__name__ = old_name
        _Alias.__qualname__ = old_name
        return _Alias


class Account_create(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", DEFAULT_PREFIX)

            meta = ""
            if "json_metadata" in kwargs and kwargs["json_metadata"]:
                if isinstance(kwargs["json_metadata"], dict):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]
            super().__init__(
                OrderedDict(
                    [
                        ("fee", Amount(kwargs["fee"])),
                        ("delegation", Amount(kwargs["delegation"])),
                        ("creator", String(kwargs["creator"])),
                        ("new_account_name", String(kwargs["new_account_name"])),
                        ("master", Permission(kwargs["master"], prefix=prefix)),
                        ("active", Permission(kwargs["active"], prefix=prefix)),
                        ("regular", Permission(kwargs["regular"], prefix=prefix)),
                        ("memo_key", PublicKey(kwargs["memo_key"], prefix=prefix)),
                        ("json_metadata", String(meta)),
                        ("referrer", String(kwargs["referrer"])),
                        ("extensions", Array([])),
                    ]
                )
            )


class Account_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", DEFAULT_PREFIX)

            meta = ""
            if "json_metadata" in kwargs and kwargs["json_metadata"]:
                if isinstance(kwargs["json_metadata"], dict):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]

            master = Permission(kwargs["master"], prefix=prefix) if "master" in kwargs else None
            active = Permission(kwargs["active"], prefix=prefix) if "active" in kwargs else None
            regular = Permission(kwargs["regular"], prefix=prefix) if "regular" in kwargs else None

            super().__init__(
                OrderedDict(
                    [
                        ("account", String(kwargs["account"])),
                        ("master", Optional(master)),
                        ("active", Optional(active)),
                        ("regular", Optional(regular)),
                        ("memo_key", PublicKey(kwargs["memo_key"], prefix=prefix)),
                        ("json_metadata", String(meta)),
                    ]
                )
            )


class Account_metadata(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            meta = ""
            if kwargs.get("json_metadata"):
                if isinstance(kwargs["json_metadata"], dict):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]

            super().__init__(
                OrderedDict(
                    [
                        ("account", String(kwargs["account"])),
                        ("json_metadata", String(meta)),
                    ]
                )
            )


class Award(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "custom_sequence" not in kwargs:
                kwargs["custom_sequence"] = 0

            super().__init__(
                OrderedDict(
                    [
                        ("initiator", String(kwargs["initiator"])),
                        ("receiver", String(kwargs["receiver"])),
                        ("energy", Uint16(kwargs["energy"])),
                        ("custom_sequence", Uint64(kwargs["custom_sequence"])),
                        ("memo", String(kwargs["memo"])),
                        (
                            "beneficiaries",
                            Array([Beneficiary(o) for o in kwargs["beneficiaries"]]),
                        ),
                    ]
                )
            )


class Fixed_award(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "custom_sequence" not in kwargs:
                kwargs["custom_sequence"] = 0

            super().__init__(
                OrderedDict(
                    [
                        ("initiator", String(kwargs["initiator"])),
                        ("receiver", String(kwargs["receiver"])),
                        ("reward_amount", Amount(kwargs["reward_amount"])),
                        ("max_energy", Uint16(kwargs["max_energy"])),
                        ("custom_sequence", Uint64(kwargs["custom_sequence"])),
                        ("memo", String(kwargs["memo"])),
                        (
                            "beneficiaries",
                            Array([Beneficiary(o) for o in kwargs["beneficiaries"]]),
                        ),
                    ]
                )
            )


class Transfer(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "memo" not in kwargs:
                kwargs["memo"] = ""
            super().__init__(
                OrderedDict(
                    [
                        ("from", String(kwargs["from"])),
                        ("to", String(kwargs["to"])),
                        ("amount", Amount(kwargs["amount"])),
                        ("memo", String(kwargs["memo"])),
                    ]
                )
            )


class Transfer_to_vesting(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(
                OrderedDict(
                    [
                        ("from", String(kwargs["from"])),
                        ("to", String(kwargs["to"])),
                        ("amount", Amount(kwargs["amount"])),
                    ]
                )
            )


class Withdraw_vesting(GrapheneObject):
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
                        ("vesting_shares", Amount(kwargs["vesting_shares"])),
                    ]
                )
            )


class Delegate_vesting_shares(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(
                OrderedDict(
                    [
                        ("delegator", String(kwargs["delegator"])),
                        ("delegatee", String(kwargs["delegatee"])),
                        ("vesting_shares", Amount(kwargs["vesting_shares"])),
                    ]
                )
            )


class Set_withdraw_vesting_route(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(
                OrderedDict(
                    [
                        ("from_account", String(kwargs["from_account"])),
                        ("to_account", String(kwargs["to_account"])),
                        ("percent", Uint16(kwargs["percent"])),
                        ("auto_vest", Bool(kwargs["auto_vest"])),
                    ]
                )
            )


class Validator_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", DEFAULT_PREFIX)

            if not kwargs["block_signing_key"]:
                kwargs["block_signing_key"] = f"{prefix}1111111111111111111111111111111114T1Anm"
            super().__init__(
                OrderedDict(
                    [
                        ("owner", String(kwargs["owner"])),
                        ("url", String(kwargs["url"])),
                        ("block_signing_key", PublicKey(kwargs["block_signing_key"], prefix=prefix)),
                    ]
                )
            )


class Versioned_chain_properties_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            props = kwargs.get("props")

            # A hack to extract properties at the second op processing in transactionbuilder
            if props and isinstance(props, list):
                props = props[1]

            if props and isinstance(props, dict):
                props = ChainPropertiesVariant(props)

            super().__init__(OrderedDict([("owner", String(kwargs["owner"])), ("props", props)]))


class Account_validator_vote(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            kwargs = translate_kwargs(
                kwargs,
                OP_FIELD_ALIASES["account_validator_vote"],
                context="Account_validator_vote",
            )
            super().__init__(
                OrderedDict(
                    [
                        ("account", String(kwargs["account"])),
                        ("validator", String(kwargs["validator"])),
                        ("approve", Bool(bool(kwargs["approve"]))),
                    ]
                )
            )


class Proposal_create(GrapheneObject):
    """See libraries/protocol/include/graphene/protocol/proposal_operations.hpp."""

    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "review_period_time" in kwargs:
                review = Optional(PointInTime(kwargs["review_period_time"]))
            else:
                review = Optional(None)
            super().__init__(
                OrderedDict(
                    [
                        ("author", String(kwargs["author"])),
                        ("title", String(kwargs["title"])),
                        ("memo", String(kwargs.get("memo", ""))),
                        ("expiration_time", PointInTime(kwargs["expiration_time"])),
                        ("proposed_operations", Array([Op_wrapper(o) for o in kwargs["proposed_operations"]])),
                        ("review_period_time", review),
                        ("extensions", Array(kwargs.get("extensions") or [])),
                    ]
                )
            )


class Proposal_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", DEFAULT_PREFIX)

            active_approvals_to_add = [String(str(x)) for x in kwargs.get("active_approvals_to_add") or []]
            active_approvals_to_remove = [String(str(x)) for x in kwargs.get("active_approvals_to_remove") or []]
            master_approvals_to_add = [String(str(x)) for x in kwargs.get("master_approvals_to_add") or []]
            master_approvals_to_remove = [String(str(x)) for x in kwargs.get("master_approvals_to_remove") or []]
            regular_approvals_to_add = [String(str(x)) for x in kwargs.get("regular_approvals_to_add") or []]
            regular_approvals_to_remove = [String(str(x)) for x in kwargs.get("regular_approvals_to_remove") or []]
            key_approvals_to_add = [PublicKey(x, prefix=prefix) for x in kwargs.get("key_approvals_to_add") or []]
            key_approvals_to_remove = [PublicKey(x, prefix=prefix) for x in kwargs.get("key_approvals_to_remove") or []]

            super().__init__(
                OrderedDict(
                    [
                        ("author", String(kwargs["author"])),
                        ("title", String(kwargs["title"])),
                        ("active_approvals_to_add", Array(active_approvals_to_add)),
                        (
                            "active_approvals_to_remove",
                            Array(active_approvals_to_remove),
                        ),
                        ("master_approvals_to_add", Array(master_approvals_to_add)),
                        ("master_approvals_to_remove", Array(master_approvals_to_remove)),
                        ("regular_approvals_to_add", Array(regular_approvals_to_add)),
                        (
                            "regular_approvals_to_remove",
                            Array(regular_approvals_to_remove),
                        ),
                        ("key_approvals_to_add", Array(key_approvals_to_add)),
                        ("key_approvals_to_remove", Array(key_approvals_to_remove)),
                        ("extensions", Array(kwargs.get("extensions") or [])),
                    ]
                )
            )


class Proposal_delete(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(
                OrderedDict(
                    [
                        ("author", String(kwargs["author"])),
                        ("title", String(kwargs["title"])),
                        ("requester", String(kwargs["requester"])),
                        ("extensions", Array(kwargs.get("extensions") or [])),
                    ]
                )
            )


class Custom(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "json" in kwargs and kwargs["json"]:
                if isinstance(kwargs["json"], dict) or isinstance(kwargs["json"], list):
                    js = json.dumps(kwargs["json"])
                else:
                    js = kwargs["json"]

            if len(kwargs["id"]) > 32:
                raise ValueError("'id' is too long")

            super().__init__(
                OrderedDict(
                    [
                        (
                            "required_active_auths",
                            Array([String(o) for o in kwargs["required_active_auths"]]),
                        ),
                        (
                            "required_regular_auths",
                            Array([String(o) for o in kwargs["required_regular_auths"]]),
                        ),
                        ("id", String(kwargs["id"])),
                        ("json", String(js)),
                    ]
                )
            )


# ---------------------------------------------------------------------------
# HF14 Prediction Markets (Onix) operations.
#
# Field order and types are taken 1:1 from the FC_REFLECT macros in
# libraries/protocol/include/graphene/protocol/pm_operations.hpp on the node
# `pm` branch. Type mapping: account_name_type/string -> String, asset -> Amount,
# uint8_t -> Uint8, int8_t -> Int8, int16_t -> Int16, uint16_t -> Uint16,
# uint32_t -> Uint32, share_type/pm_object_id_type(int64) -> Int64, bool -> Bool,
# time_point_sec -> PointInTime, fc::sha256 -> Sha256, vector<string> -> Array,
# optional<T> -> Optional, extensions_type -> Array([]) (empty set).
# ---------------------------------------------------------------------------


def _prep_kwargs(self, args, kwargs):
    """Shared preamble mirroring the other ops: copy-construct or unwrap a single dict."""
    if isArgsThisClass(self, args):
        return None
    if len(args) == 1 and len(kwargs) == 0:
        kwargs = args[0]
    return kwargs


class Set_reward_sharing(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("owner", String(kw["owner"])),
                    ("sharing_rate", Uint16(kw["sharing_rate"])),
                ]
            )
        )


class Pm_oracle_register(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("owner", String(kw["owner"])),
                    ("insurance", Amount(kw["insurance"])),
                    ("fee_percent", Uint16(kw.get("fee_percent", 0))),
                    ("fixed_fee", Amount(kw["fixed_fee"])),
                    ("rules_url", String(kw.get("rules_url", ""))),
                    ("auto_accept_creator", String(kw.get("auto_accept_creator", ""))),
                    ("auto_accept_resolver", String(kw.get("auto_accept_resolver", ""))),
                    ("auto_accept", Bool(bool(kw.get("auto_accept", False)))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_oracle_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        insurance_delta = Amount(kw["insurance_delta"]) if kw.get("insurance_delta") else None
        fee_percent = Uint16(kw["fee_percent"]) if kw.get("fee_percent") is not None else None
        fixed_fee = Amount(kw["fixed_fee"]) if kw.get("fixed_fee") else None
        rules_url = String(kw["rules_url"]) if kw.get("rules_url") is not None else None
        aac = String(kw["auto_accept_creator"]) if kw.get("auto_accept_creator") is not None else None
        aar = String(kw["auto_accept_resolver"]) if kw.get("auto_accept_resolver") is not None else None
        auto_accept = Bool(bool(kw["auto_accept"])) if kw.get("auto_accept") is not None else None
        super().__init__(
            OrderedDict(
                [
                    ("owner", String(kw["owner"])),
                    ("insurance_delta", Optional(insurance_delta)),
                    ("fee_percent", Optional(fee_percent)),
                    ("fixed_fee", Optional(fixed_fee)),
                    ("rules_url", Optional(rules_url)),
                    ("auto_accept_creator", Optional(aac)),
                    ("auto_accept_resolver", Optional(aar)),
                    ("auto_accept", Optional(auto_accept)),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_create_market(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        meta = kw.get("metadata", "")
        if isinstance(meta, (dict, list)):
            meta = json.dumps(meta)
        super().__init__(
            OrderedDict(
                [
                    ("creator", String(kw["creator"])),
                    ("oracle", String(kw["oracle"])),
                    ("market_type", Uint8(kw.get("market_type", 0))),
                    ("outcomes", Array([String(o) for o in kw["outcomes"]])),
                    ("url", String(kw.get("url", ""))),
                    ("oracle_fee_percent", Uint16(kw.get("oracle_fee_percent", 0))),
                    ("oracle_fixed_fee", Amount(kw["oracle_fixed_fee"])),
                    ("creator_fee_percent", Uint16(kw.get("creator_fee_percent", 0))),
                    ("liquidity_fee_percent", Uint16(kw.get("liquidity_fee_percent", 0))),
                    ("liquidity", Amount(kw["liquidity"])),
                    ("lmsr_b", Int64(kw.get("lmsr_b", 0))),
                    ("betting_expiration", PointInTime(kw["betting_expiration"])),
                    ("result_expiration", PointInTime(kw["result_expiration"])),
                    ("time_penalty_type", Uint8(kw.get("time_penalty_type", 0))),
                    ("time_penalty_value", Uint32(kw.get("time_penalty_value", 0))),
                    ("penalty_curve_type", Uint8(kw.get("penalty_curve_type", 0))),
                    ("allow_early_resolution", Bool(bool(kw.get("allow_early_resolution", False)))),
                    ("allow_cancellation", Bool(bool(kw.get("allow_cancellation", False)))),
                    ("allow_batch", Bool(bool(kw.get("allow_batch", False)))),
                    ("allow_instant_bet", Bool(bool(kw.get("allow_instant_bet", True)))),
                    ("endogeneity_tier", Uint8(kw.get("endogeneity_tier", 2))),
                    ("dispute_mode", Uint8(kw.get("dispute_mode", 0))),
                    ("dispute_resolver", String(kw.get("dispute_resolver", ""))),
                    ("dispute_penalty_percent", Int16(kw.get("dispute_penalty_percent", 0))),
                    ("metadata", String(meta)),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_oracle_accept_market(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("oracle", String(kw["oracle"])),
                    ("market_id", Int64(kw.get("market_id", 0))),
                    ("accept", Bool(bool(kw.get("accept", True)))),
                    ("oracle_fee_percent", Uint16(kw.get("oracle_fee_percent", 0))),
                    ("oracle_fixed_fee", Amount(kw["oracle_fixed_fee"])),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_place_bet(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("account", String(kw["account"])),
                    ("market_id", Int64(kw.get("market_id", 0))),
                    ("side", Int8(kw.get("side", -1))),
                    ("outcome_index", Int16(kw.get("outcome_index", -1))),
                    ("amount", Amount(kw["amount"])),
                    ("min_tokens", Int64(kw.get("min_tokens", 0))),
                    ("mode", Uint8(kw.get("mode", 0))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_commit_bet(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("account", String(kw["account"])),
                    ("market_id", Int64(kw.get("market_id", 0))),
                    ("commitment", Sha256(kw["commitment"])),
                    ("escrow_amount", Amount(kw["escrow_amount"])),
                    ("no_reveal_fee_percent", Uint16(kw.get("no_reveal_fee_percent", 0))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_reveal_bet(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("account", String(kw["account"])),
                    ("commit_id", Int64(kw.get("commit_id", 0))),
                    ("side", Int8(kw.get("side", -1))),
                    ("outcome_index", Int16(kw.get("outcome_index", -1))),
                    ("amount", Amount(kw["amount"])),
                    ("salt", String(kw.get("salt", ""))),
                    ("min_tokens", Int64(kw.get("min_tokens", 0))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_cancel_bet(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("account", String(kw["account"])),
                    ("bet_id", Int64(kw.get("bet_id", 0))),
                    ("min_return", Int64(kw.get("min_return", 0))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_add_liquidity(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("provider", String(kw["provider"])),
                    ("market_id", Int64(kw.get("market_id", 0))),
                    ("amount", Amount(kw["amount"])),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_withdraw_liquidity(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("provider", String(kw["provider"])),
                    ("liquidity_id", Int64(kw.get("liquidity_id", 0))),
                    ("amount", Amount(kw["amount"])),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_resolve_market(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("oracle", String(kw["oracle"])),
                    ("market_id", Int64(kw.get("market_id", 0))),
                    ("winning_outcome", Int16(kw.get("winning_outcome", -1))),
                    ("decision_url", String(kw.get("decision_url", ""))),
                    ("decision_reason", String(kw.get("decision_reason", ""))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_no_contest(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("oracle", String(kw["oracle"])),
                    ("market_id", Int64(kw.get("market_id", 0))),
                    ("reason", String(kw.get("reason", ""))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_dispute_create(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("disputer", String(kw["disputer"])),
                    ("market_id", Int64(kw.get("market_id", 0))),
                    ("proposed_outcome", Int16(kw.get("proposed_outcome", -1))),
                    ("reason", String(kw.get("reason", ""))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_dispute_vote(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("voter", String(kw["voter"])),
                    ("market_id", Int64(kw.get("market_id", 0))),
                    ("vote_outcome", Int16(kw.get("vote_outcome", -1))),
                    ("vote_percent", Int16(kw.get("vote_percent", 0))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_dispute_resolve(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("resolver", String(kw["resolver"])),
                    ("market_id", Int64(kw.get("market_id", 0))),
                    ("correct_outcome", Int16(kw.get("correct_outcome", -1))),
                    ("penalty_amount", Amount(kw["penalty_amount"])),
                    ("ban_oracle", Bool(bool(kw.get("ban_oracle", False)))),
                    ("ban_oracle_until", PointInTime(kw["ban_oracle_until"])),
                    ("ban_creator", Bool(bool(kw.get("ban_creator", False)))),
                    ("ban_creator_until", PointInTime(kw["ban_creator_until"])),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_transfer_position(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("from", String(kw["from"])),
                    ("bet_id", Int64(kw.get("bet_id", 0))),
                    ("to", String(kw["to"])),
                    ("amount", Int64(kw.get("amount", 0))),
                    ("memo", String(kw.get("memo", ""))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_lazy_deposit(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("account", String(kw["account"])),
                    ("amount", Amount(kw["amount"])),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_lazy_withdraw(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("account", String(kw["account"])),
                    ("shares", Int64(kw.get("shares", 0))),
                    ("emergency", Bool(bool(kw.get("emergency", False)))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_leverage_open(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("account", String(kw["account"])),
                    ("market_id", Int64(kw.get("market_id", 0))),
                    ("outcome_index", Int16(kw.get("outcome_index", 0))),
                    ("collateral", Amount(kw["collateral"])),
                    ("loan", Amount(kw["loan"])),
                    ("min_tokens", Int64(kw.get("min_tokens", 0))),
                    ("max_slippage_percent", Uint16(kw.get("max_slippage_percent", 0))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_leverage_close(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("account", String(kw["account"])),
                    ("position_id", Int64(kw.get("position_id", 0))),
                    ("min_return", Int64(kw.get("min_return", 0))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_leverage_convert(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("account", String(kw["account"])),
                    ("position_id", Int64(kw.get("position_id", 0))),
                    ("conversion_profit_cost", Uint16(kw.get("conversion_profit_cost", 0))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_dispute_oracle_respond(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("oracle", String(kw["oracle"])),
                    ("market_id", Int64(kw.get("market_id", 0))),
                    ("response", String(kw.get("response", ""))),
                    ("extensions", Array([])),
                ]
            )
        )


class Pm_unban(GrapheneObject):
    def __init__(self, *args, **kwargs):
        kw = _prep_kwargs(self, args, kwargs)
        if kw is None:
            self.data = args[0].data
            return
        super().__init__(
            OrderedDict(
                [
                    ("resolver", String(kw["resolver"])),
                    ("target", String(kw["target"])),
                    ("unban_oracle", Bool(bool(kw.get("unban_oracle", False)))),
                    ("unban_creator", Bool(bool(kw.get("unban_creator", False)))),
                    ("extensions", Array([])),
                ]
            )
        )


# Deprecated witness-named aliases. Subclasses that warn once per process
# on first instantiation. Remove during Phase C cleanup.
Witness_update = _DeprecatedAlias.make("Witness_update", Validator_update)
Account_witness_vote = _DeprecatedAlias.make("Account_witness_vote", Account_validator_vote)

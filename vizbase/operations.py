# -*- coding: utf-8 -*-
import json

from collections import OrderedDict
from binascii import hexlify, unhexlify

from graphenebase.types import (
    Array,
    Bool,
    Bytes,
    Fixed_array,
    Id,
    Int16,
    Int64,
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
    Ripemd160,
    Sha1,
    Sha256,
)

from .account import PublicKey
from .objects import (
    Amount,
    Asset,
    Beneficiary,
    GrapheneObject,
    Memo,
    Operation,
    Permission,
    isArgsThisClass,
)
from .operationids import operations
from .chains import DEFAULT_PREFIX


class_idmap = {}
class_namemap = {}

# You can find operations definitions in
# libraries/protocol/include/graphene/protocol/chain_operations.hpp


def fill_classmaps():
    for name, ind in operations.items():
        classname = name[0:1].upper() + name[1:]
        class_namemap[classname] = ind
        try:
            class_idmap[ind] = globals()[classname]
        except Exception:
            continue


def getOperationClassForId(op_id):
    """ Convert an operation id into the corresponding class
    """
    return class_idmap[op_id] if op_id in class_idmap else None


def getOperationIdForClass(name):
    """ Convert an operation classname into the corresponding id
    """
    return class_namemap[name] if name in class_namemap else None


def getOperationNameForId(i):
    """ Convert an operation id into the corresponding string
    """
    for key in operations:
        if int(operations[key]) is int(i):
            return key
    return "Unknown Operation ID %d" % i


class Account_create_with_delegation(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", DEFAULT_PREFIX)

            assert (
                len(kwargs["new_account_name"]) <= 16
            ), "Account name must be at most 16 chars long"

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

            master = (
                Permission(kwargs["master"], prefix=prefix)
                if "master" in kwargs
                else None
            )
            active = (
                Permission(kwargs["active"], prefix=prefix)
                if "active" in kwargs
                else None
            )
            regular = (
                Permission(kwargs["regular"], prefix=prefix)
                if "regular" in kwargs
                else None
            )

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
                        ("percent", Uint16((kwargs["percent"]))),
                        ("auto_vest", Bool(kwargs["auto_vest"])),
                    ]
                )
            )


class Witness_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", DEFAULT_PREFIX)

            if not kwargs["block_signing_key"]:
                kwargs[
                    "block_signing_key"
                ] = "{}1111111111111111111111111111111114T1Anm".format(prefix)
            super().__init__(
                OrderedDict(
                    [
                        ("master", String(kwargs["master"])),
                        ("url", String(kwargs["url"])),
                        (
                            "block_signing_key",
                            PublicKey(kwargs["block_signing_key"], prefix=prefix),
                        ),
                        ("props", ChainProperties(kwargs["props"])),
                        ("fee", Amount(kwargs["fee"])),
                    ]
                )
            )


# TODO: VersionedChainPropertiesUpdate
class Chain_properties_update(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            props = kwargs.get("props")

            # A hack to extract properties at the second op processing in transactionbuilder
            if props and type(props) == list:
                props = props[1]

            if props and type(props) == dict:
                type_id = 0
                if "min_delegation" in props:
                    type_id = 1
                if "auction_window_size" in props:
                    type_id = 2

                obj = [type_id, {"props": props}]
                props = Props(obj)

            super().__init__(
                OrderedDict([("master", String(kwargs["master"])), ("props", props)])
            )


class Account_witness_vote(GrapheneObject):
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
                        ("witness", String(kwargs["witness"])),
                        ("approve", Bool(bool(kwargs["approve"]))),
                    ]
                )
            )


# TODO: make sure this is working
class Proposal_create(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            assert kwargs["proposed_operations"], "proposed_operations cannot be empty!"

            if isinstance(kwargs["proposed_operations"][0], GrapheneObject):
                proposed_operations = [
                    OperationWrapper(Operation(op))
                    for op in kwargs["proposed_operations"]
                ]
            else:
                proposed_operations = [
                    OperationWrapper(Operation(op["op"]))
                    for op in kwargs["proposed_operations"]
                ]

            review_period_time = (
                PointInTime(kwargs["review_period_time"])
                if kwargs.get("review_period_time")
                else None
            )

            super().__init__(
                OrderedDict(
                    [
                        ("author", String(kwargs["author"])),
                        ("title", String(kwargs["title"])),
                        ("memo", String(kwargs.get("memo", ""))),
                        ("expiration_time", PointInTime(kwargs["expiration_time"])),
                        ("proposed_operations", Array(proposed_operations)),
                        ("review_period_time", Optional(review_period_time)),
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

            active_approvals_to_add = [
                String(str(x)) for x in kwargs.get("active_approvals_to_add") or []
            ]
            active_approvals_to_remove = [
                String(str(x)) for x in kwargs.get("active_approvals_to_remove") or []
            ]
            master_approvals_to_add = [
                String(str(x)) for x in kwargs.get("master_approvals_to_add") or []
            ]
            master_approvals_to_remove = [
                String(str(x)) for x in kwargs.get("master_approvals_to_remove") or []
            ]
            regular_approvals_to_add = [
                String(str(x)) for x in kwargs.get("regular_approvals_to_add") or []
            ]
            regular_approvals_to_remove = [
                String(str(x)) for x in kwargs.get("regular_approvals_to_remove") or []
            ]
            key_approvals_to_add = [
                String(str(x)) for x in kwargs.get("key_approvals_to_add") or []
            ]
            key_approvals_to_remove = [
                String(str(x)) for x in kwargs.get("key_approvals_to_remove") or []
            ]

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
                raise Exception("'id' too long")

            super().__init__(
                OrderedDict(
                    [
                        (
                            "required_auths",
                            Array([String(o) for o in kwargs["required_auths"]]),
                        ),
                        (
                            "required_regular_auths",
                            Array(
                                [String(o) for o in kwargs["required_regular_auths"]]
                            ),
                        ),
                        ("id", String(kwargs["id"])),
                        ("json", String(js)),
                    ]
                )
            )


# TODO: versioned_chain_properties op


fill_classmaps()

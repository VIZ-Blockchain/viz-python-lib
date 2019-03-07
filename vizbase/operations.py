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
    GrapheneObject,
    Memo,
    Operation,
    Permission,
    isArgsThisClass,
)
from .operationids import operations


default_prefix = "VIZ"
class_idmap = {}
class_namemap = {}


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


class AccountCreateWithDelegation(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", default_prefix)

            assert len(kwargs["new_account_name"]) <= 16, "Account name must be at most 16 chars long"

            meta = ""
            if "json_metadata" in kwargs and kwargs["json_metadata"]:
                if isinstance(kwargs["json_metadata"], dict):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]
            super().__init__(OrderedDict([
                ('fee', Amount(kwargs["fee"])),
                ('delegation', Amount(kwargs["delegation"])),
                ('creator', String(kwargs["creator"])),
                ('new_account_name', String(kwargs["new_account_name"])),
                ('owner', Permission(kwargs["owner"], prefix=prefix)),
                ('active', Permission(kwargs["active"], prefix=prefix)),
                ('posting', Permission(kwargs["posting"], prefix=prefix)),
                ('memo_key', PublicKey(kwargs["memo_key"], prefix=prefix)),
                ('json_metadata', String(meta)),
                ('extensions', Array([])),
            ]))


class AccountUpdate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", default_prefix)

            meta = ""
            if "json_metadata" in kwargs and kwargs["json_metadata"]:
                if isinstance(kwargs["json_metadata"], dict):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]

            owner = Permission(kwargs["owner"], prefix=prefix) if "owner" in kwargs else None
            active = Permission(kwargs["active"], prefix=prefix) if "active" in kwargs else None
            posting = Permission(kwargs["posting"], prefix=prefix) if "posting" in kwargs else None

            super().__init__(OrderedDict([
                ('account', String(kwargs["account"])),
                ('owner', Optional(owner)),
                ('active', Optional(active)),
                ('posting', Optional(posting)),
                ('memo_key', PublicKey(kwargs["memo_key"], prefix=prefix)),
                ('json_metadata', String(meta)),
            ]))

class AccountMetadata(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            meta = ""
            if kwargs.get('json_metadata'):
                if isinstance(kwargs["json_metadata"], dict):
                    meta = json.dumps(kwargs["json_metadata"])
                else:
                    meta = kwargs["json_metadata"]

            super().__init__(OrderedDict([
                ('account', String(kwargs["account"])),
                ('json_metadata', String(meta)),
            ]))


class Transfer(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if "memo" not in kwargs:
                kwargs["memo"] = ""
            super().__init__(OrderedDict([
                ('from', String(kwargs["from"])),
                ('to', String(kwargs["to"])),
                ('amount', Amount(kwargs["amount"])),
                ('memo', String(kwargs["memo"])),
            ]))


class TransferToVesting(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('from', String(kwargs["from"])),
                ('to', String(kwargs["to"])),
                ('amount', Amount(kwargs["amount"])),
            ]))


class WithdrawVesting(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('account', String(kwargs["account"])),
                ('vesting_shares', Amount(kwargs["vesting_shares"])),
            ]))


class DelegateVestingShares(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('delegator', String(kwargs["delegator"])),
                ('delegatee', String(kwargs["delegatee"])),
                ('vesting_shares', Amount(kwargs["vesting_shares"])),
            ]))

class SetWithdrawVestingRoute(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('from_account', String(kwargs["from_account"])),
                ('to_account', String(kwargs["to_account"])),
                ('percent', Uint16((kwargs["percent"]))),
                ('auto_vest', Bool(kwargs["auto_vest"])),
            ]))

class WitnessUpdate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            prefix = kwargs.pop("prefix", default_prefix)

            if not kwargs["block_signing_key"]:
                kwargs["block_signing_key"] = "{}1111111111111111111111111111111114T1Anm".format(prefix)
            super().__init__(OrderedDict([
                ('owner', String(kwargs["owner"])),
                ('url', String(kwargs["url"])),
                ('block_signing_key', PublicKey(kwargs["block_signing_key"], prefix=prefix)),
                ('props', ChainProperties(kwargs["props"])),
                ('fee', Amount(kwargs["fee"])),
            ]))

# TODO: VersionedChainPropertiesUpdate
class ChainPropertiesUpdate(GrapheneObject):
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
                if 'min_delegation' in props:
                    type_id = 1
                if 'auction_window_size' in props:
                    type_id = 2

                obj = [type_id, {'props': props}]
                props = Props(obj)

            super().__init__(OrderedDict([
                ('owner', String(kwargs["owner"])),
                ('props', props),
            ]))

class AccountWitnessVote(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('account', String(kwargs["account"])),
                ('witness', String(kwargs["witness"])),
                ('approve', Bool(bool(kwargs["approve"]))),
            ]))


class ProposalCreate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            assert kwargs['proposed_operations'], 'proposed_operations cannot be empty!'

            if isinstance(kwargs['proposed_operations'][0], GrapheneObject):
                proposed_operations = [OperationWrapper(Operation(op)) for op in kwargs['proposed_operations']]
            else:
                proposed_operations = [OperationWrapper(Operation(op['op'])) for op in kwargs['proposed_operations']]

            review_period_time = PointInTime(kwargs['review_period_time']) if kwargs.get('review_period_time') else None

            super().__init__(OrderedDict([
                ('author', String(kwargs['author'])),
                ('title', String(kwargs['title'])),
                ('memo', String(kwargs.get('memo', ''))),
                ('expiration_time', PointInTime(kwargs['expiration_time'])),
                ('proposed_operations', Array(proposed_operations)),
                ('review_period_time', Optional(review_period_time)),
                ('extensions', Array(kwargs.get('extensions') or [])),
            ]))


class ProposalUpdate(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]

            active_approvals_to_add = [String(str(x)) for x in kwargs.get('active_approvals_to_add') or []]
            active_approvals_to_remove = [String(str(x)) for x in kwargs.get('active_approvals_to_remove') or []]
            owner_approvals_to_add = [String(str(x)) for x in kwargs.get('owner_approvals_to_add') or []]
            owner_approvals_to_remove = [String(str(x)) for x in kwargs.get('owner_approvals_to_remove') or []]
            posting_approvals_to_add = [String(str(x)) for x in kwargs.get('posting_approvals_to_add') or []]
            posting_approvals_to_remove = [String(str(x)) for x in kwargs.get('posting_approvals_to_remove') or []]
            key_approvals_to_add = [String(str(x)) for x in kwargs.get('key_approvals_to_add') or []]
            key_approvals_to_remove = [String(str(x)) for x in kwargs.get('key_approvals_to_remove') or []]

            super().__init__(OrderedDict([
                ('author', String(kwargs['author'])),
                ('title', String(kwargs['title'])),
                ('active_approvals_to_add', Array(active_approvals_to_add)),
                ('active_approvals_to_remove', Array(active_approvals_to_remove)),
                ('owner_approvals_to_add', Array(owner_approvals_to_add)),
                ('owner_approvals_to_remove', Array(owner_approvals_to_remove)),
                ('posting_approvals_to_add', Array(posting_approvals_to_add)),
                ('posting_approvals_to_remove', Array(posting_approvals_to_remove)),
                ('key_approvals_to_add', Array(key_approvals_to_add)),
                ('key_approvals_to_remove', Array(key_approvals_to_remove)),
                ('extensions', Array(kwargs.get('extensions') or [])),
            ]))


class ProposalDelete(GrapheneObject):
    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(OrderedDict([
                ('author', String(kwargs['author'])),
                ('title', String(kwargs['title'])),
                ('requester', String(kwargs['requester'])),
                ('extensions', Array(kwargs.get('extensions') or []))
            ]))

fill_classmaps()

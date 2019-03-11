# -*- coding: utf-8 -*-
import json
import struct

from collections import OrderedDict

from graphenebase.objects import GrapheneObject
from graphenebase.objects import Operation as GrapheneOperation
from graphenebase.objects import isArgsThisClass, Asset
from graphenebase.types import Array, Bool, Bytes, Fixed_array, Id, Int16, Int64, Map
from graphenebase.types import ObjectId as GPHObjectId
from graphenebase.types import (
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

from .chains import PRECISIONS, DEFAULT_PREFIX
from .account import PublicKey
from .operationids import operations


class Operation(GrapheneOperation):
    """ Need to overwrite a few attributes to load proper operations from
        viz
    """

    module = "vizbase.operations"
    operations = operations


class Amount:
    def __init__(self, d):
        self.amount, self.asset = d.strip().split(" ")
        self.amount = float(self.amount)

        if self.asset in PRECISIONS:
            self.precision = PRECISIONS[self.asset]
        else:
            raise Exception("Asset unknown")

    def __bytes__(self):
        # padding
        asset = self.asset + "\x00" * (7 - len(self.asset))
        amount = round(float(self.amount) * 10 ** self.precision)
        return (
            struct.pack("<q", amount)
            + struct.pack("<b", self.precision)
            + bytes(asset, "ascii")
        )

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
                key=lambda x: PublicKey(x[0], prefix=prefix),
                reverse=False,
            )
            accountAuths = Map(
                [[String(e[0]), Uint16(e[1])] for e in kwargs["account_auths"]]
            )
            keyAuths = Map(
                [
                    [PublicKey(e[0], prefix=prefix), Uint16(e[1])]
                    for e in kwargs["key_auths"]
                ]
            )
            super().__init__(
                OrderedDict(
                    [
                        ("weight_threshold", Uint32(int(kwargs["weight_threshold"]))),
                        ("account_auths", accountAuths),
                        ("key_auths", keyAuths),
                    ]
                )
            )

# -*- coding: utf-8 -*-
from graphenecommon.exceptions import (
    InvalidWifError,
    KeyAlreadyInStoreException,
    KeyNotFound,
    NoWalletException,
    OfflineHasNoRPCException,
    WalletExists,
    WalletLocked,
)
from graphenecommon.wallet import Wallet as GrapheneWallet

from vizbase.account import PrivateKey

from .instance import BlockchainInstance


@BlockchainInstance.inject
class Wallet(GrapheneWallet):
    def define_classes(self):
        # identical to those in viz.py!
        self.default_key_store_app_name = "viz"
        self.privatekey_class = PrivateKey

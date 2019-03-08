# -*- coding: utf-8 -*-
import random

from graphenecommon.memo import Memo as GrapheneMemo
from vizbase.account import PrivateKey, PublicKey
from vizbase import memo

from .account import Account
from .instance import BlockchainInstance
from .exceptions import (
    InvalidMemoKeyException,
    AccountDoesNotExistsException,
    WrongMemoKey,
    InvalidMessageSignature,
    KeyNotFound,
    MissingKeyError,
)


@BlockchainInstance.inject
class Memo(GrapheneMemo):
    """ Deals with Memos that are attached to a transfer

        :param viz.account.Account from_account: Account that has sent
            the memo
        :param viz.account.Account to_account: Account that has received
            the memo
        :param viz.viz.Client blockchain_instance: Client
            instance

        A memo is encrypted with a shared secret derived from a private key of
        the sender and a public key of the receiver. Due to the underlying
        mathematics, the same shared secret can be derived by the private key
        of the receiver and the public key of the sender. The encrypted message
        is perturbed by a nonce that is part of the transmitted message.

        .. code-block:: python

            from viz.memo import Memo
            m = Memo("vizeu", "wallet.xeroc")
            m.unlock_wallet("secret")
            enc = (m.encrypt("foobar"))
            print(enc)
            >> {'nonce': '17329630356955254641', 'message': '8563e2bb2976e0217806d642901a2855'}
            print(m.decrypt(enc))
            >> foobar

        To decrypt a memo, simply use

        .. code-block:: python

            from viz.memo import Memo
            m = Memo()
            m.blockchain.wallet.unlock("secret")
            print(memo.decrypt(op_data["memo"]))

        if ``op_data`` being the payload of a transfer operation.

    """

    def define_classes(self):
        self.account_class = Account
        self.privatekey_class = PrivateKey
        self.publickey_class = PublicKey

    def encrypt(self, message):
        """ Encrypt a memo

            :param str message: clear text memo message
            :returns: encrypted message
            :rtype: str

            This class overriden because upstream assumes memo key is in
            account['options']['memo_key'], and bitshares memo format is different
        """
        if not message:
            return None

        nonce = str(random.getrandbits(64))
        try:
            memo_wif = self.blockchain.wallet.getPrivateKeyForPublicKey(
                self.from_account["memo_key"]
            )
        except KeyNotFound:
            # if all fails, raise exception
            raise MissingKeyError(
                "Memo private key {} for {} could not be found".format(
                    self.from_account["memo_key"], self.from_account["name"]
                )
            )
        if not memo_wif:
            raise MissingKeyError(
                "Memo key for %s missing!" % self.from_account["name"]
            )

        if not hasattr(self, "chain_prefix"):
            self.chain_prefix = self.blockchain.prefix

        enc = memo.encode_memo(
            self.privatekey_class(memo_wif),
            self.publickey_class(self.to_account["memo_key"], prefix=self.chain_prefix),
            nonce,
            message,
            prefix=self.chain_prefix,
        )

        return enc

    def decrypt(self, message):
        """ Decrypt a message

            :param dict message: encrypted memo message
            :returns: decrypted message
            :rtype: str
        """
        if not message:
            return None

        assert enc_memo[0] == "#", "decode memo requires memos to start with '#'"
        keys = memo.involved_keys(enc_memo)
        wif = None
        for key in keys:
            wif = self.blockchain.wallet.getPrivateKeyForPublicKey(str(key))
            if wif:
                break
        if not wif:
            raise MissingKeyError("None of the required memo keys are installed!")

        if not hasattr(self, "chain_prefix"):
            self.chain_prefix = self.blockchain.prefix

        return memo.decode_memo(self.privatekey_class(wif), enc_memo)

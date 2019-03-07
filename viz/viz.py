# -*- coding: utf-8 -*-
import logging

from datetime import datetime, timedelta

from graphenecommon.chain import AbstractGrapheneChain

from vizapi.noderpc import NodeRPC
from vizbase import operations
from vizbase.account import PublicKey

from .exceptions import AccountExistsException
from .instance import set_shared_blockchain_instance, shared_blockchain_instance
from .storage import get_default_config_store
from .transactionbuilder import ProposalBuilder, TransactionBuilder
from .wallet import Wallet
from .account import Account
from .amount import Amount


# from .utils import formatTime

log = logging.getLogger(__name__)


class Client(AbstractGrapheneChain):
    """ Blockchain network client

        :param str node: Node to connect to *(optional)*
        :param str rpcuser: RPC user *(optional)*
        :param str rpcpassword: RPC password *(optional)*
        :param bool nobroadcast: Do **not** broadcast a transaction!
            *(optional)*
        :param bool debug: Enable Debugging *(optional)*
        :param array,dict,string keys: Predefine the wif keys to shortcut the
            wallet database *(optional)*
        :param bool offline: Boolean to prevent connecting to network (defaults
            to ``False``) *(optional)*
        :param str proposer: Propose a transaction using this proposer
            *(optional)*
        :param int proposal_expiration: Expiration time (in seconds) for the
            proposal *(optional)*
        :param int proposal_review: Review period (in seconds) for the proposal
            *(optional)*
        :param int expiration: Delay in seconds until transactions are supposed
            to expire *(optional)*
        :param str blocking: Wait for broadcasted transactions to be included
            in a block and return full transaction (can be "head" or
            "irrversible")
        :param bool bundle: Do not broadcast transactions right away, but allow
            to bundle operations *(optional)*

        Three wallet operation modes are possible:

        * **Wallet Database**: Here, the libs load the keys from the
          locally stored wallet SQLite database (see ``storage.py``).
          To use this mode, simply call ``Client()`` without the
          ``keys`` parameter
        * **Providing Keys**: Here, you can provide the keys for
          your accounts manually. All you need to do is add the wif
          keys for the accounts you want to use as a simple array
          using the ``keys`` parameter to ``Client()``.
        * **Force keys**: This more is for advanced users and
          requires that you know what you are doing. Here, the
          ``keys`` parameter is a dictionary that overwrite the
          ``active``, ``owner``, or ``memo`` keys for
          any account. This mode is only used for *foreign*
          signatures!

        If no node is provided, it will connect to the node of
        http://uptick.rocks. It is **highly** recommended that you
        pick your own node instead. Default settings can be changed with:

        .. code-block:: python

            uptick set node <host>

        where ``<host>`` starts with ``ws://`` or ``wss://``.

        The purpose of this class it to simplify interaction with
        Client.

        The idea is to have a class that allows to do this:

        .. code-block:: python

            from viz import Client
            viz = Client()
            print(viz.info())

        All that is requires is for the user to have added a key with
        ``uptick``

        .. code-block:: bash

            uptick addkey

        and setting a default author:

        .. code-block:: bash

            uptick set default_account xeroc

        This class also deals with edits, votes and reading content.
    """

    def define_classes(self):
        from .blockchainobject import BlockchainObject

        self.wallet_class = Wallet
        self.account_class = Account
        self.rpc_class = NodeRPC
        self.default_key_store_app_name = "viz"
        self.proposalbuilder_class = ProposalBuilder
        self.transactionbuilder_class = TransactionBuilder
        self.blockchainobject_class = BlockchainObject

    def transfer(self, to, amount, asset, memo="", account=None, **kwargs):
        """ Transfer an asset to another account.

            :param str to: Recipient
            :param float amount: Amount to transfer
            :param str asset: Asset to transfer
            :param str memo: (optional) Memo, may begin with `#` for encrypted
                messaging
            :param str account: (optional) the source account for the transfer
                if not ``default_account``
        """
        if not account:
            if "default_account" in self.config:
                account = self.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        amount = Amount('{} {}'.format(amount, asset))

        if memo and memo[0] == "#":
            from .memo import Memo

            memoObj = Memo(
                from_account=account, to_account=to, blockchain_instance=self
            )
            memo = memoObj.encrypt(memo)

        op = operations.Transfer(
            **{
                "from": account,
                "to": to,
                "amount": '{}'.format(str(amount)),
                "memo": memo,
            }
        )

        return self.finalizeOp(op, account, "active", **kwargs)

    def decode_memo(self, enc_memo):
        """ Try to decode an encrypted memo
        """
        from .memo import Memo

        memoObj = Memo()
        return memoObj.decrypt(enc_memo)

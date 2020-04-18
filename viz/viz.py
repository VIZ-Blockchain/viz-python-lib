# -*- coding: utf-8 -*-
import logging

from datetime import datetime, timedelta

from graphenecommon.chain import AbstractGrapheneChain

from vizapi.noderpc import NodeRPC
from vizbase import operations
from vizbase.account import PublicKey
from vizbase.chains import PRECISIONS

from .exceptions import AccountExistsException
from .instance import set_shared_blockchain_instance, shared_blockchain_instance
from .storage import get_default_config_store
from .transactionbuilder import ProposalBuilder, TransactionBuilder
from .wallet import Wallet
from .account import Account
from .amount import Amount

CHAIN_100_PERCENT = 10000
CHAIN_1_PERCENT = CHAIN_100_PERCENT / 100

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
          ``active``, ``master``, or ``memo`` keys for
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

        amount = Amount("{} {}".format(amount, asset))

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
                "amount": "{}".format(str(amount)),
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

    def award(
        self, receiver, energy, memo="", beneficiaries=[], account=None, **kwargs
    ):
        """ Award someone

            :param str receiver: account name of award receiver
            :param int energy: energy as 0-10000 integer where 10000 is 100%
            :param str memo: optional comment
            :param list beneficiaries: list of dicts, example [{'account': 'vvk', 'weight': 50}]
            :param str account: initiator account name
        """
        if not account:
            if "default_account" in self.config:
                account = self.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.Award(
            **{
                "initiator": account,
                "receiver": receiver,
                "energy": int(energy),
                "custom_sequence": kwargs.get("custom_sequence", 0),
                "memo": memo,
                "beneficiaries": beneficiaries,
            }
        )

        return self.finalizeOp(op, account, "regular")

    def custom(self, id, json, required_auths=[], required_regular_auths=[]):
        """ Create a custom operation

            :param str id: identifier for the custom (max length 32 bytes)
            :param json json: the json data to put into the custom operation
            :param list required_auths: (optional) required active auths
            :param list required_regular_auths: (optional) regular auths
        """
        account = None
        requred_key_type = "regular"
        if len(required_auths):
            account = required_auths[0]
            requred_key_type = "active"
        elif len(required_regular_auths):
            account = required_regular_auths[0]
        else:
            raise Exception("At least one account needs to be specified")

        op = operations.Custom(
            **{
                "json": json,
                "required_auths": required_auths,
                "required_regular_auths": required_regular_auths,
                "id": id,
            }
        )
        return self.finalizeOp(op, account, requred_key_type)

    def withdraw_vesting(self, amount, account=None):
        """ Withdraw SHARES from the vesting account.

            :param float amount: number of SHARES to withdraw over a period
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.Withdraw_vesting(
            **{
                "account": account,
                "vesting_shares": "{:.{prec}f} {asset}".format(
                    float(amount),
                    prec=PRECISIONS.get(self.rpc.chain_params["shares_symbol"]),
                    asset=self.rpc.chain_params["shares_symbol"],
                ),
            }
        )

        return self.finalizeOp(op, account, "active")

    def transfer_to_vesting(self, amount, to=None, account=None):
        """ Vest free CORE into vesting

            :param float amount: number of CORE to vest
            :param str to: (optional) the source account for the transfer if not ``default_account``
            :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        if not to:
            to = account  # powerup on the same account

        op = operations.Transfer_to_vesting(
            **{
                "from": account,
                "to": to,
                "amount": "{:.{prec}f} {asset}".format(
                    float(amount),
                    prec=PRECISIONS.get(self.rpc.chain_params["core_symbol"]),
                    asset=self.rpc.chain_params["core_symbol"],
                ),
            }
        )

        return self.finalizeOp(op, account, "active")

    def set_withdraw_vesting_route(
        self, to, percentage=100, account=None, auto_vest=False
    ):
        """ Set up a vesting withdraw route. When vesting shares are
            withdrawn, they will be routed to these accounts based on the
            specified weights.

            To obtain existing withdraw routes, use the following example:

            .. code-block:: python

                a = Account('vvk', blockchain_instance=viz)
                pprint(a.get_withdraw_routes())

            :param str to: Recipient of the vesting withdrawal
            :param float percentage: The percent of the withdraw to go
                to the 'to' account.
            :param str account: (optional) the vesting account
            :param bool auto_vest: Set to true if the from account
                should receive the SHARES as SHARES, or false if it should
                receive them as CORE. (defaults to ``False``)
        """
        if not account:
            account = configStorage.get("default_account")
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.Set_withdraw_vesting_route(
            **{
                "from_account": account,
                "to_account": to,
                "percent": int(percentage * CHAIN_1_PERCENT),
                "auto_vest": auto_vest,
            }
        )

        return self.finalizeOp(op, account, "active")

    # TODO: Methods to implement:
    # - create_account
    # - withdraw_vesting
    # - transfer_to_vesting
    # - delegate_vesting_shares
    # - witness_update
    # - chain_properties_update
    # - set_withdraw_vesting_route
    # - allow / disallow
    # - update_memo_key
    # - approve_witness / disapprove_witness
    # - update_account_profile
    # - account_metadata
    # - proposal_create / proposal_update / proposal_delete
    # - witness_proxy
    # - recover-related methods
    # - escrow-related methods
    # - worker create / cancel / vote
    # - invite-related: create_invite, claim_invite_balance, invite_registration
    # - paid subscrives related: set_paid_subscription / paid_subscribe

# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional, Union

from graphenecommon.chain import AbstractGrapheneChain
from graphenecommon.exceptions import KeyAlreadyInStoreException, AccountDoesNotExistsException

from vizapi.noderpc import NodeRPC
from vizbase import operations
from vizbase.account import PublicKey
from vizbase.chains import PRECISIONS

from .account import Account
from .amount import Amount
from .converter import Converter
from .exceptions import AccountExistsException
from .transactionbuilder import ProposalBuilder, TransactionBuilder
from .wallet import Wallet

# from .utils import formatTime

log = logging.getLogger(__name__)


class Client(AbstractGrapheneChain):
    """
    Blockchain network client.

    :param str node: Node to connect to
    :param str rpcuser: RPC user *(optional)*
    :param str rpcpassword: RPC password *(optional)*
    :param bool nobroadcast: Do **not** broadcast a transaction!
        *(optional)*
    :param bool debug: Enable Debugging *(optional)*
    :param array,dict,string keys: Predefine the wif keys to shortcut the
        wallet database *(optional)*
    :param bool offline: Boolean to prevent connecting to network (defaults
        to ``False``) *(optional)*
    :param int expiration: Delay in seconds until transactions are supposed
        to expire *(optional)*
    :param bool blocking: Wait for broadcasted transactions to be included
        in a block and return full transaction. Blocking is checked inside
        :py:meth:`~graphenecommon.transactionbuilder.TransactionBuilder.broadcast`
        *(Default: False)*, *(optional)*
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

    The purpose of this class it to simplify interaction with
    blockchain by providing high-level methods instead of forcing user to use RPC methods directly.

    The idea is to have a class that allows to do this:

    .. code-block:: python

        from viz import Client
        viz = Client()
        print(viz.info())
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

    def new_proposal(
        self,
        title: str,
        memo: str = '',
        parent: Optional[TransactionBuilder] = None,
        expiration_time: int = 2 * 24 * 60 * 60,
        review_period_time: Optional[int] = None,
        account: str = None,
        **kwargs: Any,
    ) -> ProposalBuilder:
        """
        Create a new proposal.

        Proposal is a way to propose some transaction to another account. Primary usecase is a multisig account which
        requires several members approval to perform an operation.

        :param str title: title of proposed transaction
        :param str memo: may be a description of the proposal
        :param TransactionBuilder parent: TransactionBuilder instance to add proposal to
        :param int expiration_time: maximum time allowed for transaction
        :param int review_period_time: time to make a decision of the transaction participants
        :param str account: author of proposed transaction

        Example usage:

        .. code-block:: python

            from viz import Client
            viz = Client()
            proposal = viz.new_proposal('title', 'test proposal', account='alice')
            viz.transfer("null", 1, "VIZ", memo="test transfer proposal", account=default_account, append_to=proposal)
            proposal.broadcast()
        """
        if not parent:
            parent = self.tx()

        if not account:
            if "default_account" in self.config:
                account = self.config["default_account"]

        if not account:
            raise ValueError("You need to provide an account")

        proposal = self.proposalbuilder_class(
            account,
            title,
            memo,
            proposal_expiration=expiration_time,
            proposal_review=review_period_time,
            blockchain_instance=self,
            parent=parent,
            **kwargs,
        )
        if parent:
            parent.appendOps(proposal)
        self._propbuffer.append(proposal)
        return proposal

    def proposal_update(
        self,
        author: str,
        title: str,
        approver: Union[str, list] = None,
        keys: Union[str, list] = None,
        permission: str = "regular",
        approve: bool = True,
        account: str = None,
    ) -> dict:
        """
        Update proposal (approve or disapprove)

        :param str author: author of proposed transaction
        :param str title: title of proposed transaction
        :param str, list approver: account(s) for approvals, default is account field
        :param str keys: public key(s) used for multisig accounts (key approval)
        :param str permission: the required permission type for signing
        :param str approve: True = approve, False = disapprove
        :param str account: the account that authorizes the operation
        """
        if not account:
            if "default_account" in self.config:
                account = self.config["default_account"]

        if not account:
            raise ValueError("You need to provide an account")

        if approver:
            if not isinstance(approver, list):
                approver = [approver]
        else:
            approver = [account]

        payload = {}

        approval_dict_key = "{permission}_approvals_to_{action}".format(
            permission=permission, action="add" if approve else "remove"
        )
        payload[approval_dict_key] = approver

        if keys:
            if not isinstance(keys, list):
                keys = [keys]
            keys = [PublicKey(key) for key in keys]
            payload["key_approvals_to_{}".format("add" if approve else "remove")] = keys

        op = operations.Proposal_update(**{**payload, "author": author, "title": title, "extensions": []})
        return self.finalizeOp(op, account, permission)

    def transfer(
        self, to: str, amount: float, asset: str, memo: str = "", account: Optional[str] = None, **kwargs: Any
    ) -> dict:
        """
        Transfer an asset to another account.

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

        _amount = Amount("{} {}".format(amount, asset))

        if memo and memo[0] == "#":
            from .memo import Memo

            memo_obj = Memo(from_account=account, to_account=to, blockchain_instance=self)
            memo = memo_obj.encrypt(memo)

        op = operations.Transfer(**{"from": account, "to": to, "amount": "{}".format(str(_amount)), "memo": memo})

        return self.finalizeOp(op, account, "active", **kwargs)

    def award(
        self,
        receiver: str,
        energy: float,
        memo: str = "",
        beneficiaries: Optional[List[Dict[str, Union[str, int]]]] = None,
        account: str = None,
        **kwargs: Any,
    ) -> dict:
        """
        Award someone.

        :param str receiver: account name of award receiver
        :param float energy: energy as 0-100%
        :param str memo: optional comment
        :param list beneficiaries: list of dicts, example ``[{'account': 'vvk', 'weight': 50}]``
        :param str account: initiator account name
        """
        if not account:
            if "default_account" in self.config:
                account = self.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        if beneficiaries is None:
            beneficiaries = []

        op = operations.Award(
            **{
                "initiator": account,
                "receiver": receiver,
                "energy": int(energy * self.rpc.config['CHAIN_1_PERCENT']),
                "custom_sequence": kwargs.get("custom_sequence", 0),
                "memo": memo,
                "beneficiaries": beneficiaries,
            }
        )

        return self.finalizeOp(op, account, "regular")

    def fixed_award(
        self,
        receiver: str,
        reward_amount: float,
        max_energy: float,
        memo: str = "",
        beneficiaries: Optional[List[Dict[str, Union[str, int]]]] = None,
        account: str = None,
        **kwargs: Any,
    ) -> dict:
        """
        Award someone.

        :param str receiver: account name of award receiver
        :param float max_energy: maximum energy one is willing to expend
        :param float reward_amount: reward amount
        :param str memo: optional comment
        :param list beneficiaries: list of dicts, example ``[{'account': 'vvk', 'weight': 50}]``
        :param str account: initiator account name
        """
        if not account:
            if "default_account" in self.config:
                account = self.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        if beneficiaries is None:
            beneficiaries = []

        _amount = Amount("{} {}".format(reward_amount, "VIZ"))

        op = operations.Fixed_award(
            **{
                "initiator": account,
                "receiver": receiver,
                "reward_amount": "{}".format(str(_amount)),
                "max_energy": int(max_energy * self.rpc.config['CHAIN_1_PERCENT']),
                "custom_sequence": kwargs.get("custom_sequence", 0),
                "memo": memo,
                "beneficiaries": beneficiaries,
            }
        )

        return self.finalizeOp(op, account, "regular")

    def custom(
        self,
        id_: str,
        json: Union[Dict, List],
        required_active_auths: Optional[List[str]] = None,
        required_regular_auths: Optional[List[str]] = None,
    ) -> dict:
        """
        Create a custom operation.

        :param str id_: identifier for the custom (max length 32 bytes)
        :param dict,list json: the json data to put into the custom operation
        :param list required_active_auths: (optional) require signatures from these active auths to make this operation
            valid
        :param list required_regular_auths: (optional) require signatures from these regular auths
        """
        if required_active_auths is None:
            required_active_auths = []
        if required_regular_auths is None:
            required_regular_auths = []

        if not isinstance(required_active_auths, list) or not isinstance(required_regular_auths, list):
            raise ValueError("Expected list for required_active_auths or required_regular_auths")

        account = None
        required_key_type = "regular"

        if len(required_active_auths):
            account = required_active_auths[0]
            required_key_type = "active"
        elif len(required_regular_auths):
            account = required_regular_auths[0]
        else:
            raise ValueError("At least one account needs to be specified")

        op = operations.Custom(
            **{
                "json": json,
                "required_active_auths": required_active_auths,
                "required_regular_auths": required_regular_auths,
                "id": id_,
            }
        )
        return self.finalizeOp(op, account, required_key_type)

    def withdraw_vesting(self, amount: float, account: str = None) -> dict:
        """
        Withdraw SHARES from the vesting account.

        :param float amount: number of SHARES to withdraw over a period
        :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in self.config:
                account = self.config["default_account"]
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

    def transfer_to_vesting(self, amount: float, to: str = None, account: str = None) -> dict:
        """
        Vest free VIZ into vesting.

        :param float amount: number of VIZ to vest
        :param str to: (optional) the source account for the transfer if not ``default_account``
        :param str account: (optional) the source account for the transfer if not ``default_account``
        """
        if not account:
            if "default_account" in self.config:
                account = self.config["default_account"]
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
        self, to: str, percentage: float = 100, account: str = None, auto_vest: bool = False
    ) -> dict:
        """
        Set up a vesting withdraw route. When vesting shares are withdrawn, they will be routed to these accounts based
        on the specified weights.

        To obtain existing withdraw routes, use :py:meth:`get_withdraw_vesting_routes`

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
            if "default_account" in self.config:
                account = self.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")

        op = operations.Set_withdraw_vesting_route(
            **{
                "from_account": account,
                "to_account": to,
                "percent": int(percentage * self.rpc.config['CHAIN_1_PERCENT']),
                "auto_vest": auto_vest,
            }
        )

        return self.finalizeOp(op, account, "active")

    def get_withdraw_vesting_routes(self, account: str, **kwargs: str) -> dict:
        """
        Get vesting withdraw route for an account.

        This is a shortcut for :py:meth:`viz.account.Account.get_withdraw_routes`.

        :param str account: account name
        :return: list with routes
        """
        _account = Account(account, blockchain_instance=self)

        return _account.get_withdraw_routes(**kwargs)

    def create_account(
        self,
        account_name: str,
        json_meta: Optional[Dict[str, Any]] = None,
        password: str = None,
        master_key: str = None,
        active_key: str = None,
        regular_key: str = None,
        memo_key: str = None,
        additional_master_keys: Optional[List[str]] = None,
        additional_active_keys: Optional[List[str]] = None,
        additional_regular_keys: Optional[List[str]] = None,
        additional_master_accounts: Optional[List[str]] = None,
        additional_active_accounts: Optional[List[str]] = None,
        additional_regular_accounts: Optional[List[str]] = None,
        store_keys: bool = True,
        fee: float = 0,
        delegation: float = None,
        creator: str = None,
        referrer: str = '',
    ) -> dict:
        """
        Create new account.

        The brainkey/password can be used to recover all generated keys (see :py:mod:`vizbase.account` for more details.

        By default, this call will use ``default_account`` to
        register a new name ``account_name`` with all keys being derived from a new brain key that will be returned. The
        corresponding keys will automatically be installed in the wallet.

        .. note::

            Account creations cost a fee that is defined by the network. If you create an account, you will need to pay
            for that fee!

           **You can partially pay that fee by delegating SHARES.**

        .. warning::

            Don't call this method unless you know what you are doing! Be sure to understand what this method does and
            where to find the private keys for your account.

        .. note::

            Please note that this imports private keys (if password is present) into the wallet by default.

        :param str account_name: (**required**) new account name
        :param dict json_meta: Optional meta data for the account
        :param str password: Alternatively to providing keys, one
                             can provide a password from which the
                             keys will be derived
        :param str master_key: Main master key
        :param str active_key: Main active key
        :param str regular_key: Main regular key
        :param str memo_key: Main memo_key
        :param list additional_master_keys:  Additional master public keys
        :param list additional_active_keys: Additional active public keys
        :param list additional_regular_keys: Additional regular public keys
        :param list additional_master_accounts: Additional master account names
        :param list additional_active_accounts: Additional active account names
        :param list additional_regular_accounts: Additional regular account names
        :param bool store_keys: Store new keys in the wallet (default: ``True``)
        :param float fee: (Optional) If set, `creator` pay a fee of this amount,
                                    and delegate the rest with SHARES (calculated automatically).
        :param float delegation: amount of SHARES to be delegated to a new account
        :param str creator: which account should pay the registration fee
                            (defaults to ``default_account``)
        :param str referrer: account who will be set as referrer, defaults to creator
        :raises AccountExistsException: if the account already exists on the blockchain
        """
        max_length = self.rpc.config['CHAIN_MAX_ACCOUNT_NAME_LENGTH']
        if len(account_name) > max_length:
            raise ValueError("Account name must be at most {} chars long".format(max_length))

        if not creator and self.config["default_account"]:
            creator = self.config["default_account"]
        if not creator:
            raise ValueError("No creator account given")

        if password and (master_key or regular_key or active_key or memo_key):
            raise ValueError("You cannot use 'password' AND provide keys!")

        if additional_master_keys is None:
            additional_master_keys = []
        if additional_active_keys is None:
            additional_active_keys = []
        if additional_regular_keys is None:
            additional_regular_keys = []
        if additional_master_accounts is None:
            additional_master_accounts = []
        if additional_active_accounts is None:
            additional_active_accounts = []
        if additional_regular_accounts is None:
            additional_regular_accounts = []

        # check if account already exists
        try:
            Account(account_name, blockchain_instance=self)
        except Exception:
            pass
        else:
            raise AccountExistsException

        # Generate new keys from password
        from vizbase.account import PasswordKey, PublicKey

        key_roles = ['regular', 'active', 'master', 'memo']
        keys: DefaultDict[str, Union[PasswordKey, Dict]] = defaultdict(dict)

        if password:
            for role in key_roles:
                passkey = PasswordKey(account_name, password, role=role)
                keys['pubkeys'][role] = passkey.get_public_key()
                keys['privkeys'][role] = passkey.get_private_key()
                # store private keys
                if store_keys:
                    self._store_keys(keys['privkeys'][role])
        elif master_key and regular_key and active_key and memo_key:
            keys['pubkeys']['regular'] = PublicKey(regular_key, prefix=self.prefix)
            keys['pubkeys']['active'] = PublicKey(active_key, prefix=self.prefix)
            keys['pubkeys']['master'] = PublicKey(master_key, prefix=self.prefix)
            keys['pubkeys']['memo'] = PublicKey(memo_key, prefix=self.prefix)
        else:
            raise ValueError("Call incomplete! Provide either a password or public keys!")

        # main key authorities
        authority: Union[str, List] = ''
        for role in key_roles:
            if role == 'memo':
                authority = format(keys['pubkeys'][role], self.prefix)
            else:
                authority = [[format(keys['pubkeys'][role], self.prefix), 1]]
            keys['authorities'][role] = authority

        # additional key authorities
        for key in additional_master_keys:
            keys['authorities']['master'].append([key, 1])
        for key in additional_active_keys:
            keys['authorities']['active'].append([key, 1])
        for key in additional_regular_keys:
            keys['authorities']['regular'].append([key, 1])

        # account authorities
        owner_accounts_authority = []
        active_accounts_authority = []
        posting_accounts_authority = []

        for key in additional_master_accounts:
            owner_accounts_authority.append([key, 1])
        for key in additional_active_accounts:
            active_accounts_authority.append([key, 1])
        for key in additional_regular_accounts:
            posting_accounts_authority.append([key, 1])

        props = self.rpc.get_chain_properties()

        if not fee:
            required_fee = Amount(props['account_creation_fee']).amount
        else:
            required_fee = fee

        if delegation is None:
            delegation_ratio = props['create_account_delegation_ratio']
            cv = Converter(blockchain_instance=self)
            shares_price = cv.core_per_share()
            delegation = required_fee * delegation_ratio * shares_price

        op = {
            "fee": "{:.{prec}f} {asset}".format(
                float(required_fee),
                prec=PRECISIONS.get(self.rpc.chain_params["core_symbol"]),
                asset=self.rpc.chain_params["core_symbol"],
            ),
            "delegation": "{:.{prec}f} {asset}".format(
                float(delegation),
                prec=PRECISIONS.get(self.rpc.chain_params["shares_symbol"]),
                asset=self.rpc.chain_params["shares_symbol"],
            ),
            "creator": creator,
            "new_account_name": account_name,
            "master": {
                "account_auths": owner_accounts_authority,
                "key_auths": keys['authorities']['master'],
                "weight_threshold": 1,
            },
            "active": {
                "account_auths": active_accounts_authority,
                "key_auths": keys['authorities']['active'],
                "weight_threshold": 1,
            },
            "regular": {
                "account_auths": posting_accounts_authority,
                "key_auths": keys['authorities']['regular'],
                "weight_threshold": 1,
            },
            "memo_key": keys['authorities']['memo'],
            "json_metadata": json_meta or {},
            "referrer": referrer,
            "prefix": self.prefix,
        }

        op = operations.Account_create(**op)

        return self.finalizeOp(op, creator, "active")

    def update_account_profile(
        self,
        account_name: str,
        memo_key: str,
        json_meta: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """
        Update account profile.

        By default, this call will use ``default_account`` to
        update account profile with all keys being derived from a new brain key that will be returned. The
        corresponding keys will automatically be installed in the wallet.

        :param str account_name: (**required**) new account name
        :param dict json_meta: Optional meta data for the account

        :raises AccountDoesNotExistsException: if the account does not exist
        """

        # check if the account does not exist
        try:
            Account(account_name, blockchain_instance=self)
        except Exception:
            raise AccountDoesNotExistsException

        op = {
            "account": account_name,
            "memo_key": memo_key,
            "json_metadata": json_meta or {},
        }

        op = operations.Account_update(**op)

        return self.finalizeOp(ops=op, account=account_name, permission="active")

    def delegate_vesting_shares(self, delegator: str, delegatee: str, amount: float) -> dict:
        """
        Delegate vesting SHARES to account.

        :param str delegator: account that delegates
        :param str delegatee: account to which is delegated
        :param float amount: number of SHARES to be delegated

        :raises AccountDoesNotExistsException: if the account does not exist
        """

        # check if the account does not exist
        try:
            Account(delegatee, blockchain_instance=self)
        except Exception:
            raise AccountDoesNotExistsException

        op = {
            "delegator": delegator,
            "delegatee": delegatee,
            "vesting_shares": "{:.{prec}f} {asset}".format(
                float(amount),
                prec=PRECISIONS.get(self.rpc.chain_params["shares_symbol"]),
                asset=self.rpc.chain_params["shares_symbol"],
            ),
        }

        op = operations.Delegate_vesting_shares(**op)

        return self.finalizeOp(op, delegator, "active")

    def _store_keys(self, *args):
        """Store private keys to local storage."""
        for key in args:
            try:
                self.wallet.addPrivateKey(str(key))
            except KeyAlreadyInStoreException:
                pass

    # TODO: Methods to implement:
    # - witness_update
    # - chain_properties_update
    # - allow / disallow
    # - update_memo_key
    # - approve_witness / disapprove_witness
    # - account_metadata
    # - proposal_create / proposal_update / proposal_delete
    # - witness_proxy
    # - recover-related methods
    # - escrow-related methods
    # - worker create / cancel / vote
    # - invite-related: create_invite, claim_invite_balance, invite_registration
    # - paid subscrives related: set_paid_subscription / paid_subscribe

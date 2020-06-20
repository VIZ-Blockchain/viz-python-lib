# -*- coding: utf-8 -*-
# We don't have own Asset class because it is unneeded
import struct
from binascii import unhexlify

from graphenebase.utils import formatTimeFromNow
from graphenecommon.asset import Asset
from graphenecommon.exceptions import WalletLocked
from graphenecommon.transactionbuilder import ProposalBuilder as GrapheneProposalBuilder
from graphenecommon.transactionbuilder import TransactionBuilder as GrapheneTransactionBuilder

from vizbase import operations
from vizbase.account import PrivateKey, PublicKey
from vizbase.objects import Operation
from vizbase.signedtransactions import Signed_Transaction

from .account import Account
from .amount import Amount
from .instance import BlockchainInstance


@BlockchainInstance.inject
class ProposalBuilder(GrapheneProposalBuilder):
    """
    Proposal Builder allows us to construct an independent Proposal that may later be added to an instance of
    TransactionBuilder.

    :param str proposer: Account name of the proposing user
    :param int proposal_expiration: Number seconds until the proposal is
        supposed to expire
    :param int proposal_review: Number of seconds for review of the
        proposal
    :param .transactionbuilder.TransactionBuilder: Specify
        your own instance of transaction builder (optional)
    :param instance blockchain_instance: Blockchain instance
    """

    def __init__(
        self, author, title, memo, proposal_expiration=None, proposal_review=None, parent=None, *args, **kwargs
    ):
        self.define_classes()
        assert self.operation_class
        assert self.operations
        assert self.account_class

        self.proposal_expiration = proposal_expiration or 2 * 24 * 60 * 60
        self.proposal_review = proposal_review
        self.parent = parent
        self.proposer = author
        self.title = title
        self.memo = memo
        self.ops = []

    def define_classes(self):
        self.operation_class = Operation
        self.operations = operations
        self.account_class = Account

    def get_raw(self):
        """Returns an instance of base "Operations" for further processing."""
        if not self.ops:
            return
        ops = [self.operations.Op_wrapper(op=o) for o in list(self.ops)]
        data = {
            'author': self.proposer,
            'title': self.title,
            'memo': self.memo,
            'proposed_operations': [o.json() for o in ops],
            'expiration_time': formatTimeFromNow(self.proposal_expiration),
            'extensions': [],
        }
        if self.proposal_review:
            data.update({"review_period_time": formatTimeFromNow(self.proposal_review)})

        ops = self.operations.Proposal_create(**data)
        return self.operation_class(ops)

    def broadcast(self):
        # TODO: remove method after release with fix https://github.com/xeroc/python-graphenelib/pull/172
        assert self.parent, "No parent transaction provided!"
        self.parent._set_require_reconstruction()
        self.parent.sign()
        return self.parent.broadcast()


@BlockchainInstance.inject
class TransactionBuilder(GrapheneTransactionBuilder):
    """This class simplifies the creation of transactions by adding operations and signers."""

    permission_types = ["master", "active", "regular"]

    def define_classes(self):
        self.account_class = Account
        self.asset_class = Asset
        self.operation_class = Operation
        self.operations = operations
        self.privatekey_class = PrivateKey
        self.publickey_class = PublicKey
        self.signed_transaction_class = Signed_Transaction
        self.amount_class = Amount

    def add_required_fees(self, ops, **kwargs):
        """Override this method because steem-like chains doesn't have transaction feed."""
        return ops

    def appendSigner(self, accounts, permission):  # noqa: N802
        """Try to obtain the wif key from the wallet by telling which account and permission is supposed to sign the
        transaction."""
        assert permission in self.permission_types, "Invalid permission"

        if self.blockchain.wallet.locked():
            raise WalletLocked()
        if not isinstance(accounts, (list, tuple, set)):
            accounts = [accounts]

        for account in accounts:
            # Now let's actually deal with the accounts
            if account not in self.signing_accounts:
                # is the account an instance of public key?
                if isinstance(account, self.publickey_class):
                    self.appendWif(self.blockchain.wallet.getPrivateKeyForPublicKey(str(account)))
                # ... or should we rather obtain the keys from an account name
                else:
                    accountObj = self.account_class(account, blockchain_instance=self.blockchain)  # noqa: N806
                    # TODO: method overriden because of _authority
                    field = "{}_authority".format(permission)
                    required_treshold = accountObj[field]["weight_threshold"]
                    keys = self._fetchkeys(accountObj, field, required_treshold=required_treshold)
                    # If we couldn't find an active key, let's try overwrite it
                    # with an owner key
                    if not keys and permission != "active":
                        keys.extend(
                            self._fetchkeys(accountObj, "master_authority", required_treshold=required_treshold)
                        )
                    for x in keys:  # noqa: VNE001
                        self.appendWif(x[0])

                self.signing_accounts.append(account)

    def get_block_params(self):
        """
        Auxiliary method to obtain ``ref_block_num`` and ``ref_block_prefix``.

        Requires a websocket connection to a witness node!
        """
        ws = self.blockchain.rpc
        props = ws.get_dynamic_global_properties()
        ref_block_num = props["head_block_number"] & 0xFFFF
        ref_block_prefix = struct.unpack_from("<I", unhexlify(props["head_block_id"]), 4)[0]
        return ref_block_num, ref_block_prefix

# -*- coding: utf-8 -*-
from graphenecommon.transactionbuilder import (
    TransactionBuilder as GrapheneTransactionBuilder,
    ProposalBuilder as GrapheneProposalBuilder,
)

from vizbase import operations
from vizbase.account import PrivateKey, PublicKey
from vizbase.objects import Operation
from vizbase.signedtransactions import Signed_Transaction

# We don't have own Asset class because it is unneeded
from graphenecommon.asset import Asset

from .amount import Amount
from .account import Account
from .instance import BlockchainInstance
from .utils import formatTimeFromNow


@BlockchainInstance.inject
class ProposalBuilder(GrapheneProposalBuilder):
    """ Proposal Builder allows us to construct an independent Proposal
        that may later be added to an instance ot TransactionBuilder

        :param str proposer: Account name of the proposing user
        :param int proposal_expiration: Number seconds until the proposal is
            supposed to expire
        :param int proposal_review: Number of seconds for review of the
            proposal
        :param .transactionbuilder.TransactionBuilder: Specify
            your own instance of transaction builder (optional)
        :param instance blockchain_instance: Blockchain instance
    """

    def define_classes(self):
        self.operation_class = Operation
        self.operations = operations
        self.account_class = Account


@BlockchainInstance.inject
class TransactionBuilder(GrapheneTransactionBuilder):
    """ This class simplifies the creation of transactions by adding
        operations and signers.
    """

    def define_classes(self):
        self.account_class = Account
        self.asset_class = Asset
        self.operation_class = Operation
        self.operations = operations
        self.privatekey_class = PrivateKey
        self.publickey_class = PublicKey
        self.signed_transaction_class = Signed_Transaction
        self.amount_class = Amount

    def constructTx(self):
        # TODO: propose to control add_required_fees via variable into upstream?
        """ Construct the actual transaction and store it in the class's dict
            store

            We're overriding this method because we don't need to call
            self.add_required_fees()
        """
        ops = list()
        for op in self.ops:
            if isinstance(op, ProposalBuilder):
                # This operation is a proposal an needs to be deal with
                # differently
                proposals = op.get_raw()
                if proposals:
                    ops.append(proposals)
            else:
                # otherwise, we simply wrap ops into Operations
                ops.extend([self.operation_class(op)])

        # We now wrap everything into an actual transaction
        expiration = formatTimeFromNow(
            self.expiration
            or self.blockchain.expiration
            or 30  # defaults to 30 seconds
        )
        ref_block_num, ref_block_prefix = self.get_block_params()
        self.tx = self.signed_transaction_class(
            ref_block_num=ref_block_num,
            ref_block_prefix=ref_block_prefix,
            expiration=expiration,
            operations=ops,
        )
        dict.update(self, self.tx.json())
        self._unset_require_reconstruction()


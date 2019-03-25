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

    def add_required_fees(self, ops, **kwargs):
        """ Override this method because steem-like chains doesn't have transaction feed
        """
        return ops

    def appendSigner(self, accounts, permission):
        """ Try to obtain the wif key from the wallet by telling which account
            and permission is supposed to sign the transaction
        """
        # TODO: override this class until
        # https://github.com/xeroc/python-graphenelib/issues/85 is fixed
        assert permission in ["posting", "active", "owner"], "Invalid permission"

        if self.blockchain.wallet.locked():
            raise WalletLocked()
        if not isinstance(accounts, (list, tuple, set)):
            accounts = [accounts]

        for account in accounts:
            # Now let's actually deal with the accounts
            if account not in self.signing_accounts:
                # is the account an instance of public key?
                if isinstance(account, self.publickey_class):
                    self.appendWif(
                        self.blockchain.wallet.getPrivateKeyForPublicKey(str(account))
                    )
                # ... or should we rather obtain the keys from an account name
                else:
                    accountObj = self.account_class(
                        account, blockchain_instance=self.blockchain
                    )
                    required_treshold = accountObj[permission]["weight_threshold"]
                    keys = self._fetchkeys(
                        accountObj, permission, required_treshold=required_treshold
                    )
                    # If we couldn't find an active key, let's try overwrite it
                    # with an owner key
                    if not keys and permission != "owner":
                        keys.extend(
                            self._fetchkeys(
                                accountObj, "owner", required_treshold=required_treshold
                            )
                        )
                    for x in keys:
                        self.appendWif(x[0])

                self.signing_accounts.append(account)

from .amount import Amount
from .instance import shared_blockchain_instance


class Converter(object):
    """
    Converter simplifies the handling of different metrics of the blockchain.

    :param Steemd blockchain_instance: Steemd() instance to use when accessing a RPC
    """

    def __init__(self, blockchain_instance=None):
        self.blockchain_instance = blockchain_instance or shared_blockchain_instance()

    def core_per_share(self):
        """Obtain CORE_TOKEN/SHARES ratio."""
        info = self.blockchain_instance.rpc.get_dynamic_global_properties()
        return Amount(info["total_vesting_fund"]).amount / Amount(info["total_vesting_shares"]).amount

    def shares_to_core(self, shares):
        """
        Obtain CORE tokens representation of SHARES.

        :param number shares: SHARES to convert to CORE
        """
        return shares * self.core_per_share()

    def core_to_shares(self, amount):
        """
        Obtain SHARES from CORE tokens.

        :param number amount: amount of CORE tokens to convert
        """
        return amount / self.core_per_share()

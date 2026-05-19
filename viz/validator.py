from graphenecommon.witness import Witness as GrapheneWitness
from graphenecommon.witness import Witnesses as GrapheneWitnesses

from .account import Account
from .instance import BlockchainInstance


@BlockchainInstance.inject
class Validator(GrapheneWitness):
    """
    Read data about a validator in the chain.

    :param str account_name: Name of the validator
    :param viz blockchain_instance: Client() instance to use when
           accesing a RPC

    .. note::
        Inherits from graphenecommon.witness.Witness. Once graphenecommon
        migrates its terminology, this parent can be swapped to the
        validator-named equivalent.
    """

    def define_classes(self):
        self.account_class = Account
        self.type_ids = [6, 2]


@BlockchainInstance.inject
class Validators(GrapheneWitnesses):
    """
    Obtain a list of **active** validators and the current schedule.

    :param bool only_active: (False) Only return validators that are
        actively producing blocks
    :param viz blockchain_instance: Client() instance to use when
        accesing a RPC
    """

    def define_classes(self):
        self.account_class = Account
        # graphenecommon contract: parent asserts self.witness_class.
        self.witness_class = Validator
        # Forward-compat for a future graphenecommon migration. Harmless today.
        self.validator_class = Validator

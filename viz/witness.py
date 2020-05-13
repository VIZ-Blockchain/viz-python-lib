# -*- coding: utf-8 -*-
from graphenecommon.witness import Witness as GrapheneWitness
from graphenecommon.witness import Witnesses as GrapheneWitnesses

from .account import Account
from .instance import BlockchainInstance


@BlockchainInstance.inject
class Witness(GrapheneWitness):
    """
    Read data about a witness in the chain.

    :param str account_name: Name of the witness
    :param viz blockchain_instance: Client() instance to use when
           accesing a RPC
    """

    def define_classes(self):
        self.account_class = Account
        self.type_ids = [6, 2]


@BlockchainInstance.inject
class Witnesses(GrapheneWitnesses):
    """
    Obtain a list of **active** witnesses and the current schedule.

    :param bool only_active: (False) Only return witnesses that are
        actively producing blocks
    :param viz blockchain_instance: Client() instance to use when
        accesing a RPC
    """

    def define_classes(self):
        self.account_class = Account
        self.witness_class = Witness

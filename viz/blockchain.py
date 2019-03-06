# -*- coding: utf-8 -*-
import hashlib
import json

from .block import Block
from .instance import BlockchainInstance
from vizbase import operationids
from graphenecommon.blockchain import Blockchain as GrapheneBlockchain


@BlockchainInstance.inject
class Blockchain(GrapheneBlockchain):
    """ This class allows to access the blockchain and read data
        from it

        :param viz.viz.Client blockchain_instance: Client
                 instance
        :param str mode: (default) Irreversible block (``irreversible``) or
                 actual head block (``head``)
        :param int max_block_wait_repetition: (default) 3 maximum wait time for
            next block ismax_block_wait_repetition * block_interval

        This class let's you deal with blockchain related data and methods.
    """

    def define_classes(self):
        self.block_class = Block
        self.operationids = operationids

    @staticmethod
    def hash_op(event: dict):
        """ This method generates a hash of blockchain operation. """
        data = json.dumps(event, sort_keys=True)
        return hashlib.sha1(bytes(data, 'utf-8')).hexdigest()

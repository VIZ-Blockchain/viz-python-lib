# -*- coding: utf-8 -*-
from graphenecommon.block import Block as GrapheneBlock
from graphenecommon.block import BlockHeader as GrapheneBlockHeader

from .instance import BlockchainInstance


@BlockchainInstance.inject
class Block(GrapheneBlock):
    """
    Read a single block from the chain.

    :param int block: block number
    :param viz.viz.Client blockchain_instance: Client
        instance
    :param bool lazy: Use lazy loading

    Instances of this class are dictionaries that come with additional
    methods (see below) that allow dealing with a block and it's
    corresponding functions.

    .. code-block:: python

        from viz.block import Block
        block = Block(1)
        print(block)

    .. note:: This class comes with its own caching function to reduce the
              load on the API server. Instances of this class can be
              refreshed with ``Account.refresh()``.
    """

    def define_classes(self):
        self.type_id = "-none-"


@BlockchainInstance.inject
class BlockHeader(GrapheneBlockHeader):
    def define_classes(self):
        self.type_id = "-none-"

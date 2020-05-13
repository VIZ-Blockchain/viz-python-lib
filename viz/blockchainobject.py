# -*- coding: utf-8 -*-
from graphenecommon.blockchainobject import BlockchainObject as GrapheneBlockchainObject
from graphenecommon.blockchainobject import Object as GrapheneChainObject

from .instance import BlockchainInstance


@BlockchainInstance.inject
class BlockchainObject(GrapheneBlockchainObject):
    pass


@BlockchainInstance.inject
class Object(GrapheneChainObject):
    perform_id_tests = False

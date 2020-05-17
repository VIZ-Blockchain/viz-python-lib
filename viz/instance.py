# -*- coding: utf-8 -*-
from graphenecommon.instance import AbstractBlockchainInstanceProvider


class BlockchainInstance(AbstractBlockchainInstanceProvider):
    """This is a class that allows compatibility with previous naming conventions."""

    def __init__(self, *args, **kwargs):
        # Also allow 'instance'
        if kwargs.get("instance"):
            kwargs["blockchain_instance"] = kwargs["instance"]
        AbstractBlockchainInstanceProvider.__init__(self, *args, **kwargs)

    @property
    def viz(self):
        """Alias for the specific blockchain."""
        return self.blockchain

    def get_instance_class(self):
        """Should return the Chain instance class, e.g. `viz.Client`"""
        import viz

        return viz.Client


def shared_blockchain_instance():
    return BlockchainInstance().shared_blockchain_instance()


def set_shared_blockchain_instance(instance):
    instance.clear_cache()
    BlockchainInstance.set_shared_blockchain_instance(instance)


def set_shared_config(config):
    shared_blockchain_instance().set_shared_config(config)
    BlockchainInstance.set_shared_config(config)


shared_chain_instance = shared_blockchain_instance
set_shared_chain_instance = set_shared_blockchain_instance

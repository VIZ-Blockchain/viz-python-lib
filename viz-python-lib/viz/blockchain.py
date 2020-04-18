# -*- coding: utf-8 -*-
import hashlib
import json
import time

from typing import Union

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
        return hashlib.sha1(bytes(data, "utf-8")).hexdigest()

    def get_block_interval(self):
        """ Override class from graphenelib because our API is different
        """
        return self.blockchain.rpc.config.get("CHAIN_BLOCK_INTERVAL")

    def stream_from(
        self,
        start_block=None,
        end_block=None,
        batch_operations=False,
        full_blocks=False,
        only_virtual_ops=False,
        **kwargs
    ):
        """ This call yields raw blocks or operations depending on
        ``full_blocks`` param.

        By default, this generator will yield operations, one by one.
        You can choose to yield lists of operations, batched to contain
        all operations for each block with ``batch_operations=True``.
        You can also yield full blocks instead, with ``full_blocks=True``.

        :param int start_block: Block to start with. If not provided, current (head) block is used.
        :param int end_block: Stop iterating at this block. If not provided, this generator will run forever (streaming mode).
        :param bool batch_operations: (Defaults to False) Rather than yielding operations one by one,
                yield a list of all operations for each block.
        :param bool full_blocks: (Defaults to False) Rather than yielding operations, return raw, unedited blocks as
                provided by blokchain_instance. This mode will NOT include virtual operations.
        """

        _ = kwargs  # we need this
        # Let's find out how often blocks are generated!
        block_interval = self.get_block_interval()

        is_reversed = end_block and start_block > end_block

        if not start_block:
            start_block = self.get_current_block_num()

        while True:
            head_block = self.get_current_block_num()

            range_params = (start_block, head_block + 1)
            if end_block is not None and start_block > end_block:
                range_params = (start_block, max(0, end_block - 2), -1)

            for block_num in range(*range_params):
                if end_block is not None:
                    if is_reversed and block_num < end_block:
                        raise StopIteration("Reached stop block at: #%s" % block_num)
                    elif not is_reversed and block_num > end_block:
                        raise StopIteration("Reached stop block at: #%s" % block_num)

                if full_blocks:
                    block = self.blockchain.rpc.get_block(block_num)
                    # inject block number
                    block.update({"block_num": block_num})
                    yield block
                elif batch_operations:
                    yield self.blockchain.rpc.get_ops_in_block(
                        block_num, only_virtual_ops
                    )
                else:
                    ops = self.blockchain.rpc.get_ops_in_block(
                        block_num, only_virtual_ops
                    )
                    for op in ops:
                        # avoid yielding empty ops
                        if op:
                            yield op

            # next round
            start_block = head_block + 1
            time.sleep(block_interval)

    def stream(self, filter_by: Union[str, list] = list(), *args, **kwargs):
        """ Yield a stream of specific operations, starting with current head block.

            This method can work in 2 modes:
            1. Whether only real operations are requested, it will use get_block() API call, so you don't need to have
            neigher operation_history nor accunt_history plugins enabled.
            2. Whether you're requesting any of the virtual operations, your node should have operation_history or
            accunt_history plugins enabled and appropriate settings for the history-related params should be set
            (history-start-block, history-whitelist-ops or history-blacklist-ops).

            The dict output is formated such that ``type`` caries the operation type, timestamp and block_num are taken
            from the block the operation was stored in and the other key depend on the actual operation.

            Note: you can pass all stream_from() params too.

            :param int start_block: Block to start with. If not provided, current (head) block is used.
            :param int end_block: Stop iterating at this block. If not provided, this generator will run forever (streaming mode).
            :param str,list filter_by: List of operations to filter for
        """
        if isinstance(filter_by, str):
            filter_by = [filter_by]

        if not bool(set(filter_by).intersection(operationids.VIRTUAL_OPS)):
            # uses get_block instead of get_ops_in_block
            for block in self.stream_from(full_blocks=True, *args, **kwargs):
                for tx in block.get("transactions"):
                    for op in tx["operations"]:
                        if not filter_by or op[0] in filter_by:
                            r = {
                                "type": op[0],
                                "timestamp": block.get("timestamp"),
                                "block_num": block.get("block_num"),
                            }
                            r.update(op[1])
                            yield r
        else:
            # uses get_ops_in_block
            kwargs["only_virtual_ops"] = not bool(
                set(filter_by).difference(operationids.VIRTUAL_OPS)
            )
            for op in self.stream_from(full_blocks=False, *args, **kwargs):
                if kwargs.get("raw_output"):
                    yield op

                if not filter_by or op["op"][0] in filter_by:
                    r = {
                        "_id": self.hash_op(op),
                        "type": op["op"][0],
                        "timestamp": op.get("timestamp"),
                        "block_num": op.get("block"),
                        "trx_id": op.get("trx_id"),
                    }
                    r.update(op["op"][1])
                    yield r
